from typing import List
from sqlalchemy import select, and_
from sqlalchemy.orm import Session


from model.model import Submission, Task, WordError, engine
from grader.grading_transcript import LegacyGrader

def entry_point(session: Session, grader: LegacyGrader):
    submission_stmt = select(Submission).where(and_(Submission.task_id != None, Submission.score == None))
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
            word_error = WordError(submission_id=submission.id, wrong_word=error[0], right_word=error[1])
            word_error_objs.append(word_error)

        session.add_all(word_error_objs)

        session.commit()