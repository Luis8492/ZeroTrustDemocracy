"""Parser for the synthetic 'sample' minute format.

The format is intentionally simple so the reference plugin is readable as
documentation. A real municipality parser would extract the same structure
from messier HTML / CP932 text.

Format example::

    [meeting]
    date=2026年1月15日
    name=サンプル区議会 第1回定例会

    [topic]議題1: 防災対策について

    ◆山田太郎 委員:大規模災害への備えについて伺います。
    ◎佐藤花子 区長:備蓄計画を見直し中です。
    ◆山田太郎 委員:避難所の数は十分でしょうか。
    ◎佐藤花子 区長:今年度中に5施設増設します。

Marks follow the project convention: ``◆`` = questioner, ``◎`` = respondent,
``○`` = chair. Each ``◆`` boundary starts a new QA sequence inside the topic.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from app.municipal_modules.base.base_minute_parser import BaseMinuteParser


_SPEECH_RE = re.compile(r"^(?P<mark>[◆◎○])(?P<who>[^:：]+)[:：](?P<comment>.*)$")


class SampleParser(BaseMinuteParser):
    FETCHER_NAME = "SampleFetcher"

    def convert(self, text: str) -> Dict[str, Any]:
        meeting: Dict[str, str] = {}
        topics: List[Dict[str, Any]] = []
        qas: List[List[List[Dict[str, Any]]]] = []

        section = None
        current_topic: Dict[str, Any] | None = None
        current_speeches: List[Dict[str, Any]] = []

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith("[meeting]"):
                section = "meeting"
                continue
            if line.startswith("[topic]"):
                if current_topic is not None:
                    current_topic["speeches"] = current_speeches
                    topics.append(current_topic)
                    qas.append(_group_into_qas(current_speeches))
                section = "topic"
                current_topic = {
                    "topic_id": len(topics) + 1,
                    "raw": line[len("[topic]"):].strip(),
                    "speeches": [],
                }
                current_speeches = []
                continue

            if section == "meeting":
                if "=" in line:
                    key, _, value = line.partition("=")
                    meeting[key.strip()] = value.strip()
                continue

            if section == "topic":
                speech = _parse_speech(line, index=len(current_speeches) + 1)
                if speech is not None:
                    current_speeches.append(speech)

        if current_topic is not None:
            current_topic["speeches"] = current_speeches
            topics.append(current_topic)
            qas.append(_group_into_qas(current_speeches))

        return {
            "meeting": {
                "date": meeting.get("date", ""),
                "name": meeting.get("name", ""),
                "participants": _collect_participants(topics),
            },
            "topics": topics,
            "QAs": qas,
        }


def _parse_speech(line: str, *, index: int) -> Dict[str, Any] | None:
    match = _SPEECH_RE.match(line)
    if not match:
        return None
    who = match.group("who").strip()
    name, _, role = who.partition(" ")
    return {
        "id": index,
        "mark": match.group("mark"),
        "name": name.strip(),
        "role": role.strip(),
        "comment": match.group("comment").strip(),
        "raw": line,
    }


def _group_into_qas(speeches: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """Group speeches into [intro, qa_seq, qa_seq, ...].

    Every ``◆`` (questioner) opens a new QA sequence; subsequent ``◎`` / ``○``
    speeches attach to it. Leading non-``◆`` speeches form the intro.
    """
    intro: List[Dict[str, Any]] = []
    sequences: List[List[Dict[str, Any]]] = []
    current: List[Dict[str, Any]] | None = None

    for speech in speeches:
        if speech["mark"] == "◆":
            if current is not None:
                sequences.append(current)
            current = [speech]
        else:
            if current is None:
                intro.append(speech)
            else:
                current.append(speech)

    if current is not None:
        sequences.append(current)

    return [intro] + sequences


def _collect_participants(topics: List[Dict[str, Any]]) -> List[str]:
    seen: Dict[str, None] = {}
    for topic in topics:
        for speech in topic.get("speeches", []):
            name = speech.get("name")
            if name and name not in seen:
                seen[name] = None
    return list(seen)
