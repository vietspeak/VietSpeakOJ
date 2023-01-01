from asyncio import current_task
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from model.model import CMUPronunciation
from utils.dictionary import Dictionary
from utils.lcs import LCSResult, LongestCommonSubsequence
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from collections import Counter
import numpy as np
import statistics


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
    pronunciation_matches: List[Tuple[str, str]]


class LegacyGrader:
    def __init__(self, dictionary: Dictionary):
        self.dictionary = dictionary

    @classmethod
    def matchable(cls, a: List[CMUPronunciation], b: List[CMUPronunciation]) -> bool:
        return bool(cls.find_first_matching_pronunciation(a, b))

    @classmethod
    def find_first_matching_pronunciation(
        cls, a: List[CMUPronunciation], b: List[CMUPronunciation]
    ) -> CMUPronunciation:
        arpa_1: List[str] = [x.arpabet for x in a]
        arpa_2: Set[str] = set(x.arpabet for x in b)
        for x in arpa_1:
            if x in arpa_2:
                return x

        return None

    @classmethod
    def add_sound_to_matches(
        cls,
        pronunciation_matches: List[Tuple[str, str]],
        sound_grader: str,
        sound_student: Optional[str] = None,
    ):
        list_x = (
            [sound_grader[:-1], sound_grader[-1]]
            if "0" <= sound_grader[-1] <= "9"
            else [sound_grader]
        )

        if sound_student:
            list_y = (
                [sound_student[:-1], sound_student[-1]]
                if "0" <= sound_student[-1] <= "9"
                else [sound_student, None]
            )
        else:
            list_y = [None, None]

        for i in range(len(list_x)):
            pronunciation_matches.append((list_x[i], list_y[i]))

    def grader(self, student_script: str, grading_script: str) -> Feedback:

        student_arpabet = self.dictionary.get_pronunciation_from_text(student_script)
        grading_arpabet = self.dictionary.get_pronunciation_from_text(grading_script)

        grading_lengths = [g[0].arpabet.count(" ") + 1 for g in grading_arpabet]
        total_grading_length = sum(grading_lengths)

        total_matches_length = 0
        common = LongestCommonSubsequence.solve(
            student_arpabet, grading_arpabet, self.matchable
        )

        pronunciation_matches: List[Tuple[str, str]] = []
        for location in common.locations:
            total_matches_length += grading_lengths[location[1]]

            matching_pronunciation: List[str] = self.find_first_matching_pronunciation(
                student_arpabet[location[0]], grading_arpabet[location[1]]
            ).split(" ")

            for pro in matching_pronunciation:
                self.add_sound_to_matches(pronunciation_matches, pro, pro)

        common.locations = (
            [(-1, -1)]
            + common.locations
            + [(len(student_arpabet), len(grading_arpabet))]
        )

        print(common.locations)

        common.locations.sort(key=lambda x: x[0])

        mismatches_id: List[Tuple[int, int]] = []
        for i in range(1, len(common.locations)):
            student_range = (common.locations[i - 1][0] + 1, common.locations[i][0])
            if student_range[1] <= student_range[0]:
                continue

            grading_range = (common.locations[i - 1][1] + 1, common.locations[i][1])

            if grading_range[1] <= grading_range[0]:
                continue

            def create_arpabet_and_ranges(
                sample: List[List[CMUPronunciation]],
                rg: Tuple[int, int],
                arpabet: List[str],
                ranges: List[Tuple[int, int]],
            ):
                ptr = 0
                for id in range(rg[0], rg[1]):
                    x = sample[id]
                    current_arpabet = x[0].arpabet.split()
                    arpabet += current_arpabet

                    current_length = len(current_arpabet)
                    ranges.append((ptr, ptr + current_length))
                    ptr += current_length

            student_subset_arpabet: List[str] = []
            student_subset_ranges: List[Tuple[int, int]] = []
            create_arpabet_and_ranges(
                student_arpabet,
                student_range,
                student_subset_arpabet,
                student_subset_ranges,
            )
            student_subset_id_to_word_id = {}
            for j, x in enumerate(student_subset_ranges):
                for l in range(x[0], x[1]):
                    student_subset_id_to_word_id[l] = student_range[0] + j

            grading_subset_arpabet: List[str] = []
            grading_subset_ranges: List[Tuple[int, int]] = []
            create_arpabet_and_ranges(
                grading_arpabet,
                grading_range,
                grading_subset_arpabet,
                grading_subset_ranges,
            )

            common_subset: LCSResult = LongestCommonSubsequence.solve(
                grading_subset_arpabet, student_subset_arpabet
            )

            total_matches_length += len(common_subset)

            grading_to_student_subset_id = dict(common_subset.locations)
            student_to_grading_subset_id = dict(
                (y, x) for x, y in common_subset.locations
            )

            ptr = 0
            for j in range(len(grading_subset_arpabet)):
                if j in grading_to_student_subset_id:
                    self.add_sound_to_matches(
                        pronunciation_matches,
                        grading_subset_arpabet[j],
                        student_subset_arpabet[grading_to_student_subset_id[j]],
                    )
                    ptr = grading_to_student_subset_id[j] + 1
                else:
                    if ptr in student_to_grading_subset_id or ptr >= len(
                        student_subset_arpabet
                    ):
                        self.add_sound_to_matches(
                            pronunciation_matches, grading_subset_arpabet[j], None
                        )
                    else:
                        self.add_sound_to_matches(
                            pronunciation_matches,
                            grading_subset_arpabet[j],
                            student_subset_arpabet[ptr],
                        )
                        ptr += 1

            for j in range(grading_range[0], grading_range[1]):
                real_j = j - grading_range[0]
                matches_word_id = [
                    student_subset_id_to_word_id[grading_to_student_subset_id[x]]
                    for x in range(*grading_subset_ranges[real_j])
                    if x in grading_to_student_subset_id
                ]

                if not matches_word_id:
                    mismatches_id.append((j, None))
                    continue

                best_word = statistics.mode(matches_word_id)
                mismatches_id.append((j, best_word))

        print(len(grading_arpabet))
        print(mismatches_id)

        word_errors = []
        for x, y in mismatches_id:
            if y:
                word_errors.append(
                    (grading_arpabet[x][0].word, student_arpabet[y][0].word)
                )
            else:
                word_errors.append((grading_arpabet[x][0].word, None))

        return Feedback(
            score=total_matches_length / total_grading_length,
            errors=word_errors,
            pronunciation_matches=pronunciation_matches,
        )
