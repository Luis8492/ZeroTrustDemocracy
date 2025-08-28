import sqlite3
import os,re
import json

def convert_minute_txt_to_json(text):
    minute_json = {}
    minute_json["meeting"] = _extract_meeting_data(text)
    minute_json["topics"] = _extract_topic_data(text)
    return minute_json

def _extract_meeting_data(text):
    lines = text.splitlines()
    for line in lines:
        match = re.match(r"^\[\s*令和\s*(\d+)\s*年\s*(\d+)月\s*(.+?)－(\d+)月(\d+)日-(\d+)号", line)
        if match:
            era_year = int(match.group(1))
            month = int(match.group(2))
            name = match.group(3).strip()
            western_year = 2018 + era_year  # 令和元年 = 2019年
            day_month = f"{match.group(4)}月{match.group(5)}日{match.group(6)}号"
            date = f"{western_year}年{day_month}"
            return {
                "date": date,
                "name": name
            }
    raise ValueError("会議名と日付の行が見つかりませんでした")

def _extract_topic_data(text):
    topics = []
    for i, topic_section in enumerate(_extract_topic_section(text), start=1):
        speeches = _extract_speeches(topic_section)
        topics.append({
            "topic_id": i,
            "raw": topic_section,
            "speeches":speeches
        })
    return topics

def _extract_topic_section(text):
    parts = re.split(r"^\s*━{10,}\s*$", text, flags=re.MULTILINE)
    if len(parts) <= 1:
        raise ValueError("トピックの区切りが見つかりませんでした")
    return [part.strip() for part in parts[1:]]

def _extract_speeches(topic_text):
    lines = topic_text.splitlines()
    speeches = []
    current_speech = None
    speech_id = 1
    speaker_pattern = re.compile(r"^([○◆◎])([^\s　]+)[　\s]+([^\s　]+)[　\s]+(.+)")
    for line in lines:
        line = line.strip()
        if not line:
            continue
        match = speaker_pattern.match(line)
        if match:
            if current_speech:
                speeches.append(current_speech)
                speech_id += 1
            mark, name, role, comment = match.groups()
            current_speech = {
                "id": speech_id,
                "mark": mark,
                "name": name,
                "role": role,
                "comment": comment,
                "raw": line
            }
        else:
            if current_speech:
                current_speech["comment"] += "\n" + line
                current_speech["raw"] += "\n" + line
            else:
                pass
    if current_speech:
        speeches.append(current_speech)
    return speeches
