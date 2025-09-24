from pathlib import Path

from app.municipal_modules.Tokyo.parsers.tokyo_parser import TokyoParser


def load_sample() -> str:
    sample_path = Path("app/municipal_modules/Tokyo/samples/01.html")
    return sample_path.read_text(encoding="utf-8")


def test_tokyo_parser_extracts_topics_and_speeches():
    parser = TokyoParser()
    minute = parser.convert(load_sample())

    assert minute["meeting"]["name"] == "令和7年第2回定例会 代表質問・一般質問"
    assert minute["meeting"]["questioner_name"] == "川松 真一朗"
    assert minute["meeting"]["questioner_party"] == "自民党"

    assert len(minute["topics"]) == 20

    first_topic = minute["topics"][0]
    assert first_topic["topic_id"] == 1
    assert first_topic["name"] == "国連の誘致を国に呼びかけたこと"

    speeches = first_topic["speeches"]
    assert [speech["mark"] for speech in speeches] == ["○", "◆", "◎"]
    assert speeches[1]["name"] == minute["meeting"]["questioner_name"]
    assert "知事" in speeches[2]["name"]
    assert "国連の誘致" in speeches[2]["comment"]

    qas = minute["QAs"][0]
    assert qas[0][0]["mark"] == "○"
    assert qas[1][0]["mark"] == "◆"
    assert qas[1][1]["mark"] == "◎"
