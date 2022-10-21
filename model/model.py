import enum
import json
from typing import Any, List

from sqlalchemy import (BLOB, TIMESTAMP, Boolean, Column, Enum, ForeignKey,
                        Integer, String, create_engine)
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


class FileSource(enum.Enum):
    SLACK = 0
    WEBSITE = 1


class AudioFile(Base):
    __tablename__ = "audio_files"

    id = Column(Integer, primary_key=True)
    source = Column(Enum(FileSource))
    content = Column(BLOB)
    transcript = Column(String)

    def __repr__(self):
        attrs = ["id", "source", "content", "transcript"]
        return generate_repr(self, "AudioFile", attrs)


Base.metadata.create_all(engine)
