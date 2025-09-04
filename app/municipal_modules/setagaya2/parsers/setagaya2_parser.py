"""Parser implementation for Setagaya regular session meeting minutes."""

from __future__ import annotations

import html
import re
from typing import Any, Dict, List

from app.municipal_modules.base.base_minute_parser import BaseMinuteParser
from app.municipal_modules.setagaya2.dev.pattern_classifier import classify_pattern


class Setagaya2Parser(BaseMinuteParser):
    """Parser for Setagaya regular session meeting minutes."""

    def __init__(self) -> None:  # pragma: no cover - simple init
        self.pattern: str = "Unknown"

    def _clean_html(self, text: str) -> str:
        text = re.sub(r"<br\s*/?>", "\n", text)
        text = re.sub(r"<.*?>", "", text)
        text = text.replace("&nbsp;", " ")
        return html.unescape(text).strip()

    def extract_meeting_data(self, text: str) -> Dict[str, Any]:
        """Extract meeting metadata such as date and name."""
        self.pattern = classify_pattern(text)
        name_match = re.search(r"<h1>(.*?)</h1>", text, re.S)
        name = self._clean_html(name_match.group(1)) if name_match else ""

        date = ""
        backlink_match = re.search(
            r'<div id="tmp_lnavi_ttl">\s*<p><a[^>]*>(.*?)</a>', text, re.S
        )
        if backlink_match:
            link_text = self._clean_html(backlink_match.group(1))
            m = re.search(r"(令和\d+年).*（(.+?)）", link_text)
            if m:
                date = f"{m.group(1)}{m.group(2)}"
        return {"date": date, "name": name}

    def extract_topic_section(self, text: str) -> List[str]:
        """Split the minutes text into topic sections."""
        sections: List[str] = []
        pattern = re.compile(
            r"<h[23][^>]*><a[^>]*>(.*?)</a></h[23]>\s*<ul>([\S\s]*?)</ul>\s*<h.",
            re.S,
        )
        for questioner, ul_content in pattern.findall(text):
            for li in re.findall(r"<li>(.*?)</li>", ul_content, re.S):
                sections.append(questioner + "\n" + li)
        return sections

    def extract_speeches(self, topic_text: str) -> List[Dict[str, Any]]:
        """Extract speech entries from a topic section."""
        speeches: List[Dict[str, Any]] = []

        if self.pattern == "Pattern1":
            pass
        elif self.pattern == "Pattern2":
            pass
        elif self.pattern == "Pattern3":
            pass

        lines = topic_text.split("\n", 1)
        questioner = self._clean_html(lines[0]) if lines else ""
        li_html = lines[1] if len(lines) > 1 else ""

        speech_id = 1

        topic_match = re.match(r"<strong>(.*?)</strong><br>", li_html, re.S)
        if not topic_match:
            return speeches
        topic_html = topic_match.group(0)
        topic_title = self._clean_html(topic_match.group(1))
        speeches.append(
            {
                "id": speech_id,
                "mark": "○",
                "name": "",
                "role": "",
                "comment": topic_title,
                "raw": topic_html,
            }
        )
        speech_id += 1

        remaining = li_html[topic_match.end() :]

        q_match = re.search(
            r"<strong>質問(?:&nbsp;)?</strong>\s*(.*?)<br>", remaining, re.S
        )
        if q_match:
            question_html = q_match.group(0)
            comment = self._clean_html(q_match.group(1))
            speeches.append(
                {
                    "id": speech_id,
                    "mark": "◆",
                    "name": questioner,
                    "role": "質問",
                    "comment": comment,
                    "raw": question_html,
                }
            )
            speech_id += 1
            remaining = remaining[q_match.end() :]

        a_match = re.search(
            r"<strong>([^<]*?)(?:&nbsp;)?</strong>\s*(.*)", remaining, re.S
        )

        if a_match:
            strong_text = self._clean_html(a_match.group(1))
            after_strong = a_match.group(2)
            parts = re.split(r"<br>\s*", after_strong, 1)
            if strong_text == "答弁":
                speaker_name = self._clean_html(parts[0]) if parts else ""
                comment_html = parts[1] if len(parts) > 1 else ""
            else:
                speaker_name = strong_text
                comment_html = parts[1] if len(parts) > 1 else parts[0]
            answer_html = a_match.group(0)
            comment = self._clean_html(comment_html)
            speeches.append(
                {
                    "id": speech_id,
                    "mark": "○",
                    "name": speaker_name,
                    "role": speaker_name,
                    "comment": comment,
                    "raw": answer_html,
                }
            )
        return speeches

    def extract_QAs(self, minute: Dict[str, Any]) -> List[Any]:
        """Convert parsed minute data into QA sequences."""
        minute_QAs: List[Any] = []
        for topic in minute.get("topics", []):
            speeches = topic.get("speeches", [])
            if len(speeches) < 2:
                continue
            intro = [speeches[0]]
            qa = speeches[1:]
            minute_QAs.append([intro, qa])
        return minute_QAs
