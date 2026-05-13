"""Parser implementation for Setagaya municipal meeting minutes."""

from __future__ import annotations

import re
import json
from typing import Any, Dict, List

from app.municipal_modules.base.base_minute_parser import BaseMinuteParser
from utils.logger import get_logger

logger = get_logger(__name__)


class SetagayaCommitteeParser(BaseMinuteParser):
    """Parser for Setagaya committee meeting minutes."""
    FETCHER_NAME = "SetagayaCommitteeFetcher"

    def extract_meeting_data(self, text: str) -> Dict[str, Any]:
        lines = text.splitlines()
        date = None
        meeting_name = None
        for line in lines:
            match = re.match(
                r"^\[\s*令和\s*(\d+)\s*年\s*(\d+)月\s*(.+?)－(\d+)月(\d+)日-(\d+)号",
                line,
            )
            if match:
                era_year = int(match.group(1))
                month = int(match.group(2))
                meeting_name = match.group(3).strip()
                western_year = 2018 + era_year  # 令和元年 = 2019年
                day_month = f"{match.group(4)}月{match.group(5)}日{match.group(6)}号"
                date = f"{western_year}年{day_month}"
                break
        if date is None or meeting_name is None:
            raise ValueError("会議名と日付の行が見つかりませんでした")

        participants: List[str] = []
        collecting = False
        for line in lines:
            stripped = line.strip()
            if not collecting and "出席委員" in stripped:
                collecting = True
                continue
            if collecting:
                if (
                    stripped.startswith("事務局職員")
                    or stripped.startswith("出席説明員")
                    or stripped.startswith("◇")
                ):
                    break
                name_part = re.sub(r"^[^\s　]+[\s　]+", "", stripped)
                participant_name = re.sub(r"[\s　]+", "", name_part)
                if participant_name:
                    participants.append(participant_name)

        return {"date": date, "name": meeting_name, "participants": participants}

    def extract_topic_section(self, text: str) -> List[str]:
        parts = re.split(r"^\s*━{10,}\s*$", text, flags=re.MULTILINE)
        if len(parts) <= 1:
            raise ValueError("トピックの区切りが見つかりませんでした")
        return [part.strip() for part in parts[1:]]

    def extract_speeches(self, topic_text: str) -> List[Dict[str, Any]]:
        lines = topic_text.splitlines()
        speeches: List[Dict[str, Any]] = []
        current_speech: Dict[str, Any] | None = None
        speech_id = 1
        speaker_pattern = re.compile(r"^([○◆◎])([^\s　]+)[　\s]+([^\s　]+)[　\s]+(.+)")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            match = speaker_pattern.match(line)
            if match:
                if current_speech:
                    speeches.append(current_speech)
                    speech_id += 1
                mark, name, role, comment = match.groups()
                current_speech = {
                    "id": speech_id,
                    "mark": mark,
                    "name": name,
                    "role": role,
                    "comment": comment,
                    "raw": line,
                }
            else:
                if current_speech:
                    current_speech["comment"] += "\n" + line
                    current_speech["raw"] += "\n" + line
        if current_speech:
            speeches.append(current_speech)
        return speeches

    def _get_topic_intro_and_body(self, topic: Dict[str, Any]):
        topic_intro = []
        topic_rest = []
        found_first_question = False
        for speech in topic["speeches"]:
            if not found_first_question and speech["mark"] == "◆":
                found_first_question = True
                topic_rest.append(speech)
            elif found_first_question:
                topic_rest.append(speech)
            else:
                topic_intro.append(speech)
        return topic_intro, topic_rest

    def _build_state_transition_log(
        self, topic_body: List[Dict[str, Any]], speech_index: int
    ) -> str:
        transition_log = ""
        for i in range(speech_index):
            transition_log += topic_body[i]["mark"]
        return transition_log

    # -- State machine for grouping speeches into QA sequences --------
    #
    # States:
    #   "start"          – waiting for a ◆ questioner to open a QA
    #   "qa"             – inside a QA between a questioner and respondents
    #   "party_comments" – consecutive ◆ speeches (会派意見表明)
    #   "chair_skip"     – skipping ○ chair speeches after an interrupted ◆
    #
    # The current questioner name is tracked in `qa_owner` (set when
    # entering "qa").  Transition logic depends on the current speech's
    # mark and — for "start" / "chair_skip" — on the *next* speech's mark
    # (one-token look-ahead).

    def _extract_topic_QAs(
        self, topic_body: List[Dict[str, Any]], file_name: str = ""
    ) -> List[List[Dict[str, Any]]]:
        """Split *topic_body* (speeches after the intro) into QA sequences."""
        QAs: List[List[Dict[str, Any]]] = []
        seq: List[Dict[str, Any]] = []
        state = "start"
        qa_owner = ""
        pos = 0

        def _peek_mark() -> str | None:
            return topic_body[pos + 1]["mark"] if pos + 1 < len(topic_body) else None

        def _flush() -> None:
            nonlocal seq
            if seq:
                QAs.append(seq)
                seq = []

        def _error(ctx: str) -> RuntimeError:
            marks = "".join(s["mark"] for s in topic_body[: pos + 1])
            logger.error(
                "[ERROR] 状態遷移エラー file=%s state=%s marks=%s",
                file_name, state, marks,
            )
            return RuntimeError(
                f"Unknown state transition ({state}>{ctx}) [{marks}]"
            )

        while pos < len(topic_body):
            speech = topic_body[pos]
            mark = speech["mark"]
            next_mark = _peek_mark()

            if state == "start":
                if mark != "◆":
                    raise _error(mark)
                _flush()
                seq = [speech]
                if next_mark == "◎":
                    state, qa_owner = "qa", speech["name"]
                elif next_mark == "◆":
                    state = "party_comments"
                elif next_mark == "○":
                    _flush()          # save the lone ◆ as its own sequence
                    state = "chair_skip"
                elif next_mark is None:
                    pass              # last speech — will be flushed after loop
                else:
                    raise _error(f"{mark}>{next_mark}")

            elif state == "qa":
                if mark == "◆" and speech["name"] != qa_owner:
                    # Different questioner → start a new QA
                    _flush()
                    seq = [speech]
                    qa_owner = speech["name"]
                else:
                    # Same questioner (◆), respondent (◎), or chair (○):
                    # all belong to the current QA sequence.
                    seq.append(speech)

            elif state == "party_comments":
                if mark == "◆":
                    _flush()
                    seq = [speech]
                else:
                    # Non-◆ ends the party-comment run
                    break

            elif state == "chair_skip":
                if mark != "◆":
                    pass              # skip ○/◎ chair / admin speeches
                else:
                    seq = [speech]
                    if next_mark == "◎":
                        state, qa_owner = "qa", speech["name"]
                    elif next_mark == "◆":
                        state = "party_comments"
                    elif next_mark is None:
                        pass
                    else:
                        # e.g. ◆→○ again — stay in chair_skip
                        _flush()
                        state = "chair_skip"

            else:
                raise _error(f"unknown state {state}")

            pos += 1

        _flush()
        return QAs

    def extract_QAs(self, minute: Dict[str, Any]) -> List[Any]:
        minute_QAs = []
        file_name = minute.get("file_name", "")
        for topic in minute["topics"]:
            intro, topic_body = self._get_topic_intro_and_body(topic)
            topic_QAs: List[List[Dict[str, Any]]] = [intro]
            topic_QAs.extend(self._extract_topic_QAs(topic_body, file_name))
            minute_QAs.append(topic_QAs)
        return minute_QAs

    def convert(self, text: str) -> Dict[str, Any]:
        """Convert raw minute text into structured data."""
        minute_json: Dict[str, Any] = {
            "meeting": self.extract_meeting_data(text),
            "topics": [],
        }
        for i, topic_section in enumerate(self.extract_topic_section(text), start=1):
            speeches = self.extract_speeches(topic_section)
            minute_json["topics"].append(
                {"topic_id": i, "raw": topic_section, "speeches": speeches}
            )
        minute_json["QAs"] = self.extract_QAs(minute_json)
        return minute_json
