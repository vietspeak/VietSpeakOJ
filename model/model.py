import enum
import json
from typing import Any, List

from sqlalchemy import (BLOB, TIMESTAMP, Boolean, Column, Enum, Float, ForeignKey,
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


class TaskLevel(enum.Enum):
    YELLOW = 0
    GREEN = 1
    BLUE = 2
    RED = 3

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    slack_id = Column(String)
    email = Column(String)
    password = Column(String)


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True)
    source = Column(Enum(FileSource))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    audio_file = Column(BLOB)
    transcript = Column(String)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    score = Column(Float)

    def __repr__(self):
        attrs = ["id", "source", "audio_file", "transcript"]
        return generate_repr(self, "Submission", attrs)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    task_number = Column(Integer)
    level = Column(Enum(TaskLevel))
    title = Column(String)
    audio_file = Column(BLOB)
    sample_transcript = Column(String)
    grading_transcript = Column(String)

    def __repr__(self):
        attrs = ["id", "task_number", "level", "title", "audio_file", "sample_transcript", "grading_transcript"]
        return generate_repr(self, "Task", attrs)


Base.metadata.create_all(engine)
