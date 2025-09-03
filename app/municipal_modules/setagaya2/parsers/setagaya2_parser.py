"""Parser implementation for Setagaya regular session meeting minutes."""

from __future__ import annotations

import html
import re
from typing import Any, Dict, List

from app.municipal_modules.base.base_minute_parser import BaseMinuteParser
from utils.logger import get_logger

logger = get_logger(__name__)


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
            m = re.search(r"令和(\d+)年.*（(.+?)）", link_text)
            if m:
                era_year = int(m.group(1))
                western_year = 2018 + era_year
                date = f"{western_year}年{m.group(2)}"
        return {"date": date, "name": name}

    def extract_topic_section(self, text: str) -> List[str]:
        """Split the minutes text into topic sections."""
        sections: List[str] = []
        pattern = re.compile(
            r"<h3><a[^>]*>(.*?)</a></h3>\s*<ul>(.*?)</ul>", re.S
        )
        for questioner, ul_content in pattern.findall(text):
            for li in re.findall(r"<li>(.*?)</li>", ul_content, re.S):
                sections.append(questioner + "\n" + li)
        return sections

    def extract_speeches(self, topic_text: str) -> List[Dict[str, Any]]:
        """Extract speech entries from a topic section."""
        lines = topic_text.split("\n", 1)
        questioner = self._clean_html(lines[0]) if lines else ""
        li_html = lines[1] if len(lines) > 1 else ""

        speeches: List[Dict[str, Any]] = []
        speech_id = 1

        topic_match = re.search(r"<strong>(.*?)</strong>", li_html, re.S)
        if not topic_match:
            return speeches
        topic_title = self._clean_html(topic_match.group(1))
        speeches.append(
            {
                "id": speech_id,
                "mark": "",
                "name": "",
                "role": "topic",
                "comment": topic_title,
                "raw": topic_title,
            }
        )
        speech_id += 1

        remaining = li_html[topic_match.end() :]
        qa_pattern = re.compile(
            r"<strong>(質問|答弁)&nbsp;</strong>(.*?)(?=(<strong>(?:質問|答弁)&nbsp;</strong>|$))",
            re.S,
        )
        for role, content, _ in qa_pattern.findall(remaining):
            comment = self._clean_html(content)
            if role == "質問":
                mark = "◆"
                name = questioner
            else:
                mark = "◎"
                name = ""
            speeches.append(
                {
                    "id": speech_id,
                    "mark": mark,
                    "name": name,
                    "role": role,
                    "comment": comment,
                    "raw": f"{role}{comment}",
                }
            )
            speech_id += 1
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
