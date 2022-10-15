from typing import Dict

from pytest import fixture
from sqlalchemy.orm import Session

from model.model import engine
from utils.dictionary import Dictionary


@fixture
def session() -> Session:
    return Session(engine)


def test_standardize_word_valid():
    word_1 = "hello"
    assert Dictionary._standardize_word(word_1) == "HELLO"
    word_2 = "I'm"
    assert Dictionary._standardize_word(word_2) == "I'M"
    word_3 = "I’m"
    assert Dictionary._standardize_word(word_3) == "I'M"


def test_standardize_word_begin_of_sentence():
    word_1 = ".Hello"
    assert Dictionary._standardize_word(word_1) == "HELLO"
    word_2 = "'Hello"
    assert Dictionary._standardize_word(word_2) == "HELLO"
    word_3 = "“Hello"
    assert Dictionary._standardize_word(word_3) == "HELLO"


def test_standardize_word_end_of_sentence():
    word_1 = "Hello?"
    assert Dictionary._standardize_word(word_1) == "HELLO"
    word_2 = "Hello."
    assert Dictionary._standardize_word(word_2) == "HELLO"
    word_3 = "Hello." + "\u201d"
    assert Dictionary._standardize_word(word_3) == "HELLO"


def test_standardize_word_no_word():
    word_1 = ""
    assert Dictionary._standardize_word(word_1) is None
    word_2 = ".?!"
    assert Dictionary._standardize_word(word_2) is None


def test_standardize_word_multiple_quotes():
    word_1 = "o'c'c" + "\u201d"
    assert Dictionary._standardize_word(word_1) == "O'C"
    word_2 = "o'clock"
    assert Dictionary._standardize_word(word_2) == "O'CLOCK"


def test_pronounce_word_no_grader(session: Session):
    with session:
        dictionary = Dictionary(session)
        word_1 = "A"
        result = dictionary.get_pronunciation_from_word(word_1)
        assert len(result) == 2

        word_2 = "dsjvkjsdvjkfd"
        result = dictionary.get_pronunciation_from_word(word_2)
        assert len(result) == 0


def test_pronounce_word_with_grader(session: Session):
    with session:
        dictionary = Dictionary(session)
        word_1 = "A"
        result = dictionary.get_pronunciation_from_word(word_1, for_grader=True)
        assert len(result) == 0

        word_2 = "affordable"
        result = dictionary.get_pronunciation_from_word(word_2, for_grader=True)
        assert len(result) == 1


def test_pronounce_text_no_grader(session: Session):
    with session:
        dictionary = Dictionary(session)
        text_1 = "A B C D E F G ??!!"
        result = dictionary.get_pronunciation_from_text(text_1)
        assert len(result) == 7
        assert len(result[0]) == 2


def test_pronounce_text_with_grader(session: Session):
    with session:
        dictionary = Dictionary(session)
        text_1 = "A B C D E F G ??!! 234 567"
        result = dictionary.get_pronunciation_from_text(text_1, for_grader=True)
        assert len(result) == 0

        text_2 = "affordable housing"
        result = dictionary.get_pronunciation_from_text(text_2, for_grader=True)
        assert len(result) == 2
