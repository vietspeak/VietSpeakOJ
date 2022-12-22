from sqlalchemy import update
from sqlalchemy.orm import Session

from config.config import NUMBER_OF_RESTING_DAYS
from model.model import User


def entry_point(session: Session):
    user_stmt = f"""
        SELECT id FROM users
        WHERE (JULIANDAY(CURRENT_TIMESTAMP) - JULIANDAY(created_time) > {NUMBER_OF_RESTING_DAYS})
            AND (
                last_official_submission_timestamp IS NULL or
                second_to_last_human_feedback_timestamp IS NULL or
                julianday(current_timestamp) - julianday(last_official_submission_timestamp) > {NUMBER_OF_RESTING_DAYS} or
                julianday(current_timestamp) - julianday(second_to_last_human_feedback_timestamp) > {NUMBER_OF_RESTING_DAYS})
            AND (not is_bot)
            AND (not is_admin)
            AND (not is_owner)
            AND (not is_eliminated)
    """

    for user in session.execute(user_stmt):
        user_id: int = user[0]
        update_stmt = update(User).where(User.id == user_id).values(is_eliminated=True)
        session.execute(update_stmt)
    session.commit()
