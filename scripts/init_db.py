import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config_loader import load


def init_db(municipality: str = "setagaya"):
    config = load(municipality)
    db_path = Path(config["db_path"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
CREATE TABLE IF NOT EXISTS minutes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE,
    file_name TEXT,
    analyzed INTEGER
)
"""
    )
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
    conn.commit()
    conn.close()


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "setagaya"
    init_db(target)
