from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Tuple
import sqlite3, random, json, re, sys
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent))
from config_loader import load, load_global, available_municipalities
from anonymizer import Anonymizer


def validate_municipality(name: str) -> str:
    if name not in available_municipalities():
        raise HTTPException(status_code=400, detail="Unsupported municipality")
    return name


def load_party_table(path: str) -> Dict[str, str]:
    import csv

    with open(path, encoding="utf-8") as f:
        return {"".join(row["Name"].split()): row["Party"] for row in csv.DictReader(f)}


def party_from_metadata(metadata: str | None, questioner: str) -> str:
    if not metadata:
        return ""
    try:
        data = json.loads(metadata)
    except json.JSONDecodeError:
        return ""

    party = (data or {}).get("questioner_party")
    if party:
        recorded_name = (data or {}).get("questioner_name")
        if not recorded_name or _normalize_name(recorded_name) == _normalize_name(questioner):
            return party

    display = (data or {}).get("questioner_display")
    if isinstance(display, str):
        match = re.match(r"(?P<name>[^（]+)（(?P<party>.+)）", display)
        if match:
            return match.group("party").strip()
    return ""


def _normalize_name(name: str) -> str:
    return "".join(name.split())


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
def get_next_qa(data: EvaledRequest, municipality: str = Query("setagaya")):
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

@app.get("/api/qa")
def get_qa_by_uuid(uuid: str = Query(...), municipality: str = Query("setagaya")):
    try:
        municipality = validate_municipality(municipality)
        config = load(municipality)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    qa = get_QA_by_uuid(uuid, config)
    if qa is None:
        raise HTTPException(status_code=404, detail="QA not found")
    return format_QA(qa, config)

@app.post("/api/qa/meta")
def get_qa_meta(data: EvaledRequest, municipality: str = Query("setagaya")):
    if not data.evaled_ids:
        return []
    try:
        municipality = validate_municipality(municipality)
        config = load(municipality)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    party_table: Dict[str, str] = {}
    party_table_path = config.get("party_table_path")
    if party_table_path:
        party_table = load_party_table(party_table_path)

    conn = sqlite3.connect(config["db_path"])
    cur = conn.cursor()
    query = f"""
        SELECT q.id, q.uuid, q.questioner, q.topic_intro, q.QA, m.name, m.date, helper.metadata
        FROM questions q
        JOIN meetings m ON q.file_name = m.file_name
        LEFT JOIN minutes mi ON q.file_name = mi.file_name
        LEFT JOIN downloaded_minutes_url_helper helper ON mi.url = helper.url
        WHERE q.id IN ({','.join('?' for _ in data.evaled_ids)})
    """
    cur.execute(query, data.evaled_ids)
    metas = []
    for row in cur.fetchall():
        questioner = row[2]
        metadata = row[7]
        party = party_table.get(questioner, "") if party_table else ""
        if not party:
            party = party_from_metadata(metadata, questioner)
        metas.append(
            {
                "id": row[0],
                "uuid": row[1],
                "questioner": questioner,
                "questioner_party": party,
                "topic_intro": json.loads(row[3]),
                "QA": json.loads(row[4]),
                "committee_name": row[5],
                "committee_date": row[6],
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
    cur.execute("SELECT id,uuid,file_name,topic_intro,QA FROM questions WHERE id=?", (qa_id,))
    row = cur.fetchone()
    conn.close()
    return {
        "id": qa_id,
        "uuid": row[1],
        "file_name":row[2],
        "topic_intro": row[3],
        "QA": row[4]
    }

def get_QA_by_uuid(qa_uuid: str, config: Dict[str, Any]) -> Dict[str, Any] | None:
    conn = sqlite3.connect(config["db_path"])
    cur = conn.cursor()
    cur.execute("SELECT id,uuid,file_name,topic_intro,QA FROM questions WHERE uuid=?", (qa_uuid,))
    row = cur.fetchone()
    conn.close()
    if row is None:
        return None
    return {
        "id": row[0],
        "uuid": row[1],
        "file_name": row[2],
        "topic_intro": row[3],
        "QA": row[4],
    }

def format_QA(entry: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    conn = sqlite3.connect(config["db_path"])
    cur = conn.cursor()
    cur.execute("SELECT id,date,name FROM meetings WHERE file_name=?", (entry.get("file_name"),))
    row = cur.fetchone()
    conn.close()
    return {
        "id": entry.get("id"),
        "uuid": entry.get("uuid"),
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
