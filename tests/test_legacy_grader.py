from grader.grading_transcript import LegacyGrader
from utils.dictionary import Dictionary
from pytest import fixture

@fixture
def grader(dictionary: Dictionary) -> LegacyGrader:
    return LegacyGrader(dictionary)

def test_legacy_grader(grader: LegacyGrader):
    grading_result = grader.grader("A very good morning teacher", "A really good morning teacher")
    assert abs(grading_result.score -  8/9) < 1e-6
    assert grading_result.errors == [("REALLY", "VERY")]
     

