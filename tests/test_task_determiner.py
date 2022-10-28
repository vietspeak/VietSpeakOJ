from unittest.mock import Mock

from pytest import fixture
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlalchemy.orm import Session
from utils.task_determiner import TaskDeterminer


@fixture
def task_determiner():
    session = Mock(spec=Session)
    obj = TaskDeterminer(session)
    obj._reload_data = Mock()
    return obj


def test_detect_task(task_determiner: TaskDeterminer):
    task_determiner.corpus = [
        """Gas / Get / Gown / Good
Rash / Red / Round / Root
I’m Going to Go Get some Gas.
I have some Red Rashes aRound my arms.
GRaph / GRease / GRind / GRill / GRowth / GRave / GRape
GRandma is GRaceful to find a GReat GRoup of GRoundskeepers.""",
        """
        "State / Steam / Stove / Stall / Stick / Stumble / Stimulate
Tasty / Nasty / Esteem / Constant / Substance / Majestic
Waist / Pest / Roast / Moist / Boost / Novelist / Dishonest
Standstill / Statistic / Stainless-Steel
Stop wasting stamina over the past.
The custodian stained the customer’s costume.
        """,
        """
        Ox / Lunar / Joy / Celebrate
Wish / Dream / Peace / Happiness
Wealth / Health / Success / Pleasure Abundance / Adventure / Achievement / Ambition
Prosperous / Prosperity / Longevity Resolution / Opportunity
        """,
        """
        Germ                    Bird                       Burn
Her                        Dirt                       Fur
Nerd                     Girl                        Hurt
Perm                     Quirk                    Church
Term                     Sir                          Turn
*Learn                  *Work                  *Word
Intern                   Thirsty                  Urban
Concern               Confirm                 Occur
Internal                Affirmative          Occurrence
        """,
    ]

    task_determiner.task_ids = [4, 2, 3, 1]
    task_determiner.vectorizer = TfidfVectorizer()
    task_determiner.word_matrix = task_determiner.vectorizer.fit_transform(
        task_determiner.corpus
    )

    results = [task_determiner.detect_task(task) for task in task_determiner.corpus]

    assert results == task_determiner.task_ids
