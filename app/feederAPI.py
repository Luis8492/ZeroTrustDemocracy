from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Tuple
import sqlite3, random, json, csv, sys
from pathlib import Path
from anonymizer import Anonymizer
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config_loader import load, load_global

ALLOWED_MUNICIPALITIES = {"Tokyo"}


def validate_municipality(name: str) -> str:
    if name not in ALLOWED_MUNICIPALITIES:
        raise HTTPException(status_code=400, detail="Unsupported municipality")
    return name


def load_party_table(path: str) -> Dict[str, str]:
    with open(path, encoding="utf-8") as f:
        return {"".join(row["Name"].split()): row["Party"] for row in csv.DictReader(f)}


global_config = load_global()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=global_config.get("allow_origins", []),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EvaledRequest(BaseModel):
    evaled_ids: List[int]  # POSTデータ受け用

@app.post("/api/qa/next")
def get_next_qa(data: EvaledRequest, municipality: str = Query("Tokyo")):
    try:
        municipality = validate_municipality(municipality)
        config = load(municipality)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    non_evaled = extract_non_evaled_QA(data.evaled_ids, config)
    if not non_evaled:
        return {"message": "全て評価済みです"}
    eval_counts = get_eval_counts(data.evaled_ids, config)
    ids = [row[0] for row in non_evaled]
    questioners = [row[1] for row in non_evaled]
    weights = [1 / (eval_counts.get(q, 0) + 1) for q in questioners]
    target_id = random.choices(ids, weights=weights, k=1)[0]
    qa = get_QA_by_id(target_id, config)
    return format_QA(qa, config)

@app.post("/api/qa/meta")
def get_qa_meta(data: EvaledRequest, municipality: str = Query("Tokyo")):
    if not data.evaled_ids:
        return []
    try:
        municipality = validate_municipality(municipality)
        config = load(municipality)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    party_table = load_party_table(config["party_table_path"])

    conn = sqlite3.connect(config["db_path"])
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
                "questioner_party": party_table.get(questioner, ""),
                "topic_intro": json.loads(row[2]),
                "QA": json.loads(row[3]),
                "committee_name": row[4],
                "committee_date": row[5],
            }
        )
    conn.close()
    return metas

def extract_non_evaled_QA(evaled_ids: List[int], config: Dict[str, Any]) -> List[Tuple[int, str]]:
    conn = sqlite3.connect(config["db_path"])
    cur = conn.cursor()
    if evaled_ids:
        q = f"SELECT id, questioner FROM questions WHERE id NOT IN ({','.join(['?'] * len(evaled_ids))})"
        cur.execute(q, evaled_ids)
    else:
        cur.execute("SELECT id, questioner FROM questions")
    rows = cur.fetchall()
    conn.close()
    return [(row[0], row[1]) for row in rows]

def get_eval_counts(evaled_ids: List[int], config: Dict[str, Any]) -> Dict[str, int]:
    if not evaled_ids:
        return {}
    conn = sqlite3.connect(config["db_path"])
    cur = conn.cursor()
    q = f"SELECT questioner, COUNT(*) FROM questions WHERE id IN ({','.join(['?'] * len(evaled_ids))}) GROUP BY questioner"
    cur.execute(q, evaled_ids)
    counts = {row[0]: row[1] for row in cur.fetchall()}
    conn.close()
    return counts

def get_QA_by_id(qa_id: int, config: Dict[str, Any]) -> Dict[str, Any]:
    conn = sqlite3.connect(config["db_path"])
    cur = conn.cursor()
    cur.execute("SELECT id,file_name,topic_intro,QA FROM questions WHERE id=?", (qa_id,))
    row = cur.fetchone()
    conn.close()
    return {
        "id": qa_id,
        "file_name":row[1],
        "topic_intro": row[2],
        "QA": row[3]
    }

def format_QA(entry: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    conn = sqlite3.connect(config["db_path"])
    cur = conn.cursor()
    cur.execute("SELECT id,date,name FROM meetings WHERE file_name=?", (entry.get("file_name"),))
    row = cur.fetchone()
    conn.close()
    return {
        "id": entry.get("id"),
        "committee_date": row[1],
        "committee_name": row[2],
        "topic_intro": anonymize_QA(json.loads(entry.get("topic_intro")), config),
        "QA": anonymize_QA(json.loads(entry.get("QA")), config),
        "eval_target": "◆"
    }

def anonymize_QA(QA: List[dict], config: Dict[str, Any]):
    anonymized_QA = []
    anonymizer = Anonymizer(config.get("pii_files"))
    for speech in QA:
        anonymized_speech = {
            "mark": speech.get("mark"),
            "role": speech.get("role"),
            "comment": anonymizer.anonymize_comment(speech.get("comment")),
        }
        anonymized_QA.append(anonymized_speech)
    return anonymized_QA
