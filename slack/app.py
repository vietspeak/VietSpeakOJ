import os
from typing import Any, Dict, Optional
import logging

# Use the package we installed
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from config.config import MANDATORY_CHANNEL
from model.model import FileSource, Submission, engine
from slack_sdk.web.client import WebClient
from sqlalchemy.orm import Session

# Initializes your app with your bot token and signing secret
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)


@app.event("file_shared")
def file_shared_handler(event: Optional[Dict[str, Any]]):
    logging.info("I'm here")
    
    with Session(engine) as session:
        new_submission = Submission(
            source=FileSource.SLACK,
            user_id=event.get("user_id"),
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
