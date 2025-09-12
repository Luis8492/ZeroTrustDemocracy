import sqlite3
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config_loader import load
from app.minute_analyzer import analyze_minute, get_parser


def add_participants_column(municipality: str = "setagaya") -> None:
    """Add participants column to meetings table and backfill existing rows."""
    config = load(municipality)
    db_path = Path(config["db_path"])
    encoding = config.get("encoding", "cp932")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Ensure participants column exists
    cur.execute("PRAGMA table_info(meetings)")
    columns = [row[1] for row in cur.fetchall()]
    if "participants" not in columns:
        cur.execute("ALTER TABLE meetings ADD COLUMN participants TEXT")
        conn.commit()

    parser = get_parser(municipality)

    cur.execute(
        "SELECT file_name FROM meetings WHERE participants IS NULL OR participants = ''"
    )
    rows = cur.fetchall()
    for (file_name,) in rows:
        file_path = Path("raw_minutes") / file_name
        if not file_path.exists():
            file_path = Path("app/raw_minutes") / file_name
        if not file_path.exists():
            continue
        try:
            minute_json = analyze_minute(str(file_path), parser, encoding=encoding)
        except Exception:
            continue
        participants = minute_json.get("meeting", {}).get("participants", [])
        participants_text = json.dumps(participants, ensure_ascii=False)
        cur.execute(
            "UPDATE meetings SET participants = ? WHERE file_name = ?",
            (participants_text, file_name),
        )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "setagaya"
    add_participants_column(target)
