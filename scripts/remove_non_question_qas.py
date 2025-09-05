import json
import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config_loader import load
from utils.logger import get_logger


logger = get_logger(__name__)


def has_questioner_mark(qa_text: str) -> bool:
    """Return True if QA JSON contains a speech marked with '◆'."""
    try:
        qa = json.loads(qa_text)
    except json.JSONDecodeError:
        return False
    if not isinstance(qa, list):
        return False
    return any(
        isinstance(speech, dict) and speech.get("mark") == "◆" for speech in qa
    )


def remove_non_question_qas(municipality: str = "setagaya") -> None:
    config = load(municipality)
    db_path = Path(config["db_path"])
    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        return
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id, QA FROM questions")
    rows = cur.fetchall()
    ids_to_delete = [row[0] for row in rows if not has_questioner_mark(row[1])]
    if ids_to_delete:
        cur.executemany(
            "DELETE FROM questions WHERE id=?", [(i,) for i in ids_to_delete]
        )
        conn.commit()
    logger.info(
        f"Deleted {len(ids_to_delete)} QA entries without questioner mark (◆)."
    )
    conn.close()


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "setagaya"
    remove_non_question_qas(target)
