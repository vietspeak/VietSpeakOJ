import re
from collections import defaultdict
from io import FileIO
from typing import DefaultDict, Generator, List

from sqlalchemy.orm import Session

from model.model import CMUPronunciation, engine

DICTIONARY_PATH = "./install/cmudict-0.7b.txt"
VALID_WORD_PATTERN = r"([A-Z]+)((\([0-9]+\))*)(\s+)([A-Z0-9][A-Z0-9\s]*)"

NUM_WORDS = {
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
    "twenty",
    "thirty",
    "forty",
    "fifty",
    "sixty",
    "seventy",
    "eighty",
    "ninety",
    "hundred",
    "thousand",
    "million",
    "billion",
    "trillion",
}

NUM_PRONOUNCIATION_EXCEPTIONS = {"EY1 T", "T EH1 N", "EY1 T IY0"}

ARPABET_TO_IPA = {
    "AA": "ɑ",
    "AE": "æ",
    "AH": "ə",
    "AO": "ɔ",
    "AW": "aʊ",
    "AY": "aɪ",
    "B": "b",
    "CH": "tʃ",
    "D": "d",
    "DH": "ð",
    "EH": "ɛ",
    "ER": "ɝ",
    "EY": "eɪ",
    "F": "f",
    "G": "ɡ",
    "HH": "h",
    "IH": "ɪ",
    "IY": "i",
    "JH": "dʒ",
    "K": "k",
    "L": "l",
    "M": "m",
    "N": "n",
    "NG": "ŋ",
    "OW": "oʊ",
    "OY": "ɔɪ",
    "P": "p",
    "R": "ɹ",
    "S": "s",
    "SH": "ʃ",
    "T": "t",
    "TH": "θ",
    "UH": "ʊ",
    "UW": "u",
    "V": "v",
    "W": "w",
    "Y": "j",
    "Z": "z",
    "ZH": "ʒ",
}

PRIMARY_STRESS = "ˈ"
SECONDARY_STRESS = "ˌ"


class DictionaryETL:
    @classmethod
    def extract(cls, file: FileIO) -> DefaultDict[str, List[str]]:
        word_pronunciation_pairs: Generator[str] = (
            matches.group(1, 5)
            for line in file
            if (matches := re.fullmatch(VALID_WORD_PATTERN, line.strip()))
        )
        data: DefaultDict[str, List[str]] = defaultdict(list)
        WORD = 0
        PRONUNCIATION = 1
        for pair in word_pronunciation_pairs:
            data[pair[WORD]].append(pair[PRONUNCIATION])

        return data

    @classmethod
    def arpabets_to_ipa(cls, arpabets):
        symbols = arpabets.split()

        result = []

        for sym in symbols:
            matches = re.fullmatch("([A-Z]*)([0-9]*)", sym)
            result.append(ARPABET_TO_IPA[matches.group(1)])
            if matches.group(2):
                index = int(matches.group(2))
                if index == 1:
                    result.append(PRIMARY_STRESS)
                elif index != 0:
                    result.append(SECONDARY_STRESS)

        return "".join(result)

    @classmethod
    def transform(cls, data: DefaultDict[str, List[str]]) -> List[CMUPronunciation]:
        number_pronunciations: List[str] = []
        for x in NUM_WORDS:
            assert x.upper() in data
            number_pronunciations += data[x.upper()]

        pronounce_objects: List[CMUPronunciation] = []

        for word, pronunciations in data.items():

            def number_pronunciation_checker() -> bool:
                for pronunciation in pronunciations:
                    for number in number_pronunciations:
                        if number == pronunciation or (
                            number not in NUM_PRONOUNCIATION_EXCEPTIONS
                            and (
                                pronunciation.startswith(number)
                                or pronunciation.endswith(number)
                            )
                        ):
                            return True
                return False

            use_in_grader: bool = len(word) > 3 and (not number_pronunciation_checker())

            for pronunciation in pronunciations:
                pronounce_objects.append(
                    CMUPronunciation(
                        word=word,
                        arpabet=pronunciation,
                        ipa=cls.arpabets_to_ipa(pronunciation),
                        use_in_grader=use_in_grader,
                    )
                )

        return pronounce_objects

    @classmethod
    def load(cls, session: Session, pronounce_objects: List[CMUPronunciation]):
        session.add_all(pronounce_objects)
        session.commit()

    @classmethod
    def pipeline(cls, file, session):
        data = cls.extract(file)
        pronounce_objects = cls.transform(data)
        cls.load(session, pronounce_objects)


def entry_point():
    with open(DICTIONARY_PATH, "r") as f:
        with Session(engine) as session:
            DictionaryETL.pipeline(f, session)


if __name__ == "__main__":
    entry_point()
