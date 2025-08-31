from __future__ import annotations

import json
from typing import Dict, Any

from municipal_modules.parsers.base_minute_parser import BaseMinuteParser


def convert_minute_txt_to_json(text: str, parser: BaseMinuteParser) -> Dict[str, Any]:
    """Convert raw minute text to a structured JSON-like dict using the given parser."""
    minute_json: Dict[str, Any] = {"meeting": parser.extract_meeting_data(text), "topics": []}
    for i, topic_section in enumerate(parser.extract_topic_section(text), start=1):
        speeches = parser.extract_speeches(topic_section)
        minute_json["topics"].append(
            {"topic_id": i, "raw": topic_section, "speeches": speeches}
        )
    return minute_json
