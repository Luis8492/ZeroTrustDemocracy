"""Generate a mock evaluations CSV for testing the statistics view.

Usage:
    python scripts/generate_mock_evaluations.py [--db DB_PATH] [-o OUTPUT] [--ratio R]

The script reads all question IDs from the SQLite database, randomly samples
a portion (default 80%), and assigns each a random agreement score (-3 to +3)
and importance score (0 to 3). The remaining QAs are left out so the
frontend's evaluation screen still has unevaluated items to display.
The output CSV can be imported via the "CSV で読み込み" button on the
statistics page.
"""

import argparse
import csv
import random
import sqlite3
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Generate mock evaluation CSV")
    parser.add_argument(
        "--db",
        default="db/setagaya.db",
        help="Path to the SQLite database (default: db/setagaya.db)",
    )
    parser.add_argument(
        "-o", "--output",
        default="mock_evaluations.csv",
        help="Output CSV file path (default: mock_evaluations.csv)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible output",
    )
    parser.add_argument(
        "--ratio",
        type=float,
        default=0.8,
        help="Fraction of QAs to mark as evaluated (default: 0.8)",
    )
    args = parser.parse_args()

    if not 0 < args.ratio <= 1:
        print("Error: --ratio must be in (0, 1]", file=sys.stderr)
        sys.exit(1)

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"Error: database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("SELECT id FROM questions")
    ids = [row[0] for row in cur.fetchall()]
    conn.close()

    if not ids:
        print("Error: no questions found in the database", file=sys.stderr)
        sys.exit(1)

    rng = random.Random(args.seed)

    sample_size = max(1, round(len(ids) * args.ratio))
    sampled_ids = rng.sample(ids, sample_size)

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["QA_id", "eval", "importance"])
        for qa_id in sampled_ids:
            writer.writerow([qa_id, rng.randint(-3, 3), rng.randint(0, 3)])

    print(
        f"Wrote {sample_size} mock evaluations ({sample_size}/{len(ids)}, "
        f"{sample_size / len(ids):.0%}) to {args.output}"
    )


if __name__ == "__main__":
    main()
