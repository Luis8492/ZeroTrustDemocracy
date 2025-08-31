import sqlite3
import os, re
import json
import sys
from pathlib import Path

import minute_converter
from parsers.base_minute_parser import BaseMinuteParser
from parsers.setagaya_parser import SetagayaParser

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config_loader import load


def analyze_unprocessed_minutes(
    municipality: str = "setagaya", parser: BaseMinuteParser | None = None
):
    if parser is None:
        parser = get_parser(municipality)
    config = load(municipality)
    conn = sqlite3.connect(config["db_path"])
    cur = conn.cursor()
    rows = query_not_analyzed_data(cur)
    print(f"[INFO] 未分析のファイル数: {len(rows)}")
    for minute_id, file_name in rows:
        file_path = "raw_minutes/" + file_name
        if not os.path.exists(file_path):
            print(f"[WARN] ファイルが見つかりません: {file_path}")
            continue
        try:
            minute_json = analyze_minute(file_path, parser)
            save_minute_to_db(minute_json, conn)
            update_analyzed_status(conn, cur, minute_id)
        except Exception as e:
            print(f"[ERROR] 分析失敗（ID={minute_id}）: {e}")

    conn.close()

def query_not_analyzed_data(cur):
    cur.execute("SELECT id, file_name FROM minutes WHERE analyzed = 0")
    return cur.fetchall()

def analyze_minute(file_path: str, parser: BaseMinuteParser) -> dict:
    minute_text = open(file_path, "r", encoding="cp932", errors="replace").read()
    minute_json = minute_converter.convert_minute_txt_to_json(minute_text, parser)
    minute_json["file_name"] = file_path.split("/")[-1]
    minute_json["QAs"] = extract_QAs(minute_json)
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

def get_topic_intro_and_body(topic):
    topic_intro = []
    topic_rest = []
    found_first_question = False
    for speech in topic["speeches"]:
        if not found_first_question and speech["mark"] == "◆":
            found_first_question = True
            topic_rest.append(speech)
        elif found_first_question:
            topic_rest.append(speech)
        else:
            topic_intro.append(speech)
    return topic_intro, topic_rest

def build_state_transition_log(topic_body, speech_index):
    transition_log = ""
    for i in range(speech_index):
        transition_log += topic_body[i]["mark"]
    return transition_log

def extract_QAs(minute):
    minute_QAs=[]
    for topic in minute["topics"]:
        QAs = []
        intro, topic_body = get_topic_intro_and_body(topic)
        QAs.append(intro)
        QA_sequence = []
        state = "start"
        for speech_index in range(len(topic_body)):
            if state=="start":
                if topic_body[speech_index]["mark"] != "◆":
                    transition_log = build_state_transition_log(topic_body, speech_index)
                    raise RuntimeError("Start時にmarkが◆でないことは想定されていません。["+transition_log+"]")
                elif topic_body[speech_index+1]["mark"] == "◎":
                    new_state = "QA"+topic_body[speech_index]["name"]
                    QAs.append(QA_sequence)
                    QA_sequence = [topic_body[speech_index]]
                    state = new_state
                elif topic_body[speech_index+1]["mark"] == "◆":
                    new_state = "party_comments"
                    QAs.append(QA_sequence)
                    QA_sequence = [topic_body[speech_index]]
                    state = new_state
                else:
                    transition_log = build_state_transition_log(topic_body, speech_index+1)
                    print(f"[ERROR] 元議事録ファイル: {minute.get('file_name', '')}")
                    print(
                        f"[ERROR] 当該シークエンスの最初: {json.dumps(topic_body[speech_index], ensure_ascii=False)}"
                    )
                    raise RuntimeError("Unknown state transition.("+state+">?)["+transition_log+"]")
            elif state[:2] == "QA":
                if topic_body[speech_index]["mark"] != "○":
                    if topic_body[speech_index]["mark"] == "◆":
                        if topic_body[speech_index]["name"] != state[2:]:
                            new_state = "QA"+topic_body[speech_index]["name"]
                            QAs.append(QA_sequence)
                            QA_sequence = [topic_body[speech_index]]
                            state = new_state
                        else:
                            QA_sequence.append(topic_body[speech_index])
                    else:
                        QA_sequence.append(topic_body[speech_index])
                else:
                    for i in range(speech_index,len(topic_body)): # i+1>lenの判定をしていない。
                        if topic_body[i]["mark"] == "◆":
                            if i+1<len(topic_body):
                                if topic_body[i+1]["mark"] == "◆":
                                    new_state = "party_comments"
                                    QAs.append(QA_sequence)
                                    QAs.append([topic_body[i]])
                                    QAs.append([topic_body[i+1]])
                                    QA_sequence=[]
                                    speech_index = i+1
                                    state = new_state
                                    break
                                elif topic_body[i+1]["mark"] == "◎":
                                    if topic_body[i]["name"] == state[2:]:
                                        QA_sequence.append(topic_body[i])
                                        QA_sequence.append(topic_body[i+1])
                                        speech_index = i+1
                                        break
                                    else:
                                        new_state = "QA"+topic_body[i]["name"]
                                        QAs.append(QA_sequence)
                                        QA_sequence=[topic_body[i],topic_body[i+1]]
                                        speech_index = i+1
                                        state = new_state
                                        break
                                else:
                                    transition_log = build_state_transition_log(topic_body, i+1)
                                    print(
                                        f"[ERROR] 元議事録ファイル: {minute.get('file_name', '')}"
                                    )
                                    print(
                                        f"[ERROR] 当該シークエンスの最初: {json.dumps(topic_body[speech_index], ensure_ascii=False)}"
                                    )
                                    raise RuntimeError("Unknown state transition.("+state+">?)["+transition_log+"]")
                            else:
                                break
                        else:
                            QA_sequence.append(topic_body[speech_index])
            elif state == "party_comments":
                if topic_body[speech_index]["mark"] == "◆":
                    QAs.append(QA_sequence)
                    QA_sequence=[topic_body[speech_index]]
                else:
                    break
            else:
                transition_log = build_state_transition_log(topic_body, speech_index+1)
                raise RuntimeError("Unknown state. ("+state+")["+transition_log+"]")
        QAs.append(QA_sequence)
        minute_QAs.append(QAs)
    return minute_QAs

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

analyze_unprocessed_minutes()
