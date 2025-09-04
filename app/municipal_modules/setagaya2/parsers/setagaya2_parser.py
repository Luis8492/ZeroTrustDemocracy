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
        # Default to Pattern1 behaviour when pattern is unknown so that the
        # function can be exercised independently in unit tests.
        pattern = self.pattern if self.pattern != "Unknown" else "Pattern1"

        if pattern == "Pattern1":
            # topic_text is expected to look like:
            #   "質問者\n<strong>議題</strong><br>..."
            # where the first line contains the questioner name and the rest of
            # the string is a sequence of <strong> blocks describing the topic,
            # question and answers.
            questioner = ""
            body = topic_text
            if "\n" in topic_text:
                questioner, body = topic_text.split("\n", 1)
                questioner = self._clean_html(questioner)

            # Split at each <strong>..</strong> and capture the trailing text
            # until the next <strong> or end of string.
            segments = re.findall(r"<strong>(.*?)</strong>(.*?)(?=<strong>|$)", body, re.S)

            speech_id = 1
            for idx, (header, tail) in enumerate(segments):
                header_clean = self._clean_html(header)
                tail_clean = self._clean_html(tail)

                if idx == 0:
                    # First segment is the topic title.
                    speeches.append(
                        {"id": speech_id, "name": "", "comment": header_clean}
                    )
                    speech_id += 1
                    continue

                if header_clean.startswith("質問"):
                    name = questioner
                    comment = tail_clean
                else:
                    # For answers the speaker name may appear either after the
                    # generic marker (e.g. "答弁") or directly within the
                    # <strong> tag (e.g. "教育長").
                    if header_clean in ("答弁",):
                        parts = tail_clean.split("\n", 1)
                        name = parts[0] if parts else ""
                        comment = parts[1] if len(parts) > 1 else ""
                    else:
                        name = header_clean
                        comment = tail_clean

                speeches.append(
                    {"id": speech_id, "name": name, "comment": comment}
                )
                speech_id += 1

        elif pattern == "Pattern2":
            pass
        elif pattern == "Pattern3":
            pass
        # TODO: Pattern2 and Pattern3 are not yet implemented.
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
