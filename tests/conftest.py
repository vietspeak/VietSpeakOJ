from pytest import fixture
from sqlalchemy.orm import Session

from model.model import engine

from pytest import fixture

@fixture
def session() -> Session:
    return Session(engine)