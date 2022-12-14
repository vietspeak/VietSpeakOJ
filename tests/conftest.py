from typing import Iterable

from pytest import fixture
from sqlalchemy.orm import Session

from model.model import engine
from utils.dictionary import Dictionary


@fixture
def session() -> Iterable[Session]:
    with Session(engine) as session:
        yield session


@fixture
def dictionary(session) -> Dictionary:
    return Dictionary(session)
