import json
import sqlite3
from pathlib import Path
import sys

# Ensure the repository root is on ``sys.path`` so that this script can be
# executed directly (e.g. ``python scripts/remove_non_question_qas.py``) without
# ``ModuleNotFoundError``. When run as a standalone script the ``scripts``
# directory is placed on the module search path, but the project root (which
# contains the ``utils`` package) is not. Prepending the root fixes the import.
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from utils.logger import get_logger


logger = get_logger(__name__)

def has_question_mark(qa_text: str) -> bool:
    """Return True if QA JSON contains a speech marked with '◆'."""
    try:
        qa = json.loads(qa_text)
    except json.JSONDecodeError:
        return False
    if not isinstance(qa, list):
        return False
    for speech in qa:
        if isinstance(speech, dict) and speech.get("mark") == "◆":
            return True
    return False

def main():
    db_path = repo_root / "db" / "minutes.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id, QA FROM questions")
    rows = cur.fetchall()
    ids_to_delete = [row[0] for row in rows if not has_question_mark(row[1])]
    if ids_to_delete:
        cur.executemany("DELETE FROM questions WHERE id=?", [(i,) for i in ids_to_delete])
        conn.commit()
    logger.info(f"Deleted {len(ids_to_delete)} QA entries without question mark.")
    conn.close()

if __name__ == "__main__":
    main()
