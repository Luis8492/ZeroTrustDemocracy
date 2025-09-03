import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config_loader import load


def add_fetcher_column(
    municipality: str = "setagaya", fetcher_value: str = "SetagayaCommitteeFetcher"
) -> None:
    """Add fetcher column to minutes table and prefix existing filenames.

    This updates the `minutes` table to include a `fetcher` column if it
    doesn't exist and renames stored file names and actual files on disk to
    include the fetcher name as a prefix. Related tables (`meetings` and
    `questions`) that reference the old file names are also updated so they
    point to the new, prefixed names.
    """
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
        cur.execute(
            "UPDATE minutes SET fetcher = ? WHERE fetcher IS NULL", (fetcher_value,)
        )
        conn.commit()

    cur.execute("SELECT id, file_name, fetcher FROM minutes")
    rows = cur.fetchall()
    for minute_id, file_name, fetcher in rows:
        if not file_name:
            continue
        prefix = f"{fetcher}_"
        if file_name.startswith(prefix):
            continue
        new_file_name = prefix + file_name
        old_path = Path("raw_minutes") / file_name
        new_path = Path("raw_minutes") / new_file_name
        if not old_path.exists():
            old_path = Path("app/raw_minutes") / file_name
            new_path = Path("app/raw_minutes") / new_file_name
        if old_path.exists():
            old_path.rename(new_path)
        cur.execute(
            "UPDATE minutes SET file_name = ? WHERE id = ?", (new_file_name, minute_id)
        )
        for table in ("meetings", "questions"):
            cur.execute(
                f"UPDATE {table} SET file_name = ? WHERE file_name = ?",
                (new_file_name, file_name),
            )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "setagaya"
    add_fetcher_column(target)
