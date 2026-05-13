"""Display parsed result for a Setagaya regular session minute (dev tool)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.minute_analyzer import analyze_minute
from app.municipal_modules.setagaya.regular.parsers.setagaya_regular_parser import (
    SetagayaRegularParser,
)
from config_loader import load_for_fetcher


def main(file_name: str) -> None:
    """Parse the given raw minute file and print structured JSON."""
    file_path = Path("raw_minutes") / file_name
    encoding = load_for_fetcher("setagaya", "SetagayaRegularFetcher").get("encoding", "utf-8")
    parser = SetagayaRegularParser()
    minute = analyze_minute(str(file_path), parser, encoding=encoding)
    print(json.dumps(minute, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/display_setagaya2_minute.py <file_name>")
    else:
        main(sys.argv[1])
