import time

from sqlalchemy.orm import Session

import bridges.task_bridge as task_bridge
import bridges.transcript_bridge as transcript_bridge
from grader.grading_transcript import GradingTranscript
from model.model import engine
from utils.dictionary import Dictionary

with Session(engine) as session:
    dictionary = Dictionary(session)
    grading_transcript_producer = GradingTranscript(dictionary)
    transcript_bridge.entry_point(session)
    task_bridge.entry_point(session, grading_transcript_producer)
