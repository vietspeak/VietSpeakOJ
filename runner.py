import time

from sqlalchemy.orm import Session

import bridges.task_audio_bridge as task_audio_bridge
import bridges.submission_audio_bridge as submission_audio_bridge
from grader.grading_transcript import GradingTranscript
from model.model import engine
from utils.dictionary import Dictionary
from utils.task_determiner import TaskDeterminer

with Session(engine) as session:
    dictionary = Dictionary(session)
    grading_transcript_producer = GradingTranscript(dictionary)
    task_determiner = TaskDeterminer(session)
    submission_audio_bridge.entry_point(session)
    task_audio_bridge.entry_point(session, grading_transcript_producer)
