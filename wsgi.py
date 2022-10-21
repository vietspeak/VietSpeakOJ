import os

from slack.app import app

if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
