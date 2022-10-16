# VietSpeakGrader
A module that gives pronunciation score based on the audio transcript produced by Kaldi/Slack and the model transcript. Powered by the Carnegie Mellon University Pronouncing Dictionary

## Development installation
```
conda create -n vietspeakoj python black isort pytest pytest-cov sqlalchemy
conda activate vietspeakoj
mkdir database
python3 installer.py
```

## Testing
```
coverage run -m pytest tests && coverage report --show-missing
```
