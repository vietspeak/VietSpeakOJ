from sqlalchemy import select
from sqlalchemy.orm import Session

from bridges.submission_audio_bridge import bytes_to_transcript
from grader.grading_transcript import GradingTranscript
from model.model import Task, engine


def entry_point(session: Session, grading_transcript: GradingTranscript):
    stmt = select(Task).where(Task.audio_file != None)
    tasks = list(session.scalars(stmt))

    if tasks:
        for task in tasks:
            transcript = bytes_to_transcript(task.audio_file)
            task.grading_transcript = grading_transcript.get_grading_transcript(
                task.sample_transcript, transcript
            )
            task.audio_file = None
            session.commit()
