import json
import sqlite3
from pathlib import Path

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
    db_path = Path(__file__).resolve().parent / "db" / "minutes.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id, QA FROM questions")
    rows = cur.fetchall()
    ids_to_delete = [row[0] for row in rows if not has_question_mark(row[1])]
    if ids_to_delete:
        cur.executemany("DELETE FROM questions WHERE id=?", [(i,) for i in ids_to_delete])
        conn.commit()
    print(f"Deleted {len(ids_to_delete)} QA entries without question mark.")
    conn.close()

if __name__ == "__main__":
    main()
