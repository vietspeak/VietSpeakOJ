from bridges.submission_audio_bridge import vtt_link_to_transcript

def test_vtt():
    result = vtt_link_to_transcript("https://files.slack.com/files-tmb/T01BUG1HQDB-F048NQEEXTM-9cef57b246/file.vtt?_xcb=b0435")
    assert "An english professor wrote the words Woman without her man" in result