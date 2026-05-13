"""Parser implementation for Setagaya regular session meeting minutes."""

from __future__ import annotations

import csv
import html
import re
from pathlib import Path
from typing import Any, Dict, List

from app.municipal_modules.base.base_minute_parser import BaseMinuteParser
from app.municipal_modules.setagaya.regular.dev.pattern_classifier import classify_pattern

# Load party names once at import time to avoid repeated file I/O
_PARTY_NAMES: List[str]
_party_path = Path(__file__).resolve().parents[1] / "config" / "party_names.csv"
try:
    with _party_path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        _PARTY_NAMES = [row["partyname"].strip() for row in reader if row.get("partyname")]
except FileNotFoundError:  # pragma: no cover - defensive programming
    _PARTY_NAMES = []


class SetagayaRegularParser(BaseMinuteParser):
    """Parser for Setagaya regular session meeting minutes."""
    FETCHER_NAME = "SetagayaRegularFetcher"

    def __init__(self) -> None:  # pragma: no cover - simple init
        self.pattern: str = "Unknown"

    def _clean_html(self, text: str) -> str:
        text = re.sub(r"<br\s*/?>", "\n", text)
        text = re.sub(r"<.*?>", "", text)
        text = text.replace("&nbsp;", " ")
        return html.unescape(text).strip()

    def get_meeting_data(self, text: str) -> Dict[str, Any]:
        """Get meeting metadata such as date and name."""
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

    def divide_entire_minute_into_questioners(self, text: str) -> List[Dict[str, str]]:
        """Divide the entire minute HTML into per-questioner sections.

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
    
    def divide_questioner_piles_into_topics(self, questioner: Dict[str, str]) -> List[Dict[str, str]]:
        """Divide a questioner's HTML block into individual topic sections.

        The Setagaya minutes use several different HTML layouts.  For now we
        only support ``Pattern1`` (nested ``<ul>/<li>`` structure).  This
        function receives a dictionary produced by
        :meth:`divide_entire_minute_into_questioners` that contains the questioner's
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
        questioner_name = self.questioner_name_clearner(questioner.get("name", ""))
        text = questioner.get("section", "")
        ul_match = re.search(r"<ul>([\s\S]*)</ul>", text)
        if not ul_match:
            return []
        topics: List[Dict[str, Any]] = []
        
        patterns = {
            "Pattern1": (
                r"<li><strong>([\S\s]*?)</strong>[\s\S]*?"
                r"<li><strong>([\S\s]*?)</strong>([\S\s]*?)</li>[\S\s]*?"
                r"<li><strong>([\S\s]*?)</strong>([\S\s]*?)</li>",
                "<li><strong>{}</strong><li><strong{}</strong>{}</li><li><strong>{}</strong>{}</li>"
            ),
            "Pattern2": (
                r"<li><strong>([\s\S]*?)<br>([\s\S]*?)</strong>([\s\S]*?)<br>[\s\S]*?"
                r"<strong>([\s\S]*?)</strong>([\s\S]*?)</li>",
                "<li><strong>{}<br>{}</strong>{}<br><strong>{}</strong>{}</li>"
            ),
            "Pattern3": (
                r"<li><strong>([\s\S]*?)</strong><br>[\s\S]*?"
                r"<strong>([\s\S]*?)</strong>([\s\S]*?)<br>[\s\S]*?"
                r"<strong>([\s\S]*?)</strong>([\s\S]*?)</li>",
                "<li><strong>{}</strong><br><strong>{}</strong>{}<br><strong>{}</strong>{}</li>"
            ),
        }
        pattern_regex, raw_format = patterns.get(self.pattern, (None, None))
        if pattern_regex is None:
            return topics  # or raise Exception
        for topic, roleQ, question, roleA, answer in re.findall(pattern_regex, ul_match.group(1)):
            speeches = [
                {"id": 1, "mark": "○", "name": "議題", "role": "-", "raw": topic, "comment": self._clean_html(topic)},
                {"id": 2, "mark": "◆", "name": questioner_name, "role": self._normalize_role(roleQ), "comment": self._clean_html(question)},
                {"id": 3, "mark": "◎", "name": "回答者", "role": self._normalize_role(roleA), "comment": self._clean_html(answer)},
            ]
            topics.append({
                "name": questioner_name,
                "speeches": speeches,
                "raw": raw_format.format(topic, roleQ, question, roleA, answer)
            })
        return topics

    @staticmethod
    def _normalize_role(role: str) -> str:
        cleaned = role.replace("&nbsp;", " ").replace("\xa0", " ")
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip()
    def questioner_name_clearner(self, questioner_name: str) -> str:
        cleaned_name = questioner_name
        # delete "（*）"
        cleaned_name = re.sub(r"（[^）]*）", "", cleaned_name)
        # delete "議員"
        cleaned_name = cleaned_name.replace("議員", "")
        # delete any names in partyname and surrounding space(s)
        for party in _PARTY_NAMES:
            cleaned_name = re.sub(rf"\s*{re.escape(party)}\s*", "", cleaned_name)
        cleaned_name = re.sub(r"\s+", " ", cleaned_name)
        return cleaned_name.strip()
    
    def generate_QA_combination(self, minute: Dict[str, Any]) -> List[Any]:
        """Generate QA combinations from parsed minute data."""
        minute_QAs: List[Any] = []
        for topic in minute.get("topics", []):
            QA_topic = []
            intro_speeches = [topic["speeches"][0]]
            qa_seq = [topic["speeches"][1],topic["speeches"][2]]
            QA_topic.append(intro_speeches)
            QA_topic.append(qa_seq)
            minute_QAs.append(QA_topic)
        return minute_QAs


    def convert(self, text: str) -> Dict[str, Any]:
        """Convert raw minute text into structured data."""
        minute_json: Dict[str, Any] = {
            "meeting": self.get_meeting_data(text),
            "topics": [],
        }
        for questioner in self.divide_entire_minute_into_questioners(text):
            for j, topic in enumerate(self.divide_questioner_piles_into_topics(questioner), start=1):
                minute_json["topics"].append(
                    {
                        "topic_id": j,
                        "name": topic["name"],
                        "raw": topic["raw"],
                        "speeches": topic["speeches"]
                    }
                )
        minute_json["QAs"] = self.generate_QA_combination(minute_json)
        return minute_json
