import re
from typing import List

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from model.model import CMUPronunciation


class Dictionary:
    def __init__(self, session: Session):
        self.session = session

    @classmethod
    def _remove_smart_quotes(cls, word: str) -> str:
        return (
            word.replace("\u2018", "'")
            .replace("\u2019", "'")
            .replace("\u201c", '"')
            .replace("\u201d", '"')
        )

    @classmethod
    def _standardize_word(cls, word: str) -> str:
        word = cls._remove_smart_quotes(word.upper())
        find_word = re.search("[A-Z]+['-]?[A-Z]*", word)
        if find_word:
            return find_word[0]
        return None

    def get_pronunciation_from_word(
        self, word: str, for_grader: bool = False
    ) -> List[CMUPronunciation]:
        word = Dictionary._standardize_word(word)
        if not word:
            return []

        if for_grader:
            stmt = select(CMUPronunciation).where(
                and_(CMUPronunciation.word == word, CMUPronunciation.use_in_grader)
            )
        else:
            stmt = select(CMUPronunciation).where(CMUPronunciation.word == word)

        result: List[CMUPronunciation] = list(self.session.scalars(stmt))
        result.sort(key=lambda x: x.ipa.count("ə"), reverse=True)
        return result


    def get_pronunciation_from_text(
        self, text: str, for_grader: bool = False
    ) -> List[List[CMUPronunciation]]:
        result = []
        for word in text.split():
            pronounce_list: List[CMUPronunciation] = self.get_pronunciation_from_word(
                word, for_grader
            )
            if pronounce_list:
                result.append(pronounce_list)
        return result
