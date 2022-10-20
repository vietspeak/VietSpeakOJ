from sqlalchemy.orm import Session

from grader.grading_transcript import GradingTranscript
from utils.dictionary import Dictionary


def test_scenario(session: Session):
    dictionary = Dictionary(session)
    transcript_processor = GradingTranscript(dictionary)
    result = transcript_processor.get_grading_transcript(
        "A very good morning, teacher", "A really good morning, teacher"
    )
    assert result == "GOOD MORNING TEACHER"
