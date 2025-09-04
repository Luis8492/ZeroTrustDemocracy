import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.municipal_modules.setagaya2.parsers.setagaya2_parser import Setagaya2Parser


def test_extract_questioner_section_splits_representative_questions():
    parser = Setagaya2Parser()
    text = (
        "<h1>令和6年第1回定例会 代表質問</h1>"
        "<h2><a>質問者A</a></h2><ul></ul>"
        "<h2><a>質問者B</a></h2><ul></ul>"
    )
    sections = parser.extract_questioner_section(text)
    assert [s["name"] for s in sections] == ["質問者A", "質問者B"]


def test_extract_questioner_section_splits_general_questions():
    parser = Setagaya2Parser()
    text = (
        "<h1>令和6年第1回定例会 一般質問</h1>"
        "<h2 id=\"p1\">質問者一覧</h2><table></table>"
        "<h3 class=\"active\"><a id=\"a1\">阿久津 皇（自民）</a></h3><ul></ul>"
        "<h3 class=\"active\"><a id=\"a2\">菊池 太郎（立民）</a></h3><ul></ul>"
    )
    sections = parser.extract_questioner_section(text)
    assert [s["name"] for s in sections] == ["阿久津 皇（自民）", "菊池 太郎（立民）"]


def test_extract_questioner_section_ignores_trailing_paragraph_representative():
    parser = Setagaya2Parser()
    text = (
        "<h1>令和6年第1回定例会 代表質問</h1>"
        "<h2><a>質問者A</a></h2><ul></ul>"
        "<p>備考</p>"
    )
    sections = parser.extract_questioner_section(text)
    assert len(sections) == 1
    assert sections[0]["section"].strip() == "<ul></ul>"


def test_extract_questioner_section_ignores_trailing_paragraph_general():
    parser = Setagaya2Parser()
    text = (
        "<h1>令和6年第1回定例会 一般質問</h1>"
        "<h2 id=\"p1\">質問者一覧</h2><table></table>"
        "<h3><a id=\"a1\">質問者A</a></h3><ul></ul>"
        "<p>備考</p>"
    )
    sections = parser.extract_questioner_section(text)
    assert len(sections) == 1
    assert sections[0]["section"].strip() == "<ul></ul>"


def test_extract_topic_section_returns_empty_when_no_topics():
    parser = Setagaya2Parser()
    parser.pattern = "Pattern1"
    sections = parser.extract_topic_section({"name": "A", "section": ""})
    assert sections == []


def test_extract_topic_section_parses_representative_questions():
    parser = Setagaya2Parser()
    parser.pattern = "Pattern1"
    text = (
        "<h1>令和6年第1回定例会 代表質問</h1>"
        "<h2><a>質問者</a></h2>"
        "<ul><li><strong>議題</strong><ul><li>Q</li><li>A</li></ul></li></ul>"
        "<h2></h2>"
    )
    q_sections = parser.extract_questioner_section(text)
    sections = parser.extract_topic_section(q_sections[0])
    assert sections == [
        {
            "name": "質問者",
            "section": "<li><strong>議題</strong><ul><li>Q</li><li>A</li></ul></li>",
        }
    ]


def test_extract_topic_section_parses_general_questions():
    parser = Setagaya2Parser()
    parser.pattern = "Pattern1"
    text = (
        "<h1>令和6年第1回定例会 一般質問</h1>"
        "<h2 id=\"p1\">質問者一覧</h2>"
        "<h3 class=\"active\"><a id=\"a1\">質問者</a></h3>"
        "<ul><li><strong>議題</strong><ul><li>Q</li><li>A</li></ul></li></ul>"
        "<h3></h3>"
    )
    q_sections = parser.extract_questioner_section(text)
    sections = parser.extract_topic_section(q_sections[0])
    assert sections == [
        {
            "name": "質問者",
            "section": "<li><strong>議題</strong><ul><li>Q</li><li>A</li></ul></li>",
        }
    ]


def test_extract_meeting_data_classifies_pattern():
    parser = Setagaya2Parser()
    text = "<ul><li><ul><li><strong>質問</strong></li></ul></li></ul>"
    meeting = parser.extract_meeting_data(text)
    assert parser.pattern == "Pattern1"
    assert "pattern" not in meeting
