"""Parser implementation for Tokyo Metropolitan Assembly net report minutes."""

from __future__ import annotations

import html
import re
from typing import Any, Dict, List, Tuple

from app.municipal_modules.base.base_minute_parser import BaseMinuteParser


class TokyoParser(BaseMinuteParser):
    """Parser for Tokyo Metropolitan Assembly net report pages."""

    FETCHER_NAME = "tokyo_net_report"

    def _clean_html(self, fragment: str) -> str:
        """Return text content stripped of HTML tags."""
        text = re.sub(r"<br\s*/?>", "\n", fragment)
        text = re.sub(r"<.*?>", "", text)
        text = html.unescape(text)
        return text.strip()

    def _extract_questioner(self, text: str) -> Tuple[str, str, str]:
        side_match = re.search(r"<div class=\"side-menu\">(.*?)</div>\s*<!--//side-menu -->", text, re.S)
        if not side_match:
            return "", "", ""
        side_html = side_match.group(1)
        items = re.findall(r"<li>(.*?)</li>", side_html, re.S)
        for item in items:
            cleaned = self._clean_html(item)
            if not cleaned:
                continue
            display = cleaned
            name = display
            party = ""
            name_party_match = re.match(r"(?P<name>[^（]+)（(?P<party>.+)）", display)
            if name_party_match:
                name = name_party_match.group("name").strip()
                party = name_party_match.group("party").strip()
            return display, name, party
        return "", "", ""

    def get_meeting_data(self, text: str) -> Dict[str, Any]:
        title_match = re.search(r"<title>(.*?)</title>", text, re.S)
        meeting_name = ""
        if title_match:
            title_text = self._clean_html(title_match.group(1))
            if "｜" in title_text:
                title_text = title_text.split("｜", 1)[0]
            meeting_name = re.sub(r"（[^（）]*）$", "", title_text).strip()
        display, name, party = self._extract_questioner(text)
        participants: List[str] = [name] if name else []
        meeting: Dict[str, Any] = {
            "name": meeting_name,
            "date": "",
            "participants": participants,
        }
        if display:
            meeting["questioner_display"] = display
        if name:
            meeting["questioner_name"] = name
        if party:
            meeting["questioner_party"] = party
        return meeting

    def _extract_topic_sections(self, text: str) -> List[Tuple[str, str]]:
        main_match = re.search(r"<div class=\"main\">(.*?)</div>\s*<!--//main -->", text, re.S)
        if not main_match:
            return []
        main_html = main_match.group(1)
        topic_pattern = re.compile(r"<h4[^>]*>(?P<title>.*?)</h4>(?P<body>.*?)(?=<h4[^>]*>|$)", re.S)
        sections: List[Tuple[str, str]] = []
        for match in topic_pattern.finditer(main_html):
            title = self._clean_html(match.group("title"))
            body = match.group("body")
            if title:
                sections.append((title, body))
        return sections

    def _strip_question_label(self, html_fragment: str) -> str:
        fragment = re.sub(r"<em[^>]*>質問\s*\d+</em>", "", html_fragment, count=1, flags=re.S)
        fragment = re.sub(r"^(?:\s*<br\s*/?>)+", "", fragment, flags=re.S)
        return self._clean_html(fragment)

    def _strip_answer_label(self, html_fragment: str) -> Tuple[str, str]:
        fragment = re.sub(r"<em[^>]*>答弁\s*\d+</em>", "", html_fragment, count=1, flags=re.S)
        speaker_match = re.search(r"<strong>(.*?)</strong>", fragment, re.S)
        speaker = self._clean_html(speaker_match.group(1)) if speaker_match else "答弁者"
        fragment = re.sub(r"<strong>.*?</strong>", "", fragment, count=1, flags=re.S)
        fragment = re.sub(r"^(?:\s*<br\s*/?>)+", "", fragment, flags=re.S)
        return speaker, self._clean_html(fragment)

    def _parse_topic(self, title: str, body: str, questioner_name: str) -> Tuple[Dict[str, Any], List[List[Dict[str, Any]]]]:
        speeches: List[Dict[str, Any]] = []
        qa_pairs: List[List[Dict[str, Any]]] = []
        speech_id = 1

        intro = {
            "id": speech_id,
            "mark": "○",
            "name": "議題",
            "role": "-",
            "comment": title,
            "raw": title,
        }
        speeches.append(intro)
        speech_id += 1

        paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", body, re.S)
        state: str | None = None
        question_role = ""
        question_parts: List[str] = []
        answer_role = ""
        answer_parts: List[str] = []
        answer_speaker = ""
        last_question_speech: Dict[str, Any] | None = None

        def finalize_question() -> Dict[str, Any] | None:
            nonlocal question_parts, question_role, speech_id, last_question_speech, state
            if not question_role and not question_parts:
                return None
            comment = "\n\n".join(part for part in question_parts if part).strip()
            speech = {
                "id": speech_id,
                "mark": "◆",
                "name": questioner_name or "質問者",
                "role": question_role or "質問",
                "comment": comment,
                "raw": comment,
            }
            speeches.append(speech)
            speech_id += 1
            last_question_speech = speech
            question_parts = []
            question_role = ""
            state = None
            return speech

        def finalize_answer() -> Dict[str, Any] | None:
            nonlocal answer_parts, answer_role, answer_speaker, speech_id, last_question_speech, state
            if not answer_role and not answer_parts:
                return None
            comment = "\n\n".join(part for part in answer_parts if part).strip()
            speech = {
                "id": speech_id,
                "mark": "◎",
                "name": answer_speaker or "答弁者",
                "role": answer_role or "答弁",
                "comment": comment,
                "raw": comment,
            }
            speeches.append(speech)
            speech_id += 1
            if last_question_speech is not None:
                qa_pairs.append([last_question_speech, speech])
                last_question_speech = None
            answer_parts = []
            answer_role = ""
            answer_speaker = ""
            state = None
            return speech

        for paragraph_html in paragraphs:
            if "pull-right" in paragraph_html:
                continue
            if not paragraph_html.strip():
                continue

            question_match = re.search(r"<em[^>]*>質問\s*(\d+)</em>", paragraph_html)
            answer_match = re.search(r"<em[^>]*>答弁\s*(\d+)</em>", paragraph_html)

            if question_match:
                if answer_parts:
                    finalize_answer()
                question_role = f"質問{question_match.group(1)}"
                question_parts = []
                stripped = self._strip_question_label(paragraph_html)
                if stripped:
                    question_parts.append(stripped)
                state = "question"
                continue

            if answer_match:
                finalize_question()
                if answer_parts:
                    finalize_answer()
                answer_role = f"答弁{answer_match.group(1)}"
                answer_speaker, stripped = self._strip_answer_label(paragraph_html)
                answer_parts = []
                if stripped:
                    answer_parts.append(stripped)
                state = "answer"
                continue

            cleaned = self._clean_html(paragraph_html)
            if not cleaned:
                continue
            if state == "question":
                question_parts.append(cleaned)
            elif state == "answer":
                answer_parts.append(cleaned)

        if state == "question" and question_parts:
            finalize_question()
        if answer_parts:
            finalize_answer()

        topic: Dict[str, Any] = {
            "name": title,
            "raw": body.strip(),
            "speeches": speeches,
        }
        qa_sequences: List[List[Dict[str, Any]]] = []
        if speeches:
            qa_sequences.append([speeches[0]])
        qa_sequences.extend(qa_pairs)
        return topic, qa_sequences

    def convert(self, text: str) -> Dict[str, Any]:
        meeting = self.get_meeting_data(text)
        questioner = meeting.get("questioner_name") or meeting.get("questioner_display", "")
        minute_json: Dict[str, Any] = {"meeting": meeting, "topics": []}
        qa_topics: List[List[List[Dict[str, Any]]]] = []
        for idx, (title, body) in enumerate(self._extract_topic_sections(text), start=1):
            topic, qa_sequences = self._parse_topic(title, body, questioner)
            topic["topic_id"] = idx
            minute_json["topics"].append(topic)
            if qa_sequences:
                qa_topics.append(qa_sequences)
        minute_json["QAs"] = qa_topics
        return minute_json
