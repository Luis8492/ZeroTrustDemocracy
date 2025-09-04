import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.municipal_modules.setagaya2.parsers.setagaya2_parser import Setagaya2Parser
from app.minute_converter import convert_minute_txt_to_json


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


def test_extract_topic_section_expands_nested_li():
    parser = Setagaya2Parser()
    text = Path("app/municipal_modules/setagaya2/samples/nested_li.html").read_text(
        encoding="utf-8"
    )
    sections = parser.extract_topic_section(text)
    assert sections == [
        "質問者\n<strong>議題</strong><br><strong>質問</strong>質問文<br><strong>区長</strong>回答文"
    ]
    speeches = parser.extract_speeches(sections[0])
    assert speeches[0]["comment"] == "議題"
    assert speeches[1]["name"] == "質問者"
    assert speeches[1]["comment"] == "質問文"
    assert speeches[2]["name"] == "区長"
    assert speeches[2]["comment"] == "回答文"


def test_extract_speeches_single_strong_contains_question():
    parser = Setagaya2Parser()
    text = Path(
        "app/municipal_modules/setagaya2/samples/single_strong_in_li.html"
    ).read_text(encoding="utf-8")
    section = parser.extract_topic_section(text)[0]
    speeches = parser.extract_speeches(section)
    assert speeches[0]["comment"] == "議題"
    assert speeches[1]["name"] == "質問者"
    assert speeches[1]["comment"] == "質問内容"
    assert speeches[2]["name"] == "区長"
    assert speeches[2]["comment"] == "回答内容"


def test_extract_speeches_separate_strongs():
    parser = Setagaya2Parser()
    text = Path(
        "app/municipal_modules/setagaya2/samples/separate_strongs.html"
    ).read_text(encoding="utf-8")
    section = parser.extract_topic_section(text)[0]
    speeches = parser.extract_speeches(section)
    assert speeches[1]["comment"] == "質問内容"
    assert speeches[2]["name"] == "区長"
    assert speeches[2]["comment"] == "回答内容"


def test_extract_speeches_normalizes_double_strong():
    parser = Setagaya2Parser()
    text = Path(
        "app/municipal_modules/setagaya2/samples/double_strong.html"
    ).read_text(encoding="utf-8")
    section = parser.extract_topic_section(text)[0]
    speeches = parser.extract_speeches(section)
    assert speeches[1]["comment"] == "質問内容"
    assert speeches[2]["name"] == "区長"
    assert speeches[2]["comment"] == "回答内容"


def test_extract_QAs_representative_sample():
    parser = Setagaya2Parser()
    text = Path(
        "app/municipal_modules/setagaya2/samples/separate_strongs.html"
    ).read_text(encoding="utf-8")
    minute = convert_minute_txt_to_json(text, parser)
    qas = parser.extract_QAs(minute)
    total_pairs = sum(len(pairs) for _, pairs in qas)
    assert total_pairs == 1
    assert qas[0][1][0][0]["name"] == "質問者"
    assert qas[0][1][0][1]["name"] == "区長"


def test_extract_QAs_general_sample():
    parser = Setagaya2Parser()
    text = Path("app/municipal_modules/setagaya2/samples/qa_general.html").read_text(
        encoding="utf-8"
    )
    minute = convert_minute_txt_to_json(text, parser)
    qas = parser.extract_QAs(minute)
    total_pairs = sum(len(pairs) for _, pairs in qas)
    assert total_pairs == 2
    assert qas[0][1][0][0]["name"] == "質問者A"
    assert qas[1][1][0][0]["name"] == "質問者B"
