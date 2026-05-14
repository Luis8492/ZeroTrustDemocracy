import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.municipal_modules.sample import SampleParser, SampleFetcher


SAMPLE = """
[meeting]
date=2026年1月15日
name=サンプル区議会 第1回定例会

[topic]議題1: 防災対策について

◆山田太郎 委員:大規模災害への備えについて伺います。
◎佐藤花子 区長:備蓄計画を見直し中です。
◆山田太郎 委員:避難所の数は十分でしょうか。
◎佐藤花子 区長:今年度中に5施設増設します。

[topic]議題2: 子育て支援について

◆鈴木一郎 委員:保育園の待機児童について教えてください。
◎佐藤花子 区長:今年度中にゼロを目指しています。
"""


def test_sample_parser_extracts_meeting_meta():
    minute = SampleParser().convert(SAMPLE)
    assert minute["meeting"]["date"] == "2026年1月15日"
    assert minute["meeting"]["name"] == "サンプル区議会 第1回定例会"
    assert set(minute["meeting"]["participants"]) >= {"山田太郎", "佐藤花子", "鈴木一郎"}


def test_sample_parser_splits_topics_and_qa_sequences():
    minute = SampleParser().convert(SAMPLE)
    assert len(minute["topics"]) == 2
    assert len(minute["QAs"]) == 2

    topic1_qas = minute["QAs"][0]
    # [intro, qa_seq1, qa_seq2]: intro is empty, two ◆ → two qa sequences
    assert topic1_qas[0] == []
    assert len(topic1_qas) == 3
    assert all(seq[0]["mark"] == "◆" for seq in topic1_qas[1:])
    assert topic1_qas[1][0]["name"] == "山田太郎"
    assert topic1_qas[1][1]["mark"] == "◎"

    topic2_qas = minute["QAs"][1]
    assert len(topic2_qas) == 2  # intro + 1 qa
    assert topic2_qas[1][0]["name"] == "鈴木一郎"


def test_sample_fetcher_registered_for_plugin_contract():
    # Sanity check: PARSERS / FETCHERS are wired so the analyzer / fetch CLI
    # picks the sample plugin up automatically.
    from app.municipal_modules.sample import PARSERS, FETCHERS

    assert PARSERS == {"SampleFetcher": SampleParser}
    assert FETCHERS == {"SampleFetcher": SampleFetcher}
