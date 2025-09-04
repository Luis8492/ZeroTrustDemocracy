"""Classify Setagaya meeting minutes HTML into predefined patterns.

This script inspects the HTML structure of a meeting minute and determines
which of the patterns described in ``setagaya2/README.md`` it matches.

Usage:
    python pattern_classifier.py path/to/minutes.html [another.html ...]

The script prints the detected pattern for each provided file.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable, List

# Allow optional attributes and intermediary tags/text between markers to cope
# with real-world HTML that may include formatting tags such as <strong> before
# nested lists.  The patterns mirror the three structures documented in
# ``setagaya2/README.md``.
PATTERN1_RE = re.compile(
    r"<li[^>]*>.*?<ul>.*?<li[^>]*>\s*<strong>質問", re.S
)
PATTERN2_RE = re.compile(
    r"<li[^>]*>\s*<strong>[^<]*?<br>\s*質問.*?</strong>", re.S
)
PATTERN3_RE = re.compile(
    r"<li[^>]*>\s*<strong>[^<]*?</strong>\s*<br>\s*<strong>質問</strong>",
    re.S,
)


def classify_pattern(html: str) -> str:
    """Return the pattern name for the given HTML snippet.

    Parameters
    ----------
    html: str
        Raw HTML text of the meeting minutes.

    Returns
    -------
    str
        "Pattern1", "Pattern2", "Pattern3", or "Unknown".
    """

    if PATTERN1_RE.search(html):
        return "Pattern1"
    if PATTERN2_RE.search(html):
        return "Pattern2"
    if PATTERN3_RE.search(html):
        return "Pattern3"
    return "Unknown"


def classify_files(paths: Iterable[Path]) -> List[str]:
    """Classify multiple files and return their pattern names."""
    results: List[str] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        results.append(classify_pattern(text))
    return results


def main() -> None:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "files", type=Path, nargs="+", help="HTML files of meeting minutes"
    )
    args = parser.parse_args()

    for path, result in zip(args.files, classify_files(args.files)):
        print(f"{path}: {result}")


if __name__ == "__main__":
    main()
