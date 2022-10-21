# VietSpeakOJ
A module that gives pronunciation score based on the audio transcript produced by Kaldi/Slack and the model transcript. Powered by the Carnegie Mellon University Pronouncing Dictionary and VOSK API

## Development installation
```
conda create -n vietspeakoj python black isort pytest pytest-cov sqlalchemy flask gunicorn
conda activate vietspeakoj
sudo apt-get install ffmpeg unzip ngrok
pip3 install vosk slack_bolt
mkdir database
mkdir vosk_model
python3 installer.py
```

Add the following lines to the end of your `.bashrc` file
```
export SLACK_BOT_TOKEN=<your Slack bot token>
export SLACK_SIGNING_SECRET=<your Slack signing secret>
```

Download a model from https://alphacephei.com/vosk/models, and unzip the model. Then, rename the new folder `vosk_model`
## Testing
```
coverage run -m pytest tests && coverage report --show-missing
```
## Deployment
```
sudo ufw allow <port>
gunicorn --bind 0.0.0.0:<port> web_app:app
```
