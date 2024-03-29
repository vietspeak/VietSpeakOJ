import sqlite3
import time
import os
from sqlalchemy import exc
from sqlalchemy.orm import Session

from bridges import (
    task_audio_bridge,
    submission_audio_bridge,
    submission_transcript_bridge,
    submission_task_bridge,
    slack_user_bridge,
    submission_timestamp_bridge,
    human_feedback_timestamp_bridge,
    user_elimination,
    user_reactivation,
    medal_awarder,
    rating_calculator,
)
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
    try:
        with Session(engine) as session:
            dictionary = Dictionary(session)
            grading_transcript_producer = GradingTranscript(dictionary)
            task_determiner = TaskDeterminer(session)
            grader = LegacyGrader(dictionary)
            if counter == 0:
                slack_user_bridge.entry_point(app, session)
                rating_calculator.entry_point(session)
                medal_awarder.entry_point(session)
                user_elimination.entry_point(session)

            counter += 1
            if counter == FETCH_COUNTER:
                counter = 0

            task_audio_bridge.entry_point(session, grading_transcript_producer)
            submission_audio_bridge.entry_point(session)
            submission_transcript_bridge.entry_point(session, task_determiner)
            submission_task_bridge.entry_point(app, session, grader)
            submission_timestamp_bridge.entry_point(session)
            human_feedback_timestamp_bridge.entry_point(session)
            user_reactivation.entry_point(session)
    except (sqlite3.OperationalError, exc.OperationalError) as e:
        print(e)
        print("Database is locked. Data are not updated")

    time.sleep(SLEEP_INTERVAL)
