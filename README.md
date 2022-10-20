# VietSpeakOJ
A module that gives pronunciation score based on the audio transcript produced by Kaldi/Slack and the model transcript. Powered by the Carnegie Mellon University Pronouncing Dictionary and VOSK API

## Development installation
```
conda create -n vietspeakoj python black isort pytest pytest-cov sqlalchemy flask
conda activate vietspeakoj
sudo apt-get install ffmpeg unzip
pip3 install vosk
mkdir database
mkdir vosk_model
python3 installer.py
```

Download a model from https://alphacephei.com/vosk/models, and unzip the model. Then, rename the new folder `vosk_model`
## Testing
```
coverage run -m pytest tests && coverage report --show-missing
```
