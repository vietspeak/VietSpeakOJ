from datetime import datetime
from typing import List, Tuple

from sqlalchemy import update
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
        update_stmt = (
            update(User)
            .where(User.id == user_id)
            .values(
                last_official_submission_timestamp=datetime.strptime(timestamp, FORMAT)
            )
        )
        session.execute(update_stmt)
    session.commit()
