from typing import List
from utils.dictionary import Dictionary
from utils.lcs import LongestCommonSubsequence

class GradingTranscript:
    
    def __init__(self, dictionary: Dictionary):
        self.dictionary = dictionary
    
    def get_grading_transcript(self, sample_transcript: str, sample_audio_transcript: str) -> str:
        sample_pronounce = self.dictionary.get_pronunciation_from_text(sample_transcript, for_grader=True)
        audio_pronounce = self.dictionary.get_pronunciation_from_text(sample_audio_transcript, for_grader=True)
        sample_pronounce: List[str] = [word_list[0].word for word_list in sample_pronounce]
        audio_pronounce: List[str] = [word_list[0].word for word_list in audio_pronounce]
        longest_common: List[str] = LongestCommonSubsequence.solve(sample_pronounce, audio_pronounce)
        return " ".join(longest_common)

        