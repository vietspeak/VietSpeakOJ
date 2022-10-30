import time
import os
from sqlalchemy.orm import Session

from bridges import task_audio_bridge, submission_audio_bridge, submission_transcript_bridge, submission_task_bridge, slack_user_bridge
from grader.grading_transcript import GradingTranscript, LegacyGrader
from model.model import engine
from utils.dictionary import Dictionary
from utils.task_determiner import TaskDeterminer
from slack_bolt import App

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)

SLEEP_INTERVAL = 15
FETCH_USER_INTERVAL = 3600
FETCH_COUNTER = FETCH_USER_INTERVAL // SLEEP_INTERVAL

counter = 0
while True:
    with Session(engine) as session:
        dictionary = Dictionary(session)
        grading_transcript_producer = GradingTranscript(dictionary)
        task_determiner = TaskDeterminer(session)
        grader = LegacyGrader(dictionary)
        if counter == 0:
            slack_user_bridge.entry_point(app, session)
        counter += 1
        if counter == FETCH_COUNTER:
            counter = 0
        
        task_audio_bridge.entry_point(session, grading_transcript_producer)
        submission_audio_bridge.entry_point(session)
        submission_transcript_bridge.entry_point(session, task_determiner)
        submission_task_bridge.entry_point(app, session, grader)
        time.sleep(SLEEP_INTERVAL)
