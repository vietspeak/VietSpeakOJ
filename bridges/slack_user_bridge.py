import logging
import random
import string
import time
from typing import List

from slack_sdk.errors import SlackApiError
from sqlalchemy import select
from sqlalchemy.orm import Session

from model.model import User
from slack.app import app

logger = logging.getLogger(__name__)


def generate_password(length: int = 10) -> str:
    return "".join(random.choice(string.ascii_letters) for _ in range(length))


def entry_point(session: Session = None):
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

    new_users: List[User] = []
    for user in all_users:
        print(user)
        find_user_stmt = select(User).where(User.slack_id == user["id"])
        user_obj: User = next(session.scalars(find_user_stmt), None)

        user_email = user["profile"].get("email")
        is_bot = user.get("is_bot", False)
        is_owner = user.get("is_owner", False)
        is_admin = user.get("is_admin", False)
        if user_obj:
            user_obj.email = user_email
            user_obj.is_bot = is_bot
            user_obj.is_owner = is_owner
            user_obj.is_admin = is_admin
        else:
            user_obj = User(
                slack_id=user["id"],
                email=user_email,
                password=generate_password(),
                first_seen_timestamp=time.time_ns(),
                is_bot=is_bot,
                is_owner=is_owner,
                is_admin=is_admin,
            )
            new_users.append(user_obj)

    session.add_all(new_users)
    session.commit()
