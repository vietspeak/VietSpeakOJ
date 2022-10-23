import os
from slack.app import flask_app

if __name__ == "__main__":
    flask_app.run(port=int(os.environ.get("PORT", 3000)))
