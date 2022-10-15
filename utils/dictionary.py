
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select
from model.model import CMUPronunciation
from sqlalchemy import and_
import re

class Dictionary:
    def __init__(self, session: Session):
        self.session = session

    @classmethod
    def _remove_smart_quotes(cls, word: str) -> str:
        return word.replace(u"\u2018", "'").replace(u"\u2019", "'").replace(u"\u201c",'"').replace(u"\u201d",'"')
    
    @classmethod
    def _standardize_word(cls, word: str) -> str:
        word = cls._remove_smart_quotes(word.upper())
        find_word = re.search("[A-Z]+'?[A-Z]*", word)
        if find_word:
            return find_word[0]
        return None
    
    def get_pronunciation_from_word(self, word: str, for_grader: bool=False) -> List[CMUPronunciation]:
        word = Dictionary._standardize_word(word)
        if not word:
            return []
        
        if for_grader:
            stmt = select(CMUPronunciation).where(and_(CMUPronunciation.word == word, CMUPronunciation.use_in_grader))
        else:
            stmt = select(CMUPronunciation).where(CMUPronunciation.word == word)

        return list(self.session.scalars(stmt))

    def get_pronunciation_from_text(self, text: str, for_grader: bool=False) -> List[List[CMUPronunciation]]:
        result = []
        for word in text.split():
            pronounce_list : List[CMUPronunciation] = self.get_pronunciation_from_word(word, for_grader)
            if pronounce_list:
                result.append(pronounce_list)
        return result
