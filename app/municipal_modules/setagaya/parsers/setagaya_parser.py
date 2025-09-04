"""Parser implementation for Setagaya municipal meeting minutes."""

from __future__ import annotations

import re
import json
from typing import Any, Dict, List

from app.municipal_modules.base.base_minute_parser import BaseMinuteParser
from utils.logger import get_logger

logger = get_logger(__name__)


class SetagayaParser(BaseMinuteParser):
    """Parser for Setagaya municipal meeting minutes."""

    def extract_meeting_data(self, text: str) -> Dict[str, Any]:
        lines = text.splitlines()
        for line in lines:
            match = re.match(r"^\[\s*令和\s*(\d+)\s*年\s*(\d+)月\s*(.+?)－(\d+)月(\d+)日-(\d+)号", line)
            if match:
                era_year = int(match.group(1))
                month = int(match.group(2))
                name = match.group(3).strip()
                western_year = 2018 + era_year  # 令和元年 = 2019年
                day_month = f"{match.group(4)}月{match.group(5)}日{match.group(6)}号"
                date = f"{western_year}年{day_month}"
                return {"date": date, "name": name}
        raise ValueError("会議名と日付の行が見つかりませんでした")

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

    def extract_QAs(self, minute: Dict[str, Any]) -> List[Any]:
        minute_QAs = []
        for topic in minute["topics"]:
            QAs = []
            intro, topic_body = self._get_topic_intro_and_body(topic)
            QAs.append(intro)
            QA_sequence = []
            state = "start"
            for speech_index in range(len(topic_body)):
                if state == "start":
                    if topic_body[speech_index]["mark"] != "◆":
                        transition_log = self._build_state_transition_log(topic_body, speech_index)
                        raise RuntimeError(
                            "Start時にmarkが◆でないことは想定されていません.[" + transition_log + "]"
                        )
                    elif topic_body[speech_index + 1]["mark"] == "◎":
                        new_state = "QA" + topic_body[speech_index]["name"]
                        QAs.append(QA_sequence)
                        QA_sequence = [topic_body[speech_index]]
                        state = new_state
                    elif topic_body[speech_index + 1]["mark"] == "◆":
                        new_state = "party_comments"
                        QAs.append(QA_sequence)
                        QA_sequence = [topic_body[speech_index]]
                        state = new_state
                    else:
                        transition_log = self._build_state_transition_log(topic_body, speech_index + 1)
                        message = f"[ERROR] 状態遷移エラー"
                        logger.error(message)
                        message = f"[ERROR] 元議事録ファイル: {minute.get('file_name', '')}"
                        logger.error(message)
                        message = (
                            f"[ERROR] 当該シークエンスの最初: {json.dumps(topic_body[speech_index], ensure_ascii=False)}"
                        )
                        logger.error(message)
                        logger.error("")
                        raise RuntimeError(
                            "Unknown state transition.(" + state + ">?)[" + transition_log + "]"
                        )
                elif state[:2] == "QA":
                    if topic_body[speech_index]["mark"] != "○":
                        if topic_body[speech_index]["mark"] == "◆":
                            if topic_body[speech_index]["name"] != state[2:]:
                                new_state = "QA" + topic_body[speech_index]["name"]
                                QAs.append(QA_sequence)
                                QA_sequence = [topic_body[speech_index]]
                                state = new_state
                            else:
                                QA_sequence.append(topic_body[speech_index])
                        else:
                            QA_sequence.append(topic_body[speech_index])
                    else:
                        for i in range(speech_index, len(topic_body)):
                            if topic_body[i]["mark"] == "◆":
                                if i + 1 < len(topic_body):
                                    if topic_body[i + 1]["mark"] == "◆":
                                        new_state = "party_comments"
                                        QAs.append(QA_sequence)
                                        QAs.append([topic_body[i]])
                                        QAs.append([topic_body[i + 1]])
                                        QA_sequence = []
                                        speech_index = i + 1 # これなに?
                                        state = new_state
                                        break
                                    elif topic_body[i + 1]["mark"] == "◎":
                                        if topic_body[i]["name"] == state[2:]:
                                            QA_sequence.append(topic_body[i])
                                            QA_sequence.append(topic_body[i + 1])
                                            speech_index = i + 1 # これなに?
                                            break
                                        else:
                                            new_state = "QA" + topic_body[i]["name"]
                                            QAs.append(QA_sequence)
                                            QA_sequence = [topic_body[i], topic_body[i + 1]]
                                            speech_index = i + 1 # これなに?
                                            state = new_state
                                            break
                                    else:
                                        transition_log = self._build_state_transition_log(topic_body, i + 1)
                                        message = f"[ERROR] 元議事録ファイル: {minute.get('file_name', '')}"
                                        logger.error(message)
                                        message = (
                                            f"[ERROR] 当該シークエンスの最初: {json.dumps(topic_body[speech_index], ensure_ascii=False)}"
                                        )
                                        logger.error(message)
                                        logger.error("")
                                        raise RuntimeError(
                                            "Unknown state transition.(" + state + ">?)[" + transition_log + "]"
                                        )
                                else:
                                    break
                            else:
                                QA_sequence.append(topic_body[i])
                elif state == "party_comments":
                    if topic_body[speech_index]["mark"] == "◆":
                        QAs.append(QA_sequence)
                        QA_sequence = [topic_body[speech_index]]
                    else:
                        break
                else:
                    transition_log = self._build_state_transition_log(topic_body, speech_index + 1)
                    raise RuntimeError("Unknown state. (" + state + ")[" + transition_log + "]")
            QAs.append(QA_sequence)
            minute_QAs.append(QAs)
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
