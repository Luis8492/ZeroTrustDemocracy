"""Parser implementation for Setagaya regular session meeting minutes."""

from __future__ import annotations

from typing import Any, Dict, List

from app.municipal_modules.base.base_minute_parser import BaseMinuteParser
from utils.logger import get_logger

logger = get_logger(__name__)


class Setagaya2Parser(BaseMinuteParser):
    """Parser for Setagaya regular session meeting minutes."""

    def extract_meeting_data(self, text: str) -> Dict[str, Any]:
        """Extract meeting metadata such as date and name."""
        raise NotImplementedError("Meeting data extraction is not implemented.")

    def extract_topic_section(self, text: str) -> List[str]:
        """Split the minutes text into topic sections."""
        raise NotImplementedError("Topic section extraction is not implemented.")

    def extract_speeches(self, topic_text: str) -> List[Dict[str, Any]]:
        """Extract speech entries from a topic section."""
        raise NotImplementedError("Speech extraction is not implemented.")

    def extract_QAs(self, minute: Dict[str, Any]) -> List[Any]:
        """Convert parsed minute data into QA sequences."""
        raise NotImplementedError("QA extraction is not implemented.")
