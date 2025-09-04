import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.municipal_modules.setagaya2.parsers.setagaya2_parser import Setagaya2Parser


def test_extract_speeches_handles_nbsp_markers():
    parser = Setagaya2Parser()
    topic_text = (
        "質問者\n"
        "<strong>議題</strong><br>"
        "<strong>質問&nbsp;</strong>質問内容<br>"
        "<strong>答弁&nbsp;</strong>答弁者<br>答弁内容"
    )
    speeches = parser.extract_speeches(topic_text)
    assert len(speeches) == 3
    assert speeches[1]["name"] == "質問者"
    assert speeches[1]["comment"] == "質問内容"
    assert speeches[2]["name"] == "答弁者"
    assert speeches[2]["comment"] == "答弁内容"


def test_extract_speeches_handles_direct_speaker_strong():
    parser = Setagaya2Parser()
    topic_text = (
        "質問者\n"
        "<strong>議題</strong><br>"
        "<strong>質問</strong>質問内容<br>"
        "<strong>教育長&nbsp;</strong>答弁内容"
    )
    speeches = parser.extract_speeches(topic_text)
    assert len(speeches) == 3
    assert speeches[2]["name"] == "教育長"
    assert speeches[2]["comment"] == "答弁内容"
