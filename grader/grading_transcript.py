from dataclasses import dataclass
from typing import Dict, List, Tuple

from model.model import CMUPronunciation
from utils.dictionary import Dictionary
from utils.lcs import LongestCommonSubsequence
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from collections import Counter
import numpy as np

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

    def _get_chosen_arpabet_script(self, script: str) -> Tuple[List[str], List[Tuple[str, Tuple[int, int]]]]:
        pronunciations = self.dictionary.get_pronunciation_from_text(script)
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

        
        errors: List[List[int]] = []
        current_min_indexed: List[int] = []
        minimum_index = 0
        for id, r in enumerate(grading_ranges):
            matches_word = [position_to_student_word_indexes[grading_map[x]] for x in range(*r[1]) if x in grading_map]
            mistake = len(matches_word) < r[1][1] - r[1][0]

            if not mistake:
                minimum_index = max(minimum_index, max(matches_word))
                continue
            
            if not matches_word:
                current_min_indexed.append(minimum_index)
                errors.append([id, None])
                continue
            
            most_common_match = Counter(matches_word).most_common(1)[0][0]
            if most_common_match < minimum_index:
                current_min_indexed.append(minimum_index)
                errors.append([id, None])
                continue
            
            minimum_index = most_common_match + 1

            if grading_arpabet[id] != student_arpabet[most_common_match]:
                current_min_indexed.append(minimum_index)
                errors.append([id, most_common_match])


        if errors:
            vectorizer = TfidfVectorizer()
            corpus: List[str] = []
            corpus_indexes = []
            for id, r in enumerate(student_ranges):
                if r[1][1] - r[1][0] > 3:
                    corpus.append(" ".join(student_arpabet[r[1][0]:r[1][1]]))
                    corpus_indexes.append(id)
            
            arpabet_matrix = vectorizer.fit_transform(corpus)

            for i in range(len(errors)):
                if current_min_indexed[i] >= len(student_arpabet):
                    break
                if errors[i][1] is not None:
                    continue

                grading_index = errors[i][0]
                grading_vector = vectorizer.transform([" ".join(grading_arpabet[grading_index])])
                similarities: np.ndarray = linear_kernel(grading_vector, arpabet_matrix).flatten()
                
                for matching_id in similarities.argsort()[-10:]:
                    if corpus_indexes[matching_id] >= current_min_indexed[i]:
                        errors[i][1] = corpus_indexes[matching_id]
        
        word_errors: List[Tuple[str, str]] = []
        for x, y in errors:
            if y:
                word_errors.append((grading_ranges[x][0], student_ranges[y][0]))
            else:
                word_errors.append((grading_ranges[x][0], None))

        return Feedback(score=score, errors=word_errors)

            
