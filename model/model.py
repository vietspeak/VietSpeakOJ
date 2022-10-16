import json
from typing import Any, List

from sqlalchemy import (
    BLOB,
    TIMESTAMP,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

with open("./config/config.json", "r") as f:
    configs = json.load(f)

PATH_TO_DATABASE = configs["PATH_TO_DATABASE"]

engine = create_engine(f"sqlite:///{PATH_TO_DATABASE}", echo=True, future=True)
Base = declarative_base()


def generate_repr(obj: Any, class_name: str, attrs: List[str]) -> str:
    inside = ", ".join(f"{attr}={getattr(obj, attr)!r}" for attr in attrs)
    return f"{class_name}({inside})"


class CMUPronunciation(Base):
    __tablename__ = "cmu_pronunciations"

    id = Column(Integer, primary_key=True)
    word = Column(String)
    arpabet = Column(String)
    ipa = Column(String)
    use_in_grader = Column(Boolean)

    def __repr__(self):
        return generate_repr(
            self, "CMUPronunciation", ["id", "word", "arpabet", "ipa", "use_in_grader"]
        )


class SlackAudioFile(Base):
    __tablename__ = "slack_audio_files"

    id = Column(Integer, primary_key=True)
    file_id = Column(String)
    transcript_id = Column(Integer, ForeignKey("transcripts.id"), default=None)
    last_update = Column(
        TIMESTAMP, server_default=func.now(), onupdate=func.current_timestamp()
    )

    def __repr__(self):
        attrs = ["id", "file_id", "transcript_id", "last_update"]
        return generate_repr(self, "SlackAudioFile", attrs)


class AudioFile(Base):
    __tablename__ = "website_audio_files"

    id = Column(Integer, primary_key=True)
    content = Column(BLOB)
    transcript_id = Column(Integer, ForeignKey("transcripts.id"), default=None)

    def __repr__(self):
        attrs = ["id", "content", "transcript_id"]
        return generate_repr(self, "AudioFile", attrs)


class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True)
    transcript = Column(String)

    def __repr__(self):
        attrs = ["id", "transcript"]
        return generate_repr(self, "Transcript", attrs)


Base.metadata.create_all(engine)
