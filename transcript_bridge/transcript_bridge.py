from vosk import Model, KaldiRecognizer
import json
from subprocess import Popen, PIPE


from sqlalchemy import select
from sqlalchemy.orm import Session

from model.model import AudioFile, Transcript, engine

SAMPLE_RATE = 16000

model = Model("vosk_model")
rec = KaldiRecognizer(model, SAMPLE_RATE)

def bytes_to_transcript(file_content: bytes) -> str:
    process = Popen(
                [
                    "ffmpeg",
                    "-i",
                    "pipe:",
                    "-ar",
                    str(SAMPLE_RATE),
                    "-ac",
                    "1",
                    "-f",
                    "s16le",
                    "-",
                ],
                stdin=PIPE,
                stdout=PIPE,
            )
    data = process.communicate(input=file_content)[0]
    ret = ""
    if len(data) == 0:
        return ret
    if rec.AcceptWaveform(data):
        res = rec.Result()
        ret += json.loads(res)["text"] + " "
    
    ret += json.loads(rec.FinalResult())["text"]
    return ret


def entry_point():
    audio_file = None
    with Session(engine) as session:
        stmt = select(AudioFile).where(AudioFile.transcript_id == None)
        audio_file: AudioFile = next(session.scalars(stmt), None)
    
        if audio_file:
            transcript = Transcript(transcript=bytes_to_transcript(audio_file.content))
            session.add(transcript)
            session.commit()
            audio_file.transcript_id = transcript.id
            session.commit()
            
