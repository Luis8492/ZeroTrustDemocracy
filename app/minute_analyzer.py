import sqlite3
import os, re
import json
import sys
from pathlib import Path

# Ensure repository root is on the Python path before importing modules outside `app`
sys.path.append(str(Path(__file__).resolve().parent.parent))

import minute_converter
from app.municipal_modules.base.base_minute_parser import BaseMinuteParser
from app.municipal_modules.setagaya.parsers.setagaya_parser import SetagayaParser
from app.municipal_modules.setagaya.fetchers import SetagayaFetcher
from config_loader import load
from utils.logger import get_logger

logger = get_logger(__name__)


def analyze_unprocessed_minutes(
    municipality: str = "setagaya",
    parser: BaseMinuteParser | None = None,
    fetcher_name: str = SetagayaFetcher.FETCHER_NAME,
):
    if parser is None:
        parser = get_parser(municipality)
    config = load(municipality)
    conn = sqlite3.connect(config["db_path"])
    cur = conn.cursor()
    rows = query_not_analyzed_data(cur, fetcher_name)
    logger.info(f"[INFO] 未分析のファイル数: {len(rows)}")
    for minute_id, file_name in rows:
        file_path = "raw_minutes/" + file_name
        if not os.path.exists(file_path):
            logger.warning(f"[WARN] ファイルが見つかりません: {file_path}")
            continue
        try:
            minute_json = analyze_minute(file_path, parser)
            save_minute_to_db(minute_json, conn)
            update_analyzed_status(conn, cur, minute_id)
        except Exception as e:
            message = f"[ERROR] 分析失敗（ID={minute_id}）: {e}"
            logger.error(message)
            print(message)

    conn.close()

def query_not_analyzed_data(cur, fetcher_name: str):
    cur.execute(
        "SELECT id, file_name FROM minutes WHERE fetcher = ? AND analyzed = 0",
        (fetcher_name,),
    )
    return cur.fetchall()

def analyze_minute(file_path: str, parser: BaseMinuteParser) -> dict:
    minute_text = open(file_path, "r", encoding="cp932", errors="replace").read()
    minute_json = minute_converter.convert_minute_txt_to_json(minute_text, parser)
    minute_json["file_name"] = file_path.split("/")[-1]
    minute_json["QAs"] = parser.extract_QAs(minute_json)
    return minute_json


def get_parser(municipality: str) -> BaseMinuteParser:
    if municipality == "setagaya":
        return SetagayaParser()
    raise ValueError(f"Unsupported municipality: {municipality}")

def update_analyzed_status(conn,cur,minute_id):
    cur.execute(
        "UPDATE minutes SET analyzed = 1 WHERE id = ?",
        (minute_id,)
    )
    conn.commit()


def save_minute_to_db(minute_json,conn):
    save_meta_info(minute_json,conn)
    save_QAs(minute_json,conn)

def save_meta_info(minute, conn):
    file_name = minute["file_name"]
    date = minute["meeting"]["date"]
    name = minute["meeting"]["name"]
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO meetings (file_name, date, name) VALUES (?, ?, ?)",
        (file_name,date,name)
    )
    conn.commit()

def save_QAs(minute,conn):
    file_name = minute["file_name"]
    cur = conn.cursor()
    for topic in minute["QAs"]:
        intro=""
        for QA in topic:
            if intro=="":
                intro=json.dumps(QA,indent=4,ensure_ascii=False)
            else:
                # if there is no entry with speech["mark"]=="◆", skip the QA
                questioner=""
                for speech in QA:
                    if speech["mark"]=="◆":
                        questioner = speech["name"]
                        break
                if questioner == "":
                    # Skip QA sequences with no question mark
                    continue
                QA_text = json.dumps(QA,indent=4,ensure_ascii=False)
                cur.execute(
                    "INSERT OR IGNORE INTO questions (file_name, topic_intro, QA, questioner) VALUES (?, ?, ?, ?)",
                    (file_name,intro,QA_text,questioner)
                )
    conn.commit()

analyze_unprocessed_minutes(fetcher_name=SetagayaFetcher.FETCHER_NAME)
