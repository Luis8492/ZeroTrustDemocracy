from __future__ import annotations

from abc import ABC, abstractmethod


class BaseMinuteParser(ABC):
    """Base parser for council meeting minutes."""

    def convert_minute_txt_to_json(self, text: str) -> dict:
        """Convert raw minute text into structured JSON."""
        return {
            "meeting": self.parse_meeting_header(text),
            "topics": self._parse_topics(text),
        }

    def _parse_topics(self, text: str) -> list:
        topics = []
        for i, topic_section in enumerate(self._extract_topic_section(text), start=1):
            speeches = self.parse_speeches(topic_section)
            topics.append({
                "topic_id": i,
                "raw": topic_section,
                "speeches": speeches,
            })
        return topics

    @abstractmethod
    def _extract_topic_section(self, text: str) -> list:
        """Split raw minute text into topic sections."""

    @abstractmethod
    def parse_meeting_header(self, text: str) -> dict:
        """Parse the meeting header and return metadata."""

    @abstractmethod
    def parse_speeches(self, topic_text: str) -> list:
        """Parse speeches within a topic section."""
