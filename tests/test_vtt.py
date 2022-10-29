from bridges.submission_audio_bridge import vtt_link_to_transcript

def test_vtt():
    result = vtt_link_to_transcript("https://files.slack.com/files-tmb/T01BUG1HQDB-F0488C72ECF-2ed6d32c6c/file.vtt?_xcb=749ed")
    assert "An english professor wrote the words Woman without her man" in result