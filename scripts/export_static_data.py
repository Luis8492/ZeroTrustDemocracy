"""Export SQLite QA data to static JSON files for Cloudflare Pages hosting.

Produces, under ``<out>/data/``:

- ``index.json``    — every QA with the minimal fields needed for client-side
                      weighted random selection and history rendering.
- ``meetings/<file_name>.json``
                    — full anonymized payload for one meeting.

Anonymization (PII redaction) and party resolution are applied at export time
so the runtime is purely static.
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(REPO_ROOT))
sys.path.append(str(REPO_ROOT / "app"))

from anonymizer import Anonymizer  # noqa: E402
from config_loader import load  # noqa: E402


def _default_out() -> Path:
    """Default export root. Overridden by ``EXPORT_OUTPUT_DIR`` env var.

    The default points at ``frontend/public`` inside the framework repo so
    ``npm run dev`` picks the data up. External runners (e.g. a private
    operations repo) set ``EXPORT_OUTPUT_DIR`` to point at their own
    ``frontend_data/`` or ``dist/`` directory.
    """
    env_value = os.getenv("EXPORT_OUTPUT_DIR")
    if env_value:
        return Path(env_value).expanduser()
    return REPO_ROOT / "frontend" / "public"


DEFAULT_OUT = _default_out()


def _normalize_name(name: str) -> str:
    return "".join((name or "").split())


def load_party_table(path: Optional[str]) -> Dict[str, str]:
    if not path:
        return {}
    with open(path, encoding="utf-8") as f:
        return {_normalize_name(row["Name"]): row["Party"] for row in csv.DictReader(f)}


def party_from_metadata(metadata: Optional[str], questioner: str) -> str:
    if not metadata:
        return ""
    try:
        data = json.loads(metadata)
    except json.JSONDecodeError:
        return ""

    party = (data or {}).get("questioner_party")
    if party:
        recorded = (data or {}).get("questioner_name")
        if not recorded or _normalize_name(recorded) == _normalize_name(questioner):
            return party

    display = (data or {}).get("questioner_display")
    if isinstance(display, str):
        match = re.match(r"(?P<name>[^（]+)（(?P<party>.+)）", display)
        if match:
            return match.group("party").strip()
    return ""


def anonymize_speeches(speeches: List[dict], anonymizer: Anonymizer) -> List[dict]:
    out = []
    for s in speeches or []:
        out.append(
            {
                "mark": s.get("mark"),
                "role": s.get("role"),
                "comment": anonymizer.anonymize_comment(s.get("comment") or ""),
            }
        )
    return out


def strip_suffix(file_name: str) -> str:
    return file_name[:-4] if file_name.endswith(".txt") else file_name


def export(municipality: str, out_root: Path) -> Dict[str, int]:
    config = load(municipality)
    db_path = config["db_path"]

    anonymizer = Anonymizer(config.get("pii_files"))
    party_table = load_party_table(config.get("party_table_path"))

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        """
        SELECT q.id, q.uuid, q.questioner, q.questioner_party,
               q.topic_intro, q.QA,
               m.file_name, m.date, m.name,
               helper.metadata
        FROM questions q
        JOIN meetings m ON q.file_name = m.file_name
        LEFT JOIN minutes mi ON q.file_name = mi.file_name
        LEFT JOIN downloaded_minutes_url_helper helper ON mi.url = helper.url
        ORDER BY m.date, q.id
        """
    )
    rows = cur.fetchall()
    conn.close()

    meetings: Dict[str, Dict[str, Any]] = {}
    index_entries: List[Dict[str, Any]] = []

    for row in rows:
        questioner = row["questioner"] or ""
        # Priority: parser-extracted party (period-correct, from the meeting's
        # own heading) > static CSV lookup > URL-helper metadata. The parser
        # path is preferred because it reflects the 会派 at the time of the
        # meeting even if the representative later switched factions.
        party = (row["questioner_party"] or "").strip()
        if not party:
            party = party_table.get(_normalize_name(questioner), "")
        if not party:
            party = party_from_metadata(row["metadata"], questioner)

        slug = strip_suffix(row["file_name"])

        try:
            topic_intro_raw = json.loads(row["topic_intro"]) if row["topic_intro"] else []
            qa_raw = json.loads(row["QA"]) if row["QA"] else []
        except json.JSONDecodeError as e:
            print(f"WARN: failed to parse QA payload id={row['id']}: {e}", file=sys.stderr)
            continue

        qa_entry = {
            "id": row["id"],
            "uuid": row["uuid"],
            "questioner": questioner,
            "questioner_party": party,
            "topic_intro": anonymize_speeches(topic_intro_raw, anonymizer),
            "QA": anonymize_speeches(qa_raw, anonymizer),
            "eval_target": "◆",
        }

        meeting = meetings.setdefault(
            slug,
            {
                "file_name": slug,
                "committee_date": row["date"],
                "committee_name": row["name"],
                "qas": [],
            },
        )
        meeting["qas"].append(qa_entry)

        index_entries.append(
            {
                "id": row["id"],
                "uuid": row["uuid"],
                "questioner": questioner,
                "questioner_party": party,
                "file_name": slug,
                "committee_date": row["date"],
                "committee_name": row["name"],
            }
        )

    out_dir = out_root / "data"
    meetings_dir = out_dir / "meetings"
    meetings_dir.mkdir(parents=True, exist_ok=True)

    existing = {p.name for p in meetings_dir.glob("*.json")}
    written = set()
    for slug, payload in meetings.items():
        target = meetings_dir / f"{slug}.json"
        target.write_text(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        written.add(target.name)

    for stale in existing - written:
        (meetings_dir / stale).unlink()

    index_payload = {
        "municipality": municipality,
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "qa_count": len(index_entries),
        "meeting_count": len(meetings),
        "qas": index_entries,
    }
    data_sources = config.get("data_sources")
    if data_sources:
        index_payload["data_sources"] = data_sources
    (out_dir / "index.json").write_text(
        json.dumps(index_payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    return {"qas": len(index_entries), "meetings": len(meetings)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--municipality", default="sample")
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"output root (default: {DEFAULT_OUT})",
    )
    args = parser.parse_args()
    stats = export(args.municipality, args.out)
    print(
        f"exported {stats['qas']} QAs across {stats['meetings']} meetings → {args.out}/data"
    )


if __name__ == "__main__":
    main()
