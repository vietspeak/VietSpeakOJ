from sqlalchemy import select, and_
from sqlalchemy.orm import Session


from model.model import Submission, engine
from utils.task_determiner import TaskDeterminer


def entry_point(session: Session, task_determiner: TaskDeterminer):
    stmt = select(Submission).where(and_(Submission.transcript != None, Submission.task_id == None))
    submission: Submission = next(session.scalars(stmt), None)

    if submission:
        task_id = task_determiner.detect_task(submission.transcript)
        submission.task_id = task_id
        session.commit()