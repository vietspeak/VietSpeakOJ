import json
import os
from subprocess import PIPE, Popen
from typing import Any, Dict

import requests
from slack_sdk.errors import SlackApiError
from sqlalchemy import select
from sqlalchemy.orm import Session
from vosk import KaldiRecognizer, Model

from model.model import FileSource, Submission
from slack.app import app

SAMPLE_RATE = 16000

model = Model("vosk_model")
rec = KaldiRecognizer(model, SAMPLE_RATE)


def bytes_to_transcript(file_content: bytes) -> str:
    with open("./tmp/input.inp", "wb") as f:
        f.write(file_content)

    process = Popen(
        [
            "ffmpeg",
            "-i",
            "./tmp/input.inp",
            "-ar",
            str(SAMPLE_RATE),
            "-ac",
            "1",
            "-f",
            "s16le",
            "-",
        ],
        stdout=PIPE,
    )
    data = process.communicate()[0]
    ret = ""
    if len(data) == 0:
        return ret
    if rec.AcceptWaveform(data):
        res = rec.Result()
        ret += json.loads(res)["text"] + " "

    ret += json.loads(rec.FinalResult())["text"]

    return ret


def slack_file_id_to_transcript(file_id: str) -> str:
    try:
        file_info: Dict[str, Any] = app.client.files_info(file=file_id).get("file", {})
    except SlackApiError:
        return ""

    url = file_info.get("url_private_download")

    if not url:
        return ""

    r = requests.get(
        url,
        headers={"Authorization": "Bearer {}".format(os.environ["SLACK_BOT_TOKEN"])},
    )
    return bytes_to_transcript(r.content)


def entry_point(session: Session):
    stmt = select(Submission).where(Submission.transcript == None)
    audio_file: Submission = next(session.scalars(stmt), None)

    if audio_file:
        if audio_file.source == FileSource.WEBSITE:
            audio_file.transcript = bytes_to_transcript(audio_file.audio_file)
            audio_file.audio_file = None
        else:
            audio_file.transcript = slack_file_id_to_transcript(
                audio_file.audio_file.decode()
            )

        session.commit()
