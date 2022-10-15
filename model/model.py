import json

from sqlalchemy import Boolean, Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base

with open("./config/config.json", "r") as f:
    configs = json.load(f)

PATH_TO_DATABASE = configs["PATH_TO_DATABASE"]

engine = create_engine(f"sqlite:///{PATH_TO_DATABASE}", echo=True, future=True)
Base = declarative_base()


class CMUPronunciation(Base):
    __tablename__ = "cmu_pronunciations"

    id = Column(Integer, primary_key=True)
    word = Column(String)
    arpabet = Column(String)
    ipa = Column(String)
    use_in_grader = Column(Boolean)

    def __repr__(self):
        attrs = ["id", "word", "arpabet", "ipa", "use_in_grader"]
        inside = ", ".join(f"{attr}={getattr(self, attr)!r}" for attr in attrs)
        return f"CMUPronunciation({inside})"


Base.metadata.create_all(engine)
