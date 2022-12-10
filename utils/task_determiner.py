import re
from typing import List

from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from sqlalchemy import select
from sqlalchemy.orm import Session

from model.model import Task

MAX_TRAINING_TRANSCRIPTS = 100


class TaskDeterminer:
    def __init__(self, session: Session):
        self.session = session
        self.corpus: List[str] = []
        self.task_ids: List[int] = []
        self.vectorizer = TfidfVectorizer()
        self.word_matrix: sparse = []

    def _reload_data(self):
        max_task_id = self.task_ids[-1] if self.task_ids else 0
        stmt = select(Task).where(Task.id > max_task_id).order_by(Task.id)
        new_tasks: List[Task] = list(self.session.scalars(stmt))

        if not new_tasks:
            return

        for task in new_tasks:
            self.task_ids.append(task.id)
            self.corpus.append(task.grading_transcript)

        self.vectorizer = TfidfVectorizer()
        self.word_matrix = self.vectorizer.fit_transform(self.corpus)

    def detect_task(self, transcript: str) -> int:
        self._reload_data()

        if len(self.task_ids) == 0:
            return None

        transcript_vector = self.vectorizer.transform([transcript])
        similarities = linear_kernel(transcript_vector, self.word_matrix).flatten()
        best_index = similarities.argsort()[-1]
        return self.task_ids[best_index]
