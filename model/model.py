from __future__ import annotations
import enum
import random
import string
from email.policy import default
from typing import Any, Dict, Iterable, List

from sqlalchemy import (BLOB, TIMESTAMP, Boolean, Column, Enum, Float,
                        ForeignKey, Integer, String, create_engine, select)
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy.sql import func

from config.config import PATH_TO_DATABASE

from flask_login import UserMixin

engine = create_engine(f"sqlite:///{PATH_TO_DATABASE}", echo=True, future=True)
Base = declarative_base()


def generate_repr(obj: Any, class_name: str, attrs: List[str]) -> str:
    inside = ", ".join(f"{attr}={getattr(obj, attr)!r}" for attr in attrs)
    return f"{class_name}({inside})"


class CMUPronunciation(Base):
    __tablename__ = "cmu_pronunciations"

    id: int = Column(Integer, primary_key=True)
    word: str = Column(String)
    arpabet: str = Column(String)
    ipa: str = Column(String)
    use_in_grader: bool = Column(Boolean)

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


class User(Base, UserMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    slack_id = Column(String)
    email = Column(String)
    password = Column(String)
    is_bot = Column(Boolean)
    is_owner = Column(Boolean)
    is_admin = Column(Boolean)
    created_time = Column(TIMESTAMP, nullable=False, server_default=func.now())
    last_official_submission_timestamp = Column(TIMESTAMP)
    second_to_last_human_feedback_timestamp = Column(TIMESTAMP)
    is_eliminated = Column(Boolean, server_default="0", nullable=False)
    display_name = Column(String)

    @classmethod
    def generate_password(cls, length: int = 10) -> str:
        return "".join(random.choice(string.ascii_letters) for _ in range(length))

    @classmethod
    def from_dict(cls, user: Dict[str, Any]) -> User:
        user_id = user.get("id")
        user_email = user["profile"].get("email")
        display_name = user["profile"].get("display_name", user.get("real_name", user.get("name")))
        is_bot = user.get("is_bot", False)
        is_owner = user.get("is_owner", False)
        is_admin = user.get("is_admin", False)

        return User(
            slack_id=user_id,
            email=user_email,
            password=cls.generate_password(),
            is_bot=is_bot,
            is_owner=is_owner,
            is_admin=is_admin,
            display_name=display_name
        )
    
    @classmethod
    def get(cls, user_id: str) -> User:
        with Session(engine) as session:
            user_stmt = select(User).where(User.id == int(user_id))
            return session.scalar(user_stmt)

    def update_from_dict(self, user: Dict[str, Any]):
        self.email = user["profile"].get("email")
        self.is_bot = user.get("is_bot", False)
        self.is_owner = user.get("is_owner", False)
        self.is_admin = user.get("is_admin", False)
        self.display_name = user["profile"].get("display_name", user.get("real_name", user.get("name")))

class WordError(Base):
    __tablename__ = "word_errors"

    id = Column(Integer, primary_key=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"))
    wrong_word = Column(String)
    right_word = Column(String, nullable=True)


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True)
    source = Column(Enum(FileSource))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_official = Column(Boolean, default=False)
    audio_file = Column(BLOB)
    transcript = Column(String)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    score = Column(Float)
    created_time = Column(TIMESTAMP, nullable=False, server_default=func.now())

    def __repr__(self):
        attrs = ["id", "source", "audio_file", "transcript"]
        return generate_repr(self, "Submission", attrs)

    def generate_feedback_markdown(self) -> str:
        if self.score is not None:
            with Session(engine) as session:
                task_stmt = select(Task).where(Task.id == self.task_id)
                task: Task = session.scalar(task_stmt)

                level_name = str(task.level).split(".")[-1]
                level_name = level_name[0] + level_name[1:].lower()

                result = f"Mình xin phép được nhận xét bài {level_name} Task {task.task_number} của bạn\n\n"
                
                word_errors_stmt = select(WordError).where(WordError.submission_id == self.id)
                word_errors: List[WordError] = list(session.scalars(word_errors_stmt))

                result += f"Mình thấy có {len(word_errors)} chỗ bạn phát âm chưa ổn.\n\n"

                if len(word_errors):
                    error_msg = " | ".join(
                        f"{error.right_word.lower()} -> `{error.wrong_word.lower() if error.wrong_word else '∅'}`"
                        for error in word_errors
                    )

                    result += f"**{error_msg}**\n\n"
                
                result += "Đây là những gì mình nghe được từ bạn:\n\n"
                result += self.transcript.lower() + "\n\n"

                human_feedback_stmt = select(HumanFeedback).where(HumanFeedback.submission_id == self.id)
                human_feedback: Iterable[HumanFeedback] = session.scalars(human_feedback_stmt)
                for feedback in human_feedback:
                    result += feedback.generate_feedback_markdown() + "\n\n"
                
                return result
        
        return ""
            


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    task_number = Column(Integer)
    level = Column(Enum(TaskLevel))
    title = Column(String)
    audio_file = Column(BLOB)
    audio_link = Column(String, server_default="")
    sample_transcript = Column(String)
    grading_transcript = Column(String)

    def __repr__(self):
        attrs = [
            "id",
            "task_number",
            "level",
            "title",
            "audio_file",
            "sample_transcript",
            "grading_transcript",
        ]
        return generate_repr(self, "Task", attrs)


class HumanFeedback(Base):
    __tablename__ = "human_feedback"
    id = Column(Integer, primary_key=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(String)
    created_time = Column(TIMESTAMP, nullable=False, server_default=func.now())

    def __repr__(self):
        attrs = ["id", "submission_id", "user_id", "content", "created_time"]
        return generate_repr(self, "Task", attrs)

    def generate_feedback_markdown(self):
        with Session(engine) as session:
            user_stmt = select(User).where(User.id == self.user_id)
            user: User = session.scalar(user_stmt)
            if user and not user.is_bot:
                return f"{user.display_name}: {self.content}"
        return ""

Base.metadata.create_all(engine)
