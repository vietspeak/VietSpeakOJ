from re import sub
from typing import List

from slack_bolt import App
from sqlalchemy import and_, select, delete
from sqlalchemy.orm import Session

from config.config import CUTOFF_SCORE
from grader.grading_transcript import LegacyGrader
from model.model import PronunciationMatch, Submission, Task, User, WordError


def entry_point(session: Session, grader: LegacyGrader):
    submission_id_stmt = """
        SELECT id 
        FROM submissions 
        WHERE id NOT IN (
            SELECT submission_id 
            FROM pronunciation_matches
        );
    """

    submission_id = next(session.execute(submission_id_stmt), None)

    if submission_id is None:
        return

    submission_id = submission_id[0]
    submission_stmt = select(Submission).where(Submission.id == submission_id)
    submission: Submission = next(session.scalars(submission_stmt), None)
    if submission:
        task_stmt = select(Task).where(Task.id == submission.task_id)
        task: Task = next(session.scalars(task_stmt), None)
        if not task:
            return
        feedback = grader.grader(submission.transcript, task.grading_transcript)
        clear_pro_matches_stmt = delete(PronunciationMatch).where(
            PronunciationMatch.submission_id == submission.id
        )
        session.execute(clear_pro_matches_stmt)
        pronunciation_matches: List[PronunciationMatch] = []
        for match in feedback.pronunciation_matches:
            pronunciation_matches.append(
                PronunciationMatch(
                    submission_id=submission.id,
                    grading_sound=match[0],
                    student_sound=match[1],
                )
            )

        session.add_all(pronunciation_matches)
        session.commit()
