import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.municipal_modules.setagaya2.parsers.setagaya2_parser import Setagaya2Parser
from app.minute_converter import convert_minute_txt_to_json

REP_FILE = Path(
    "app/raw_minutes/SetagayaRegularFetcher_https_www_city_setagaya_lg_jp_02030_21941_html.html"
)
GEN_FILE = Path(
    "app/raw_minutes/SetagayaRegularFetcher_https_www_city_setagaya_lg_jp_02030_21942_html.html"
)


def test_representative_minutes_parsing():
    parser = Setagaya2Parser()
    text = REP_FILE.read_text(encoding="utf-8")
    minute = convert_minute_txt_to_json(text, parser)

    assert len(minute["topics"]) == 33
    speeches = minute["topics"][0]["speeches"]
    assert speeches[0]["comment"] == "HPVワクチン接種助成の継続"
    assert speeches[1]["name"] == "自由民主党世田谷区議団 山口 ひろひさ"
    assert "HPVワクチン" in speeches[1]["comment"]
    assert speeches[2]["name"] == "保健所長"
    assert "接種機会を逃さぬ" in speeches[2]["comment"]

    qas = parser.extract_QAs(minute)
    assert len(qas) == 33
    assert qas[0][1][0][0]["name"] == "自由民主党世田谷区議団 山口 ひろひさ"
    assert qas[0][1][0][1]["name"] == "保健所長"


def test_general_minutes_parsing():
    parser = Setagaya2Parser()
    text = GEN_FILE.read_text(encoding="utf-8")
    minute = convert_minute_txt_to_json(text, parser)

    assert len(minute["topics"]) == 90
    speeches = minute["topics"][0]["speeches"]
    assert speeches[0]["comment"] == "違反広告物への対策の強化"
    assert speeches[1]["name"] == "佐藤 正幸（自民）"
    assert "広告物除去協力員" in speeches[1]["comment"]
    assert speeches[2]["name"] == ""
    assert "周知できるよう工夫する" in speeches[2]["comment"]

    qas = parser.extract_QAs(minute)
    assert len(qas) == 90
    assert qas[0][1][0][0]["name"] == "佐藤 正幸（自民）"
    assert qas[0][1][0][1]["name"] == ""
