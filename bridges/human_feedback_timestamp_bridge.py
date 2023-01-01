from datetime import datetime
from typing import List, Tuple

from sqlalchemy import update, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from model.model import User
from utils.timezone_converter import FORMAT


def entry_point(session: Session):
    feedback_stmt = text(
        """
        SELECT user_id, created_time
        FROM (
            SELECT user_id, created_time, dense_rank() OVER (PARTITION BY user_id ORDER BY created_time DESC) as ranking
            FROM (
	            SELECT H.user_id AS user_id,
		               MIN(H.created_time) AS created_time
	            FROM human_feedback H, submissions S
	            WHERE H.submission_id == S.id AND H.user_id != S.user_id
	            GROUP BY H.user_id, S.id
            )
        )
        WHERE ranking = 2;
    """
    )

    result: List[Tuple[int, str]] = session.execute(feedback_stmt)
    for row in result:
        user_id, timestamp = row
        user_stmt = select(User).where(User.id == user_id)
        user_obj: User = session.scalar(user_stmt)
        new_timestamp = datetime.strptime(timestamp, FORMAT)
        if (
            user_obj
            and user_obj.second_to_last_human_feedback_timestamp != new_timestamp
        ):
            user_obj.second_to_last_human_feedback_timestamp = new_timestamp
    session.commit()
