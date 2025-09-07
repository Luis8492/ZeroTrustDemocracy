import sqlite3
import sys
from pathlib import Path
from typing import Dict, List

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.logger import get_logger

logger = get_logger(__name__)

DB_PATH = Path(__file__).resolve().parent.parent / "db" / "setagaya.db"


def remove_duplicates(db_path: Path = DB_PATH) -> None:
    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    tables: Dict[str, List[str]] = {
        "minutes": ["url", "file_name", "analyzed"],
        "meetings": ["file_name", "date", "name"],
        "downloaded_minutes_url_helper": ["url"],
        "questions": ["file_name", "topic_intro", "QA", "questioner"],
    }

    for table, columns in tables.items():
        group_cols = ", ".join(columns)
        logger.info(f"Removing duplicates from {table}")
        cur.execute(
            f"""
DELETE FROM {table}
WHERE rowid NOT IN (
    SELECT MIN(rowid)
    FROM {table}
    GROUP BY {group_cols}
)
"""
        )
        logger.info(f"Deleted {cur.rowcount} rows from {table}")

    conn.commit()
    conn.close()
    logger.info("Duplicate removal complete")


if __name__ == "__main__":
    remove_duplicates()
