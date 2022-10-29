from dataclasses import dataclass
from typing import Dict, List, Tuple

from model.model import CMUPronunciation
from utils.dictionary import Dictionary
from utils.lcs import LongestCommonSubsequence
from collections import Counter

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
        ).values
        return " ".join(longest_common)


@dataclass
class Feedback:
    score: float
    errors: List[Tuple[str, str]]

class LegacyGrader:
    def __init__(self, dictionary: Dictionary):
        self.dictionary = dictionary

    @classmethod
    def _get_chosen_arpabet(
        cls, pronunciations: List[CMUPronunciation]
    ) -> CMUPronunciation:
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
        arpabets: List[str] = []
        word_ranges: List[Tuple[str, Tuple[int, int]]] = []
        result = []
        ptr = 0
        for pronounce in pronunciations:
            cmu_pronunciation = self._get_chosen_arpabet(pronounce)
            sounds = cmu_pronunciation.arpabet.split()
            result+=sounds
            word_ranges.append((cmu_pronunciation.word, (ptr, ptr + len(sounds))))
            ptr += len(sounds)
        
        return result, word_ranges

    def grader(self, student_script: str, grading_script: str) -> Feedback:
        student_arpabet, student_ranges = self._get_chosen_arpabet_script(student_script)
        grading_arpabet, grading_ranges = self._get_chosen_arpabet_script(grading_script)
        common = LongestCommonSubsequence.solve(student_arpabet, grading_arpabet)


        score = len(common) / max(1, len(grading_arpabet))

        position_to_student_word_indexes: List[int] = [None] * len(student_arpabet)
        for id, r in enumerate(student_ranges):
            for x in range(*r[1]):
                position_to_student_word_indexes[x] = id

        grading_map: Dict[int, int] = {}
        for pair in common.locations:
            grading_map[pair[1]] = pair[0]

        
        errors = []
        for id, r in enumerate(grading_ranges):
            mistake = False
            for x in range(*r[1]):
                if x not in grading_map:
                    mistake = True
                    break
            
            if mistake:
                matches_word = [position_to_student_word_indexes[grading_map[x]] for x in range(*r[1]) if x in grading_map]
                if not matches_word:
                    errors.append((r[0], None))
                else:
                    most_common_match = Counter(matches_word).most_common(1)[0][0]
                    right_word = student_ranges[most_common_match][0]
                    if grading_arpabet[id] != student_arpabet[most_common_match]:
                        errors.append((r[0], right_word))

        return Feedback(score=score, errors=errors)

            
