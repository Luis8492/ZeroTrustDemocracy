"""Phase 0a quality check: assess how cleanly setagaya2 (regular session)
raw minutes can be converted into per-questioner QA sequences.

Runs the Setagaya2Parser against every SetagayaRegularFetcher_*.html under
app/raw_minutes/ and prints a summary report.
"""

from __future__ import annotations

import json
import sys
import traceback
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(REPO_ROOT))

from app.municipal_modules.setagaya.regular.parsers.setagaya_regular_parser import (
    SetagayaRegularParser as Setagaya2Parser,
)
from app.municipal_modules.setagaya.regular.dev.pattern_classifier import classify_pattern


def main() -> None:
    raw_dir = REPO_ROOT / "app" / "raw_minutes"
    files = sorted(raw_dir.glob("SetagayaRegularFetcher_*.html"))
    if not files:
        print("No SetagayaRegularFetcher samples found.")
        return

    parser = Setagaya2Parser()
    pattern_counts: Counter[str] = Counter()
    zero_topic_files: list[Path] = []
    error_files: list[tuple[Path, str]] = []
    topic_totals: list[int] = []
    qa_seq_totals: list[int] = []
    sample_topics: list[dict] = []

    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            error_files.append((path, f"read: {exc}"))
            continue

        pattern = classify_pattern(text)
        pattern_counts[pattern] += 1

        try:
            minute = parser.convert(text)
        except Exception as exc:
            error_files.append((path, f"convert: {exc}"))
            traceback.print_exc()
            continue

        topics = minute.get("topics", [])
        qas = minute.get("QAs", [])
        topic_totals.append(len(topics))
        qa_seq_totals.append(sum(len(t) for t in qas))
        if not topics:
            zero_topic_files.append(path)
        elif len(sample_topics) < 2:
            sample_topics.append(
                {
                    "file": path.name,
                    "meeting": minute.get("meeting"),
                    "first_topic": topics[0],
                    "first_QA_group": qas[0] if qas else None,
                }
            )

    total = len(files)
    print("=== Setagaya2 (Regular Session) Parser Quality Report ===")
    print(f"Total samples: {total}")
    print(f"Pattern distribution: {dict(pattern_counts)}")
    print(f"Zero-topic files: {len(zero_topic_files)} / {total}")
    print(f"Error files: {len(error_files)}")
    if topic_totals:
        print(
            f"Topics per file: min={min(topic_totals)} max={max(topic_totals)} "
            f"avg={sum(topic_totals)/len(topic_totals):.1f}"
        )
        print(
            f"QA sequences per file (incl. intro): min={min(qa_seq_totals)} "
            f"max={max(qa_seq_totals)} avg={sum(qa_seq_totals)/len(qa_seq_totals):.1f}"
        )
    if zero_topic_files:
        print("\nFiles producing zero topics:")
        for p in zero_topic_files[:10]:
            print(f"  - {p.name}")
        if len(zero_topic_files) > 10:
            print(f"  ... and {len(zero_topic_files) - 10} more")
    if error_files:
        print("\nFiles raising errors:")
        for p, msg in error_files[:10]:
            print(f"  - {p.name}: {msg}")

    if sample_topics:
        print("\n=== Sample parsed topic (first non-empty file) ===")
        sample = sample_topics[0]
        print(f"File: {sample['file']}")
        print(f"Meeting: {sample['meeting']}")
        topic = sample["first_topic"]
        print(f"Topic questioner: {topic.get('name')}")
        for speech in topic.get("speeches", []):
            comment = speech.get("comment", "")
            preview = comment[:100].replace("\n", " ")
            print(
                f"  [{speech.get('mark')}] {speech.get('name')} ({speech.get('role')}): {preview}..."
            )


if __name__ == "__main__":
    main()
