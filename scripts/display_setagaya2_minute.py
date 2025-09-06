"""Display parsed result for a Setagaya regular session minute."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.minute_analyzer import convert_minute_txt_to_json
from app.municipal_modules.setagaya2.parsers.setagaya2_parser import Setagaya2Parser
from config_loader import load


def main(file_name: str) -> None:
    """Parse the given raw minute file and print structured JSON."""
    file_path = Path("raw_minutes") / file_name
    encoding = load("setagaya2").get("encoding", "utf-8")
    text = file_path.read_text(encoding=encoding)
    parser = Setagaya2Parser()
    minute = convert_minute_txt_to_json(text, parser)
    minute["file_name"] = file_name
    minute["QAs"] = parser.generate_QA_combination(minute)
    print(json.dumps(minute, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/display_setagaya2_minute.py <file_name>")
    else:
        main(sys.argv[1])
