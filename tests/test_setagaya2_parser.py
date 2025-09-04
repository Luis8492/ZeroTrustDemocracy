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


def test_extract_topic_section_returns_empty_when_no_topics():
    parser = Setagaya2Parser()
    text = "<h1>令和6年第1回定例会 代表質問</h1>"
    sections = parser.extract_topic_section(text)
    assert sections == []


def test_extract_topic_section_parses_representative_questions():
    parser = Setagaya2Parser()
    text = (
        "<h1>令和6年第1回定例会 代表質問</h1>"
        "<h2><a>質問者</a></h2>"
        "<ul><li><strong>議題</strong><br>内容</li></ul>"
        "<h2></h2>"
    )
    sections = parser.extract_topic_section(text)
    assert sections == ["質問者\n<strong>議題</strong><br>内容"]


def test_extract_topic_section_parses_general_questions():
    parser = Setagaya2Parser()
    text = (
        "<h1>令和6年第1回定例会 一般質問</h1>"
        "<h2><a>質問者</a></h2>"
        "<ul><li><strong>議題</strong><br>内容</li></ul>"
        "<h2></h2>"
    )
    sections = parser.extract_topic_section(text)
    assert sections == ["質問者\n<strong>議題</strong><br>内容"]


def test_extract_meeting_data_classifies_pattern():
    parser = Setagaya2Parser()
    text = "<ul><li><ul><li><strong>質問</strong></li></ul></li></ul>"
    meeting = parser.extract_meeting_data(text)
    assert parser.pattern == "Pattern1"
    assert "pattern" not in meeting


def test_convert_produces_minute_json_with_qas():
    from app.municipal_modules.setagaya2.parsers import setagaya2_parser
    setagaya2_parser.classify_pattern = lambda _text: "Pattern1"
    parser = Setagaya2Parser()
    text = (
        "<h1>令和6年第1回定例会 代表質問</h1>"
        "<h2><a>質問者</a></h2>"
        "<ul><li>"
        "<strong>議題</strong><br>"
        "<strong>質問</strong>質問内容<br>"
        "<strong>答弁</strong>答弁者<br>答弁内容"
        "</li></ul>"
        "<h2></h2>"
    )
    minute = parser.convert(text)
    assert minute["meeting"]["name"] == "令和6年第1回定例会 代表質問"
    assert minute["topics"][0]["speeches"][1]["name"] == "質問者"
    assert minute["QAs"][0][1][0]["name"] == "質問者"
    assert minute["QAs"][0][1][1]["name"] == "答弁者"
