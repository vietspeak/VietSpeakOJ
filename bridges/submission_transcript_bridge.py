from sqlalchemy import select
from sqlalchemy.orm import Session


from grader.grading_transcript import GradingTranscript
from model.model import Submission, Task, engine
from utils.task_determiner import TaskDeterminer


def entry_point(session: Session, task_determiner: TaskDeterminer):
    with Session(engine) as session:
        stmt = select(Submission).where(Submission.transcript != None)
        submission: Submission = next(session.scalars(stmt), None)

        if submission:
            task_id = task_determiner.detect_task(submission.transcript)
            submission.task_id = task_id
            session.commit()