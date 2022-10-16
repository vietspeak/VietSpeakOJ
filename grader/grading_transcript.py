from typing import List
from model.model import CMUPronunciation

from utils.dictionary import Dictionary
from utils.lcs import LongestCommonSubsequence


class GradingTranscript:
    def __init__(self, dictionary: Dictionary):
        self.dictionary = dictionary

    def get_grading_transcript(
        self, sample_transcript: str, sample_audio_transcript: str
    ) -> str:
        sample_pronounce = self.dictionary.get_pronunciation_from_text(
            sample_transcript, for_grader=True
        )
        audio_pronounce = self.dictionary.get_pronunciation_from_text(
            sample_audio_transcript, for_grader=True
        )
        sample_pronounce: List[str] = [
            word_list[0].word for word_list in sample_pronounce
        ]
        audio_pronounce: List[str] = [
            word_list[0].word for word_list in audio_pronounce
        ]
        longest_common: List[str] = LongestCommonSubsequence.solve(
            sample_pronounce, audio_pronounce
        )
        return " ".join(longest_common)

class SimpleGrader:
    def __init__(self, dictionary: Dictionary):
        self.dictionary = dictionary
    
    @classmethod
    def _get_chosen_arpabet(cls, pronunciations: List[CMUPronunciation]) -> CMUPronunciation:
        max_schwa = 0
        chosen = None
        for pronounce in pronunciations:
            number_of_schwa = pronounce.arpabet.count("AH")
            if chosen is None or number_of_schwa > max_schwa:
                max_schwa = number_of_schwa
                chosen = pronounce
        return chosen

    def _get_chosen_arpabet_script(self, script: str) -> List[str]:
        pronunciations = self.dictionary.get_pronunciation_from_text(script)
        arpabets = [self._get_chosen_arpabet(pronounce).arpabet.split() for pronounce in pronunciations]
        result = []
        for arpa in arpabets:
            result += arpa
        return result

    
    def grader(self, student_script: str, grading_script: str) -> float:
        student_arpabet = self._get_chosen_arpabet_script(student_script)
        grading_arpabet = self._get_chosen_arpabet_script(grading_script)
        common = LongestCommonSubsequence.solve(student_arpabet, grading_arpabet)
        return len(common) / max(1, len(grading_arpabet))