import csv
import json
import random
import sqlite3
from importlib import import_module
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from anonymizer import Anonymizer
from config import load_config

qa_router = APIRouter(prefix="/api/qa")


class EvaledRequest(BaseModel):
    evaled_ids: List[int] = []
    municipality: Optional[str] = None


def _get_resources(municipality: str) -> tuple[Anonymizer, object, str]:
    """Load config, parser and DB path for the municipality."""
    config = load_config(municipality)
    anonymizer = Anonymizer(pii_dir=config["pii_dir"])
    parser_name = config.get("parser", "setagaya")
    module = import_module(f"parsers.{parser_name}")
    parser_class = getattr(module, f"{parser_name.capitalize()}Parser")
    parser = parser_class()
    db_path = config.get("db_path", "db/minutes.db")
    return anonymizer, parser, db_path


with open(
    Path(__file__).resolve().parent.parent / "name-party-table.csv",
    encoding="utf-8",
) as f:
    PARTY_TABLE = {"".join(row["Name"].split()): row["Party"] for row in csv.DictReader(f)}


@qa_router.post("/next")
def get_next_qa(
    data: EvaledRequest,
    municipality: str = Query("default"),
):
    municipality = data.municipality or municipality
    anonymizer, _parser, db_path = _get_resources(municipality)
    non_evaled_ids = extract_non_evaled_QA(data.evaled_ids, db_path)
    if not non_evaled_ids:
        return {"message": "全て評価済みです"}
    target_id = random.choice(non_evaled_ids)
    qa = get_QA_by_id(target_id, db_path)
    return format_QA(qa, db_path, anonymizer)


@qa_router.post("/meta")
def get_qa_meta(
    data: EvaledRequest,
    municipality: str = Query("default"),
):
    municipality = data.municipality or municipality
    anonymizer, _parser, db_path = _get_resources(municipality)
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
                "questioner_party": PARTY_TABLE.get(questioner, ""),
                "topic_intro": json.loads(row[2]),
                "QA": json.loads(row[3]),
                "committee_name": row[4],
                "committee_date": row[5],
            }
        )
    conn.close()
    return metas


def extract_non_evaled_QA(evaled_ids: List[int], db_path: str) -> List[int]:
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


def get_QA_by_id(qa_id: int, db_path: str) -> Dict[str, Any]:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "SELECT id,file_name,topic_intro,QA FROM questions WHERE id=?",
        (qa_id,),
    )
    row = cur.fetchone()
    conn.close()
    return {
        "id": qa_id,
        "file_name": row[1],
        "topic_intro": row[2],
        "QA": row[3],
    }


def format_QA(entry: Dict[str, Any], db_path: str, anonymizer: Anonymizer) -> Dict[str, Any]:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "SELECT id,date,name FROM meetings WHERE file_name=?",
        (entry.get("file_name"),),
    )
    row = cur.fetchone()
    conn.close()
    return {
        "id": entry.get("id"),
        "committee_date": row[1],
        "committee_name": row[2],
        "topic_intro": anonymize_QA(json.loads(entry.get("topic_intro")), anonymizer),
        "QA": anonymize_QA(json.loads(entry.get("QA")), anonymizer),
        "eval_target": "◆",
    }


def anonymize_QA(QA: List[dict], anonymizer: Anonymizer):
    anonymized_QA = []
    for speech in QA:
        anonymized_speech = {
            "mark": speech.get("mark"),
            "role": speech.get("role"),
            "comment": anonymizer.anonymize_comment(speech.get("comment")),
        }
        anonymized_QA.append(anonymized_speech)
    return anonymized_QA
