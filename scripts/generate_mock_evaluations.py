"""Generate a mock evaluations CSV for testing the statistics view.

Usage:
    python scripts/generate_mock_evaluations.py [--db DB_PATH] [-o OUTPUT]

The script reads all question IDs from the SQLite database and assigns a
random agreement score (-3 to +3) and importance score (0 to 3) to each
one, then writes a CSV file that can be imported via the frontend's
"CSV で読み込み" button on the statistics page.
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
    args = parser.parse_args()

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

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["QA_id", "eval", "importance"])
        for qa_id in ids:
            writer.writerow([qa_id, rng.randint(-3, 3), rng.randint(0, 3)])

    print(f"Wrote {len(ids)} mock evaluations to {args.output}")


if __name__ == "__main__":
    main()
