from re import sub
from typing import List

from sqlalchemy import and_, select
from sqlalchemy.orm import Session
from grader.grading_transcript import LegacyGrader
from model.model import Submission, Task, User, WordError
from slack_bolt import App

def send_feedback_message(
    app: App, session: Session, task: Task, word_errors: List[WordError], submission: Submission
):
    result = f"Mình xin phép được nhận xét bài {task.level.upper()} Task {task.task_number} của bạn\n"
    result += f"Mình thấy có {len(word_errors)} chỗ bạn phát âm chưa ổn.\n"

    error_msg = " | ".join(
        f"{error.right_word} -> `{error.wrong_word if error.wrong_word else '∅'}`"
        for error in word_errors
    )

    result += f"*{error_msg}*"

    result += f"Đây là những gì mình nghe được từ bạn:\n"

    result += submission.transcript.lower() + "\n"
    result += "Điểm: {:0.2f}".format(submission.score * 100)

    user_find_stmt = select(User).where(User.id == submission.user_id)
    user: User = next(session.scalars(user_find_stmt), None)
    slack_id = user.slack_id
    app.client.chat_postMessage(channel=slack_id, text=result)


def is_complete_submission(submission: Submission) -> bool:
    return submission.transcript and submission.task_id and submission.score


def send_cache_feedback(app: App, session: Session, completed_submission: Submission):
    if not is_complete_submission(completed_submission):
        return

    task_find_stmt = select(Task).where(Task.id == completed_submission.task_id)
    task: Task = next(session.scalars(task_find_stmt), None)

    word_error_stmt = select(WordError).where(
        WordError.submission_id == completed_submission.id
    )
    word_errors = list(session.scalars(word_error_stmt))
    send_feedback_message(app, session, task, word_errors, completed_submission)


def entry_point(app: App, session: Session, grader: LegacyGrader):
    submission_stmt = select(Submission).where(
        and_(Submission.task_id != None, Submission.score == None)
    )
    submission: Submission = next(session.scalars(submission_stmt), None)

    if submission:
        task_stmt = select(Task).where(Task.id == submission.task_id)
        task: Task = next(session.scalars(task_stmt), None)

        if not task:
            submission.score = 0
            session.commit()
            return

        feedback = grader.grader(submission.transcript, task.grading_transcript)
        submission.score = feedback.score

        word_error_objs: List[WordError] = []

        for error in feedback.errors:
            word_error = WordError(
                submission_id=submission.id, wrong_word=error[0], right_word=error[1]
            )
            word_error_objs.append(word_error)

        session.add_all(word_error_objs)

        session.commit()

        send_feedback_message(app, task, word_error_objs, submission)
