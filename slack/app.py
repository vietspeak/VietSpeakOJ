import os
from typing import Any, Dict, List, Optional

# Use the package we installed
from slack_bolt import App, Say
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_sdk.errors import SlackApiError
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from bridges.submission_task_bridge import send_cache_feedback
from config.config import MANDATORY_CHANNEL
from model.model import FileSource, Submission, User, engine

# Initializes your app with your bot token and signing secret
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)


def is_official_check(dictionary: Dict[str, Any]):
    for share_key in dictionary:
        public_list: List[str] = dictionary[share_key].keys()
        if os.environ["AUDIO_POSTED_CHANNEL"] in public_list:
            return True

    return False


@app.event("team_join")
def add_new_member_to_db(event: Optional[Dict[str, Any]], say: Say):
    user: Dict[str, Any] = event.get("user")
    with Session(engine) as session:
        find_user_stmt = select(User).where(User.slack_id == user["id"])
        user_obj: User = next(session.scalars(find_user_stmt), None)

        if user_obj:
            user_obj.update_from_dict(user)
        else:
            user_obj = User.from_dict(user)
            session.add(user_obj)
        session.commit()


@app.event("file_shared")
def file_shared_handler(event: Optional[Dict[str, Any]], say: Say):
    with Session(engine) as session:
        file_id = event.get("file_id")
        find_cache_submission = select(Submission).where(
            and_(Submission.audio_file == bytes(file_id, encoding="utf-8"),
            Submission.source == FileSource.SLACK)

        )

        cache_submission: Submission = next(
            session.scalars(find_cache_submission), None
        )
        try:
            file_info = app.client.files_info(file=file_id)
        except SlackApiError:
            file_info = {}

        is_official = is_official_check(file_info.get("file", {}).get("shares", {}))

        if cache_submission:
            cache_submission.is_official = is_official
            session.commit()
            send_cache_feedback(app, session, cache_submission)
            return

        find_real_user_id = select(User).where(User.slack_id == event.get("user_id"))
        user: User = next(session.scalars(find_real_user_id), None)

        if not user:
            say("Bot chưa biết bạn là ai. Hãy đợi bot 1 phút để tìm hiểu bạn.")
            return

        new_submission = Submission(
            source=FileSource.SLACK,
            user_id=user.id,
            is_official=is_official,
            audio_file=bytes(event.get("file_id"), encoding="utf-8"),
        )
        session.add(new_submission)
        session.commit()

@app.message()
def a_likely_feedback_is_posted(logger, event: Optional[Dict[str, Any]]):
    user, text = event["user"], event["text"]
    logger.info(f"The user {user} changed the message to {text}")

from flask import Flask, request

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


# Start your app
if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))
