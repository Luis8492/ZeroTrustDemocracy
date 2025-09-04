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

    def extract_topic_section(self, questioner: Dict[str, str]) -> List[Dict[str, str]]:
        """Split a questioner's HTML block into individual topic sections.

        The Setagaya minutes use several different HTML layouts.  For now we
        only support ``Pattern1`` (nested ``<ul>/<li>`` structure).  This
        function receives a dictionary produced by
        :meth:`extract_questioner_section` that contains the questioner's
        ``name`` and raw HTML ``section``.  It returns a list of dictionaries
        where each item represents one topic ``<li>`` block together with the
        questioner's name.

        Parameters
        ----------
        questioner: Dict[str, str]
            A dictionary with ``name`` and ``section`` keys.  ``section`` is
            expected to contain a ``<ul>`` element in ``Pattern1`` format.

        Returns
        -------
        List[Dict[str, str]]
            Each element has ``name`` (the questioner) and ``section`` (raw
            HTML for the topic ``<li>`` block).
        """

        if self.pattern != "Pattern1":
            print('Not pattern1')
            return []

        name = questioner.get("name", "")
        text = questioner.get("section", "")

        ul_match = re.search(r"<ul>([\s\S]*)</ul>", text)
        if not ul_match:
            return []

        topics: List[Dict[str, str]] = []
        for topic, qa in re.findall(r"<li>([\s\S]*?)<ul>([\s\S]*?)</ul>", ul_match.group(1)):
            li_block = f"<li>{topic}<ul>{qa}</ul></li>"
            topics.append({"name": name, "section": li_block})
        return topics

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

    def extract_questioner_section(self, text: str) -> List[Dict[str, str]]:
        """Split raw HTML into per-questioner sections.

        The Setagaya minutes have two major layouts.  Representative
        questions use ``<h2>`` headings for each questioner, while general
        questions list all questioners at the top and then use ``<h3>``
        headings for individual sections.  This function normalises both
        forms and returns a list of dictionaries containing the questioner's
        name and the corresponding HTML fragment.
        """

        sections: List[Dict[str, str]] = []

        if re.search(r"<h2[^>]*>\s*質問者一覧", text):
            # General questions – questioners appear as <h3> blocks
            pattern = re.compile(
                r"<h3[^>]*>(.*?)</h3>([\s\S]*?)(?=<h3|<p)",
            )
            for heading, body in pattern.findall(text + "<p>"):
                name = self._clean_html(heading)
                sections.append({"name": name, "section": body})
        else:
            # Representative questions – each <h2> corresponds to a questioner
            pattern = re.compile(
                r"<h2[^>]*>(.*?)</h2>([\s\S]*?)(?=<h2|<p)",
            )
            for heading, body in pattern.findall(text + "<p>"):
                name = self._clean_html(heading)
                sections.append({"name": name, "section": body})
        return sections

    def convert(self, text: str) -> Dict[str, Any]:
        """Convert raw minute text into structured data."""
        minute_json: Dict[str, Any] = {
            "meeting": self.extract_meeting_data(text),
            "topics": [],
        }
        for questioner in self.extract_questioner_section(text):
            for j, topic in enumerate(
                self.extract_topic_section(questioner), start=1
            ):
                minute_json["topics"].append(
                    {
                        "topic_id": j,
                        "name": topic["name"],
                        "raw": topic["section"],
                        "speeches": [],
                    }
                )
        minute_json["QAs"] = self.extract_QAs(minute_json)
        return minute_json
