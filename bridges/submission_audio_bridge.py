import json
import time
import requests
import os
from subprocess import PIPE, Popen
from typing import Any, Dict

from sqlalchemy import select
from sqlalchemy.orm import Session
from vosk import KaldiRecognizer, Model

from model.model import FileSource, Submission
from slack.app import app
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options


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


def vtt_link_to_transcript(link: str) -> str:
    link = f"{link}&t={os.environ['SLACK_DOWNLOAD_TOKEN']}"
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
    driver.get(link)
    pageSource = driver.page_source
    return pageSource

def slack_file_id_to_transcript(file_id: str) -> str:
    file_info: Dict[str, Any] = app.client.files_info(file=file_id).get("file", {})

    url = file_info.get("url_private_download")

    if not url:
        return ""
    
    vtt_link = file_info.get("vtt")
    
    if not vtt_link and file_info.get("transcription"):
        time.sleep(file_info.get("duration_ms", 60000) / 1000)
        file_info: Dict[str, Any] = app.client.files_info(file=file_id).get("file", {})
        vtt_link = file_info.get("vtt")
    
    if vtt_link:
        return vtt_link_to_transcript(vtt_link)

    r = requests.get(url, headers={'Authorization': "Bearer {}".format(os.environ["SLACK_BOT_TOKEN"])})
    return bytes_to_transcript(r.content)


def entry_point(session: Session):
    stmt = select(Submission).where(Submission.audio_file != None)
    audio_file: Submission = next(session.scalars(stmt), None)

    if audio_file:
        if audio_file.source == FileSource.WEBSITE:
            audio_file.transcript = bytes_to_transcript(audio_file.audio_file)
        else:
            audio_file.transcript = slack_file_id_to_transcript(audio_file.audio_file.decode())
            
        audio_file.audio_file = None
        session.commit()
