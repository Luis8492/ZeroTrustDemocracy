from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Dict, Any
import sqlite3, random, json, csv, sys
from pathlib import Path
from anonymizer import Anonymizer
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config_loader import load

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8001"],  # フロントエンドのポートを指定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

config = load("setagata")
with open(Path(__file__).with_name("name-party-table.csv"), encoding="utf-8") as f:
    PARTY_TABLE = {"".join(row["Name"].split()): row["Party"] for row in csv.DictReader(f)}

class EvaledRequest(BaseModel):
    evaled_ids: List[int] # POSTデータ受け用

@app.post("/api/qa/next")
def get_next_qa(data: EvaledRequest):
    non_evaled_ids = extract_non_evaled_QA(data.evaled_ids)
    if not non_evaled_ids:
        return {"message": "全て評価済みです"}
    target_id = random.choice(non_evaled_ids)
    qa = get_QA_by_id(target_id)
    return format_QA(qa)

@app.post("/api/qa/meta")
def get_qa_meta(data: EvaledRequest):
    if not data.evaled_ids:
        return []
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
                "questioner_party": PARTY_TABLE.get(questioner, ""),
                "topic_intro": json.loads(row[2]),
                "QA": json.loads(row[3]),
                "committee_name": row[4],
                "committee_date": row[5],
            }
        )
    conn.close()
    return metas

def extract_non_evaled_QA(evaled_ids: List[int]) -> List[int]:
    conn = sqlite3.connect(config["db_path"])
    cur = conn.cursor()
    if evaled_ids:
        q = f"SELECT id FROM questions WHERE id NOT IN ({','.join(['?'] * len(evaled_ids))})"
        cur.execute(q, evaled_ids)
    else:
        cur.execute("SELECT id FROM questions")
    ids = [row[0] for row in cur.fetchall()]
    conn.close()
    return ids

def get_QA_by_id(qa_id: int) -> Dict[str, Any]:
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

def format_QA(entry: Dict[str, Any]) -> Dict[str, Any]:
    conn = sqlite3.connect(config["db_path"])
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
        "eval_target": "◆"
    }

def anonymize_QA(QA: List[dict]):
    anonymized_QA = []
    anonymizer = Anonymizer()
    for speech in QA:
        anonymized_speech = {
            "mark":speech.get("mark"),
            "role":speech.get("role"),
            "comment":anonymizer.anonymize_comment(speech.get("comment")),
        }
        anonymized_QA.append(anonymized_speech)
    return anonymized_QA
