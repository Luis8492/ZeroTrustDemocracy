import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config_loader import load


def add_fetcher_column(municipality: str = "setagaya", fetcher_value: str = "SetagayaCommitteeFetcher"):
    """Add fetcher column to minutes table if missing and set default value."""
    config = load(municipality)
    db_path = Path(config["db_path"])
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(minutes)")
    columns = [row[1] for row in cur.fetchall()]
    if "fetcher" not in columns:
        cur.execute(
            f"ALTER TABLE minutes ADD COLUMN fetcher TEXT NOT NULL DEFAULT '{fetcher_value}'"
        )
        # Existing rows get default automatically, but ensure explicitly
        cur.execute("UPDATE minutes SET fetcher = ? WHERE fetcher IS NULL", (fetcher_value,))
        conn.commit()
    conn.close()


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "setagaya"
    add_fetcher_column(target)
