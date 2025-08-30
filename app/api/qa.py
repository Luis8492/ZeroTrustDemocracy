from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from pathlib import Path
import sqlite3, random, json, csv

from anonymizer import Anonymizer

router = APIRouter()

class EvaledRequest(BaseModel):
    evaled_ids: List[int]
    municipality: Optional[str] = None


def get_context(municipality: str):
    base_dir = Path(__file__).resolve().parent.parent
    db_dir = base_dir / "db" / municipality
    db_path = db_dir / "minutes.db"
    if not db_path.exists():
        db_path = base_dir / "db" / "minutes.db"
    party_file = base_dir / f"name-party-table-{municipality}.csv"
    if not party_file.exists():
        party_file = base_dir / "name-party-table.csv"
    with open(party_file, encoding="utf-8") as f:
        party_table = {
            "".join(row["Name"].split()): row["Party"]
            for row in csv.DictReader(f)
        }
    return db_path, party_table


@router.post("/next")
def get_next_qa(data: EvaledRequest, municipality: Optional[str] = Query(None)):
    m = municipality or data.municipality or "default"
    db_path, _ = get_context(m)
    non_evaled_ids = extract_non_evaled_QA(data.evaled_ids, db_path)
    if not non_evaled_ids:
        return {"message": "全て評価済みです"}
    target_id = random.choice(non_evaled_ids)
    qa = get_QA_by_id(target_id, db_path)
    return format_QA(qa, db_path)


@router.post("/meta")
def get_qa_meta(data: EvaledRequest, municipality: Optional[str] = Query(None)):
    m = municipality or data.municipality or "default"
    db_path, party_table = get_context(m)
    if not data.evaled_ids:
        return []
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    query = f"""
        SELECT q.id, q.questioner, q.topic_intro, q.QA, m.name, m.date
        FROM questions q
        JOIN meetings m ON q.file_name = m.file_name
        WHERE q.id IN ({','.join('?' for _ in data.evaled_ids)})
    """
    cur.execute(query, data.evaled_ids)
    metas = []
    for row in cur.fetchall():
        questioner = row[1]
        metas.append(
            {
                "id": row[0],
                "questioner": questioner,
                "questioner_party": party_table.get("".join(questioner.split()), ""),
                "topic_intro": json.loads(row[2]),
                "QA": json.loads(row[3]),
                "committee_name": row[4],
                "committee_date": row[5],
            }
        )
    conn.close()
    return metas


def extract_non_evaled_QA(evaled_ids: List[int], db_path: Path) -> List[int]:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    if evaled_ids:
        q = f"SELECT id FROM questions WHERE id NOT IN ({','.join(['?'] * len(evaled_ids))})"
        cur.execute(q, evaled_ids)
    else:
        cur.execute("SELECT id FROM questions")
    ids = [row[0] for row in cur.fetchall()]
    conn.close()
    return ids


def get_QA_by_id(qa_id: int, db_path: Path) -> Dict[str, Any]:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id,file_name,topic_intro,QA FROM questions WHERE id=?", (qa_id,))
    row = cur.fetchone()
    conn.close()
    return {
        "id": qa_id,
        "file_name": row[1],
        "topic_intro": row[2],
        "QA": row[3],
    }


def format_QA(entry: Dict[str, Any], db_path: Path) -> Dict[str, Any]:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id,date,name FROM meetings WHERE file_name=?", (entry.get("file_name"),))
    row = cur.fetchone()
    conn.close()
    return {
        "id": entry.get("id"),
        "committee_date": row[1],
        "committee_name": row[2],
        "topic_intro": anonymize_QA(json.loads(entry.get("topic_intro"))),
        "QA": anonymize_QA(json.loads(entry.get("QA"))),
        "eval_target": "◆",
    }


def anonymize_QA(QA: List[dict]):
    anonymized_QA = []
    anonymizer = Anonymizer()
    for speech in QA:
        anonymized_speech = {
            "mark": speech.get("mark"),
            "role": speech.get("role"),
            "comment": anonymizer.anonymize_comment(speech.get("comment")),
        }
        anonymized_QA.append(anonymized_speech)
    return anonymized_QA
