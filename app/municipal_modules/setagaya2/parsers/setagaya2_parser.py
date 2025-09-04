"""Parser implementation for Setagaya regular session meeting minutes."""

from __future__ import annotations

import html
import re
from typing import Any, Dict, List

from app.municipal_modules.base.base_minute_parser import BaseMinuteParser


class Setagaya2Parser(BaseMinuteParser):
    """Parser for Setagaya regular session meeting minutes."""

    def _clean_html(self, text: str) -> str:
        text = re.sub(r"<br\s*/?>", "\n", text)
        text = re.sub(r"<.*?>", "", text)
        text = text.replace("&nbsp;", " ")
        return html.unescape(text).strip()

    def extract_meeting_data(self, text: str) -> Dict[str, Any]:
        """Extract meeting metadata such as date and name."""
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
            r"<h[23][^>]*><a[^>]*>(.*?)</a></h[23]>\s*<ul>([\s\S]*?)</ul>(?=\s*<h[23]|$)",
            re.S,
        )
        for questioner, ul_content in pattern.findall(text):
            if re.search(r"<ul>\s*<li>", ul_content):
                inner_lis = re.findall(r"<ul>\s*<li>([\s\S]*?)</li>\s*</ul>", ul_content, re.S)
                for inner in inner_lis:
                    sections.append(questioner + "\n" + inner)
            else:
                for li in re.findall(r"<li>([\s\S]*?)</li>", ul_content, re.S):
                    sections.append(questioner + "\n" + li)
        return sections

    def extract_speeches(self, topic_text: str) -> List[Dict[str, Any]]:
        """Extract speech entries from a topic section."""
        speeches: List[Dict[str, Any]] = []

        lines = topic_text.split("\n", 1)
        questioner = self._clean_html(lines[0]) if lines else ""
        li_html = lines[1] if len(lines) > 1 else ""

        li_html = li_html.replace("&nbsp;", " ")
        li_html = li_html.replace("<strong><strong>", "<strong>")
        li_html = li_html.replace("</strong></strong>", "</strong>")

        speech_id = 1

        topic_match = re.match(r"<strong>(.*?)</strong>(.*)", li_html, re.S)
        if not topic_match:
            return speeches

        topic_inside = topic_match.group(1)
        remaining = topic_match.group(2)

        parts = re.split(r"<br\s*/?>", topic_inside)
        topic_title = self._clean_html(parts[0]) if parts else ""
        speeches.append(
            {
                "id": speech_id,
                "mark": "○",
                "name": "",
                "role": "",
                "comment": topic_title,
                "raw": "<strong>" + topic_inside + "</strong>",
            }
        )
        speech_id += 1

        for extra in parts[1:]:
            remaining = f"<strong>{extra}</strong>" + remaining

        strong_pattern = re.compile(r"<strong>(.*?)</strong>(.*?)(?=<strong>|$)", re.S)

        for match in strong_pattern.finditer(remaining):
            strong_text = self._clean_html(match.group(1))
            body_html = re.sub(r"^\s*<br\s*/?>", "", match.group(2))

            if strong_text.startswith("質問"):
                comment = self._clean_html(body_html)
                speeches.append(
                    {
                        "id": speech_id,
                        "mark": "◆",
                        "name": questioner,
                        "role": "質問",
                        "comment": comment,
                        "raw": match.group(0),
                    }
                )
                speech_id += 1
            else:
                if strong_text == "答弁":
                    parts = re.split(r"<br\s*/?>", body_html, 1)
                    if len(parts) == 1:
                        speaker_name = ""
                        comment_html = parts[0]
                    else:
                        speaker_name = self._clean_html(parts[0])
                        comment_html = parts[1]
                else:
                    speaker_name = strong_text
                    comment_html = body_html
                comment = self._clean_html(comment_html)
                speeches.append(
                    {
                        "id": speech_id,
                        "mark": "○",
                        "name": speaker_name,
                        "role": speaker_name,
                        "comment": comment,
                        "raw": match.group(0),
                    }
                )
                speech_id += 1
        return speeches

    def extract_QAs(self, minute: Dict[str, Any]) -> List[Any]:
        """Convert parsed minute data into QA sequences."""
        minute_QAs: List[Any] = []
        for topic in minute.get("topics", []):
            speeches = topic.get("speeches", [])
            if not speeches:
                continue
            intro = [speeches[0]]
            pairs: List[List[Dict[str, Any]]] = []
            current_q: Dict[str, Any] | None = None
            for speech in speeches[1:]:
                if speech.get("role") == "質問":
                    if current_q is not None:
                        pairs.append([current_q, {"id": -1, "mark": "", "name": "", "role": "", "comment": "", "raw": ""}])
                    current_q = speech
                else:
                    if current_q is not None:
                        pairs.append([current_q, speech])
                        current_q = None
            if current_q is not None:
                pairs.append([current_q, {"id": -1, "mark": "", "name": "", "role": "", "comment": "", "raw": ""}])
            if pairs:
                minute_QAs.append([intro, pairs])
        return minute_QAs
