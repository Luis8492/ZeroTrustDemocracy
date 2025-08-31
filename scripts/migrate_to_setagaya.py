#!/usr/bin/env python3
"""Create a sample default database and copy it to setagaya.db."""

from pathlib import Path
import argparse
import shutil
import sqlite3


def create_default_db(path: Path) -> None:
    """Generate a default SQLite database with sample data."""
    if path.exists():
        path.unlink()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT,
            date TEXT,
            name TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT,
            topic_intro TEXT,
            QA TEXT,
            questioner TEXT
        )
        """
    )
    cur.execute(
        "INSERT INTO meetings (file_name, date, name) VALUES (?, ?, ?)",
        ("sample.txt", "2024-01-01", "サンプル会議"),
    )
    cur.execute(
        "INSERT INTO questions (file_name, topic_intro, QA, questioner) VALUES (?, ?, ?, ?)",
        ("sample.txt", "sample intro", "sample QA", "サンプル議員"),
    )
    conn.commit()
    conn.close()


def main(src: Path, dst: Path) -> None:
    create_default_db(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dst)
    print(f"Created {src} and copied to {dst}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create default.db and copy to setagaya.db")
    parser.add_argument("--src", default="db/default.db", help="Path for generated default database")
    parser.add_argument("--dst", default="db/setagaya.db", help="Destination database path")
    args = parser.parse_args()
    main(Path(args.src), Path(args.dst))
