import os
from typing import Any, Dict, Optional
import logging

# Use the package we installed
from slack_bolt import App, Say
from slack_bolt.adapter.flask import SlackRequestHandler
from config.config import MANDATORY_CHANNEL
from model.model import FileSource, Submission, User, engine
from slack_sdk.web.client import WebClient
from sqlalchemy.orm import Session
from sqlalchemy import select

# Initializes your app with your bot token and signing secret
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)


@app.event("file_shared")
def file_shared_handler(event: Optional[Dict[str, Any]], say: Say):
    with Session(engine) as session:
        find_real_user_id = select(User).where(User.slack_id == event.get("user_id"))
        user: User = next(session.scalars(find_real_user_id), None)

        if not user:
            say("Bot chưa biết bạn là ai. Hãy đợi bot 1 phút để tìm hiểu bạn.")
            return
        
        new_submission = Submission(
            source=FileSource.SLACK,
            user_id=user.id,
            audio_file=bytes(event.get("file_id"), encoding="utf-8"),
        )
        session.add(new_submission)
        session.commit()


from flask import Flask, request

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


# Start your app
if __name__ == "__main__":
    flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 3000)))
