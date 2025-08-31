import os
import sqlite3
import random
import json
import csv
import importlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from anonymizer import Anonymizer
from config import load_config

# APIRouter for QA endpoints
qa_router = APIRouter(prefix="/api/qa")

logger = logging.getLogger(__name__)


class EvaledRequest(BaseModel):
    """Request body for QA related endpoints."""

    evaled_ids: List[int]
    municipality: Optional[str] = None


# Party table is shared across municipalities
with open(
    Path(__file__).resolve().parent.parent / "name-party-table.csv",
    encoding="utf-8",
) as f:
    PARTY_TABLE = {"".join(row["Name"].split()): row["Party"] for row in csv.DictReader(f)}


def get_context(municipality: str):
    """Load municipality specific resources.

    Parameters
    ----------
    municipality: str
        Municipality name provided via query or body.
    """
    root = Path(__file__).resolve().parent.parent.parent
    config = load_config(municipality)
    anonymizer = Anonymizer(pii_dir=config["pii_dir"])
    db_path = root / config.get("db_path", f"db/{municipality}.db")
    municipality_id = config.get("municipality_id")
    parser = None
    try:
        parser = importlib.import_module(f"parsers.{municipality}")
    except ModuleNotFoundError:
        pass
    return anonymizer, str(db_path), municipality_id, parser


@qa_router.post("/next")
def get_next_qa(data: EvaledRequest, municipality: Optional[str] = Query(None)):
    municipality = municipality or data.municipality or os.getenv("MUNICIPALITY", "default")
    anonymizer, db_path, municipality_id, _ = get_context(municipality)
    non_evaled_ids = extract_non_evaled_QA(data.evaled_ids, db_path, municipality_id)
    if not non_evaled_ids:
        return {"message": "全て評価済みです"}
    target_id = random.choice(non_evaled_ids)
    qa = get_QA_by_id(target_id, db_path, municipality_id)
    return format_QA(qa, db_path, municipality_id, anonymizer)


@qa_router.post("/meta")
def get_qa_meta(data: EvaledRequest, municipality: Optional[str] = Query(None)):
    municipality = municipality or data.municipality or os.getenv("MUNICIPALITY", "default")
    anonymizer, db_path, municipality_id, _ = get_context(municipality)
    if not data.evaled_ids:
        return []
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    placeholder = ",".join("?" for _ in data.evaled_ids)
    base_query = (
        "SELECT q.id, q.questioner, q.topic_intro, q.QA, m.name, m.date "
        "FROM questions q "
        "JOIN meetings m ON q.file_name = m.file_name"
    )
    if municipality_id is not None:
        query = base_query + f" WHERE q.id IN ({placeholder}) AND q.municipality_id = ?"
        cur.execute(query, data.evaled_ids + [municipality_id])
    else:
        query = base_query + f" WHERE q.id IN ({placeholder})"
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


def extract_non_evaled_QA(
    evaled_ids: List[int], db_path: str, municipality_id: Optional[int]
) -> List[int]:
    conn = None
    ids: List[int] = []
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        if municipality_id is not None:
            if evaled_ids:
                placeholders = ",".join(["?"] * len(evaled_ids))
                q = (
                    f"SELECT id FROM questions WHERE municipality_id = ? "
                    f"AND id NOT IN ({placeholders})"
                )
                cur.execute(q, [municipality_id] + evaled_ids)
            else:
                cur.execute(
                    "SELECT id FROM questions WHERE municipality_id = ?",
                    (municipality_id,),
                )
        else:
            if evaled_ids:
                placeholders = ",".join(["?"] * len(evaled_ids))
                q = f"SELECT id FROM questions WHERE id NOT IN ({placeholders})"
                cur.execute(q, evaled_ids)
            else:
                cur.execute("SELECT id FROM questions")
        ids = [row[0] for row in cur.fetchall()]
    except sqlite3.Error:
        logger.exception("Failed to extract non-evaluated QA IDs")
        raise HTTPException(status_code=500, detail="Failed to query database")
    finally:
        if conn:
            conn.close()
    return ids


def get_QA_by_id(
    qa_id: int, db_path: str, municipality_id: Optional[int]
) -> Dict[str, Any]:
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        if municipality_id is not None:
            cur.execute(
                "SELECT id,file_name,topic_intro,QA FROM questions WHERE id=? AND municipality_id=?",
                (qa_id, municipality_id),
            )
        else:
            cur.execute(
                "SELECT id,file_name,topic_intro,QA FROM questions WHERE id=?",
                (qa_id,),
            )
        row = cur.fetchone()
    except sqlite3.Error:
        logger.exception("Failed to retrieve QA by id %s", qa_id)
        raise HTTPException(status_code=500, detail="Failed to query database")
    finally:
        if conn:
            conn.close()
            if row is None:
              raise HTTPException(status_code=404, detail="QA not found")
    return {
        "id": qa_id,
        "file_name": row[1],
        "topic_intro": row[2],
        "QA": row[3],
    }


def format_QA(
    entry: Dict[str, Any], db_path: str, municipality_id: Optional[int], anonymizer: Anonymizer
) -> Dict[str, Any]:
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        if municipality_id is not None:
            cur.execute(
                "SELECT id,date,name FROM meetings WHERE file_name=? AND municipality_id=?",
                (entry.get("file_name"), municipality_id),
            )
        else:
            cur.execute(
                "SELECT id,date,name FROM meetings WHERE file_name=?",
                (entry.get("file_name"),),
            )
        row = cur.fetchone()
    except sqlite3.Error:
        logger.exception("Failed to format QA for entry %s", entry.get("id"))
        raise HTTPException(status_code=500, detail="Failed to query database")
    finally:
        if conn:
            conn.close()
            if row is None:
              raise HTTPException(status_code=404, detail="QA not found")
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
