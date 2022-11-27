# VietSpeakOJ
A module that gives pronunciation score based on the audio transcript produced by Kaldi/Slack and the model transcript. Powered by the Carnegie Mellon University Pronouncing Dictionary and VOSK API

## Development installation
```
python3 -m venv env
source env/bin/activate
pip3 install black isort pytest pytest-cov sqlalchemy wheel gunicorn flask vosk slack_bolt scikit-learn aiohttp alembic
sudo apt-get install ffmpeg unzip
mkdir database
mkdir tmp
python3 installer.py
```

Add the following lines to the end of your `~/.bashrc` file
```
export SLACK_BOT_TOKEN=<your Slack bot token>
export SLACK_SIGNING_SECRET=<your Slack signing secret>
export PORT=<port>
```

Run the following command
```
. ~/.bashrc
```

Download a model from https://alphacephei.com/vosk/models, and unzip the model. Then, rename the new folder `vosk_model`
## Testing
```
coverage run -m pytest tests && coverage report --show-missing
```
## Make changes to the database
```
alembic revision --autogenerate -m "Your commit message"
alembic upgrade heads
```

## Deployment
```
sudo ufw allow $PORT
gunicorn --bind 0.0.0.0:$PORT wsgi:flask_app
```
## Load remote database
```
scp $REMOTE_SERVER:~/VietSpeakOJ/database/db.sqlite ./database/db.sqlite
```
