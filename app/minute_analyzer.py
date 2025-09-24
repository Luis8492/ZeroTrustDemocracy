from __future__ import annotations

import argparse
import sqlite3
import os
import json
import sys
from pathlib import Path

# Ensure repository root is on the Python path before importing modules outside `app`
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.municipal_modules.base.base_minute_parser import BaseMinuteParser
from app.municipal_modules import load_parsers
from config_loader import load
from utils.db import ensure_schema
from utils.logger import get_logger

logger = get_logger(__name__)

# Load parser classes available in municipal_modules
PARSER_CLASSES = load_parsers()


def analyze_unprocessed_minutes(
    municipality: str,
    parser: BaseMinuteParser | None = None,
    fetcher_name: str | None = None,
):
    if parser is None:
        parser = get_parser(municipality)
    if fetcher_name is None:
        fetcher_name = getattr(parser, "FETCHER_NAME")
    config = load(municipality)
    encoding = config.get("encoding", "cp932")
    conn = sqlite3.connect(config["db_path"])
    ensure_schema(conn)
    cur = conn.cursor()
    rows = query_not_analyzed_data(cur, fetcher_name)
    logger.info(f"[INFO] 未分析のファイル数: {len(rows)}")
    for minute_id, file_name in rows:
        file_path = "raw_minutes/" + file_name
        if not os.path.exists(file_path):
            logger.warning(f"[WARN] ファイルが見つかりません: {file_path}")
            continue
        try:
            minute_json = analyze_minute(file_path, parser, encoding=encoding)
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


def analyze_minute(
    file_path: str, parser: BaseMinuteParser, *, encoding: str = "cp932"
) -> dict:
    minute_text = Path(file_path).read_text(encoding=encoding, errors="replace")
    minute_json = parser.convert(minute_text)
    minute_json["file_name"] = file_path.split("/")[-1]
    return minute_json


def get_parser(municipality: str) -> BaseMinuteParser:
    parser_cls = PARSER_CLASSES.get(municipality)
    if parser_cls is None:
        raise ValueError(f"Unsupported municipality: {municipality}")
    return parser_cls()

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
    participants = minute["meeting"].get("participants", [])
    participants_text = json.dumps(participants, ensure_ascii=False)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO meetings (file_name, date, name, participants) VALUES (?, ?, ?, ?)",
        (file_name, date, name, participants_text)
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
                    # Skip QA sequences with no questioner mark (◆)
                    continue
                QA_text = json.dumps(QA,indent=4,ensure_ascii=False)
                cur.execute(
                    "INSERT OR IGNORE INTO questions (file_name, topic_intro, QA, questioner) VALUES (?, ?, ?, ?)",
                    (file_name,intro,QA_text,questioner)
                )
    conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze unprocessed minutes for municipalities"
    )
    parser.add_argument(
        "--municipality",
        nargs="*",
        help="Target municipality(ies). If omitted, all available municipalities are processed.",
    )
    args = parser.parse_args()

    municipalities = args.municipality or list(PARSER_CLASSES.keys())
    for muni in municipalities:
        parser_cls = PARSER_CLASSES.get(muni)
        if parser_cls is None:
            raise ValueError(f"Unsupported municipality: {muni}")
        analyze_unprocessed_minutes(muni, parser_cls(), parser_cls.FETCHER_NAME)


if __name__ == "__main__":
    main()
