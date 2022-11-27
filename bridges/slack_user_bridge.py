import logging
import random
import string
import time
from typing import Any, Dict, List

from slack_sdk.errors import SlackApiError
from sqlalchemy import select
from sqlalchemy.orm import Session
from http.client import IncompleteRead
from model.model import User
from slack_bolt import App

logger = logging.getLogger(__name__)


def entry_point(app: App, session: Session = None):
    all_users = []
    try:
        cursor = None
        while True:
            response = app.client.users_list(cursor=cursor, limit=100)
            if len(response["members"]) == 0:
                break
            all_users.extend(response["members"])
            cursor = response["response_metadata"]["next_cursor"]
            if not cursor:
                break

    except SlackApiError as e:
        logger.error("Error creating conversation: {}".format(e))
    except IncompleteRead as e:
        logger.error(f"Error creating conversation: {e}")

    new_users: List[User] = []
    for user in all_users:
        find_user_stmt = select(User).where(User.slack_id == user["id"])
        user_obj: User = next(session.scalars(find_user_stmt), None)
        if user_obj:
            user_obj.update_from_dict(user)
        else:
            user_obj = User.from_dict(user)
            new_users.append(user_obj)

    session.add_all(new_users)
    session.commit()
