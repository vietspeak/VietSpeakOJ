from sqlalchemy import update
from sqlalchemy.orm import Session

from config.config import NUMBER_OF_RESTING_DAYS
from model.model import User


def entry_point(session: Session):
    user_stmt = f"""
        SELECT id FROM users
        WHERE ((JULIANDAY(CURRENT_TIMESTAMP) - JULIANDAY(created_time) < {NUMBER_OF_RESTING_DAYS})
            OR (last_official_submission_timestamp IS NOT NULL AND
                second_to_last_human_feedback_timestamp IS NOT NULL AND
                julianday(current_timestamp) - julianday(last_official_submission_timestamp) <= {NUMBER_OF_RESTING_DAYS} AND
                julianday(current_timestamp) - julianday(second_to_last_human_feedback_timestamp) <= {NUMBER_OF_RESTING_DAYS})
            OR is_bot
            OR is_admin
            OR is_owner)
            AND is_eliminated
    """

    for user in session.execute(user_stmt):
        user_id: int = user[0]
        update_stmt = update(User).where(
            User.id == user_id).values(
            is_eliminated=False)
        session.execute(update_stmt)
    session.commit()
