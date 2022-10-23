import os

# Use the package we installed
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler


# Initializes your app with your bot token and signing secret
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)

from flask import Flask, request

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

# Start your app
if __name__ == "__main__":
    flask_app.run(port=int(os.environ.get("PORT", 3000)))
