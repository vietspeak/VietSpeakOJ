import json
from subprocess import PIPE, Popen

from sqlalchemy import select
from sqlalchemy.orm import Session
from vosk import KaldiRecognizer, Model

from model.model import FileSource, Submission

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
    print(ret)
    return ret


def entry_point(session: Session):
    stmt = select(Submission).where(Submission.audio_file != None)
    audio_file: Submission = next(session.scalars(stmt), None)

    if audio_file:
        if audio_file.source == FileSource.WEBSITE:
            audio_file.transcript = bytes_to_transcript(audio_file.audio_file)
        else:
            audio_file.transcript = ""
        audio_file.audio_file = None
        session.commit()
