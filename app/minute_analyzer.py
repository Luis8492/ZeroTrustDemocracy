from __future__ import annotations

import argparse
import sqlite3
import os
import json
import sys
import uuid
from pathlib import Path

# Ensure repository root is on the Python path before importing modules outside `app`
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.municipal_modules.base.base_minute_parser import BaseMinuteParser
from app.municipal_modules import load_parsers_by_municipality
from config_loader import load, load_for_fetcher
from utils.db import ensure_schema
from utils.logger import get_logger

logger = get_logger(__name__)

# {municipality: {fetcher_name: parser_class}}
PARSERS_BY_MUNICIPALITY = load_parsers_by_municipality()


def analyze_unprocessed_minutes(
    municipality: str,
    parser: BaseMinuteParser | None = None,
    fetcher_name: str | None = None,
):
    """Analyze all unprocessed minute files for ``municipality``.

    If ``parser`` is supplied, only that parser's fetcher is processed (legacy
    single-session entry point). Otherwise every (fetcher, parser) pair known
    for the municipality is processed against rows tagged with the matching
    ``minutes.fetcher`` value.
    """
    config = load(municipality)
    conn = sqlite3.connect(config["db_path"])
    ensure_schema(conn)

    if parser is not None:
        pairs = [(fetcher_name or getattr(parser, "FETCHER_NAME"), parser)]
    else:
        parsers = PARSERS_BY_MUNICIPALITY.get(municipality) or {}
        if not parsers:
            raise ValueError(f"No parsers registered for municipality: {municipality}")
        pairs = [(fn, cls()) for fn, cls in parsers.items()]

    for fname, parser_obj in pairs:
        fetcher_config = load_for_fetcher(municipality, fname)
        encoding = fetcher_config.get("encoding", "utf-8")
        cur = conn.cursor()
        rows = query_not_analyzed_data(cur, fname)
        logger.info(f"[INFO] {fname}: 未分析のファイル数 {len(rows)}")
        for minute_id, file_name in rows:
            file_path = "raw_minutes/" + file_name
            if not os.path.exists(file_path):
                logger.warning(f"[WARN] ファイルが見つかりません: {file_path}")
                continue
            try:
                minute_json = analyze_minute(file_path, parser_obj, encoding=encoding)
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
    """Return *any* parser registered for ``municipality``.

    Kept for legacy callers that assume one parser per municipality. Modules
    with multiple sessions return whichever parser ``dict.values()`` yields
    first; new code should iterate ``PARSERS_BY_MUNICIPALITY[municipality]``
    explicitly.
    """
    parsers = PARSERS_BY_MUNICIPALITY.get(municipality)
    if not parsers:
        raise ValueError(f"Unsupported municipality: {municipality}")
    return next(iter(parsers.values()))()

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
    minute_uuid = _get_minute_uuid(conn, file_name)
    for topic_index, topic in enumerate(minute["QAs"]):
        intro=""
        for qa_index, QA in enumerate(topic):
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
                qa_uuid = _generate_qa_uuid(minute_uuid, topic_index, qa_index)
                cur.execute(
                    "INSERT OR IGNORE INTO questions (uuid, file_name, topic_intro, QA, questioner) VALUES (?, ?, ?, ?, ?)",
                    (qa_uuid, file_name, intro, QA_text, questioner)
                )
    conn.commit()


def _get_minute_uuid(conn: sqlite3.Connection, file_name: str) -> str:
    cur = conn.cursor()
    cur.execute(
        "SELECT uuid FROM minutes WHERE file_name = ? ORDER BY id DESC LIMIT 1",
        (file_name,),
    )
    row = cur.fetchone()
    if row and row[0]:
        return row[0]
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"legacy:{file_name}"))


def _generate_qa_uuid(minute_uuid: str, topic_index: int, qa_index: int) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{minute_uuid}:{topic_index}:{qa_index}"))


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

    municipalities = args.municipality or list(PARSERS_BY_MUNICIPALITY.keys())
    for muni in municipalities:
        if muni not in PARSERS_BY_MUNICIPALITY:
            raise ValueError(f"Unsupported municipality: {muni}")
        analyze_unprocessed_minutes(muni)


if __name__ == "__main__":
    main()
