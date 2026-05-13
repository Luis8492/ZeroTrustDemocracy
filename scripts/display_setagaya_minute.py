"""Display parsed result for a Setagaya committee minute (dev tool)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.minute_analyzer import analyze_minute
from app.municipal_modules.setagaya.committee.parsers.setagaya_committee_parser import (
    SetagayaCommitteeParser,
)
from config_loader import load_for_fetcher


def main(file_name: str) -> None:
    """Parse the given raw minute file and print structured JSON."""
    file_path = Path("raw_minutes") / file_name
    print(file_path)
    encoding = load_for_fetcher("setagaya", "SetagayaCommitteeFetcher").get("encoding", "cp932")
    parser = SetagayaCommitteeParser()
    minute = analyze_minute(str(file_path), parser, encoding=encoding)
    print(json.dumps(minute, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/display_setagaya_minute.py <file_name>")
    else:
        main(sys.argv[1])
