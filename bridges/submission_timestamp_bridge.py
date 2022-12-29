from datetime import datetime
from typing import List, Tuple

from sqlalchemy import update, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from model.model import User
from utils.timezone_converter import FORMAT


def entry_point(session: Session):
    submission_stmt = text(
        """
        SELECT user_id, MAX(created_time) AS created_time
        FROM (
            SELECT user_id, MIN(created_time) AS created_time
            FROM submissions
            WHERE (is_official AND task_id IS NOT NULL)
            GROUP BY user_id, task_id
        )
        GROUP BY user_id
    """
    )

    result: List[Tuple[int, str]] = session.execute(submission_stmt)
    for row in result:
        user_id, timestamp = row
        user_obj: User = session.scalar(select(User).where(User.id == user_id))
        new_timestamp = datetime.strptime(timestamp, FORMAT)
        if user_obj and user_obj.last_official_submission_timestamp != new_timestamp:
            user_obj.last_official_submission_timestamp = new_timestamp
    session.commit()
