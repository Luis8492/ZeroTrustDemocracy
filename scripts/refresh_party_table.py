"""Refresh the plugin's name→party CSV from parser-extracted data in the DB.

Rationale: parsers that surface ``questioner_party`` in their speech output
(today: setagaya regular) record the 会派 that was active at the time of the
meeting — i.e. the authoritative period-correct value. Plugins that *don't*
extract party from source (today: setagaya committee) fall back to the static
``party_table_path`` CSV during ``export_static_data``. If we let the CSV
go stale, those committee QAs end up labelled with whichever 会派 a member
*used to* belong to.

This script closes the loop: it reads every ``questions.questioner_party``
that the analyzer wrote, picks the most recent assignment per member, and
merges it into the CSV in-place. Existing rows for members never seen in the
parser-extracted data are preserved (no destructive deletion).

Run order is therefore::

    analyze   → questions.questioner_party populated for parsers that extract
    refresh   → name-party-table.csv updated from latest analyzer signal
    export    → committee/etc. fall back to a fresh CSV
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import re
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(REPO_ROOT))

from config_loader import load  # noqa: E402
from utils.date_filter import parse_label_year, parse_meeting_date_string  # noqa: E402


def _normalize_name(name: str) -> str:
    return "".join((name or "").split())


# Era-format dates look like "令和6年2月20日～3月27日". Lexicographic
# comparison of those strings goes wrong inside the same year (the substring
# "6月" sorts AFTER "11月" because '6' > '1'), so we extract era year + first
# month/day and return a proper ``date``.
_ERA_MONTH_DAY_RE = re.compile(r"年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日")


def _meeting_sort_key(raw: str) -> _dt.date:
    """Best-effort chronological key for ``meetings.date`` strings.

    Handles two formats produced by the bundled fetchers:

    - Committee (Western): ``"2025年12月05日02号"`` — delegated to
      :func:`parse_meeting_date_string`.
    - Regular (era): ``"令和6年2月20日～3月27日"`` — needs year (from era) +
      first month/day extracted manually.

    Unknown strings sort first (``date.min``) so they lose to any parsable
    sibling without raising.
    """
    if not raw:
        return _dt.date.min
    parsed = parse_meeting_date_string(raw)
    if parsed is not None:
        return parsed
    year = parse_label_year(raw)
    if year is not None:
        m = _ERA_MONTH_DAY_RE.search(raw)
        if m:
            try:
                return _dt.date(year, int(m.group(1)), int(m.group(2)))
            except ValueError:
                pass
        # No month/day → sort as 1月1日 of that year. Still strictly worse
        # than any dated sibling in the same year.
        return _dt.date(year, 1, 1)
    return _dt.date.min


def latest_party_per_member(db_path: str) -> Dict[str, Tuple[str, str, _dt.date]]:
    """Return ``{normalized_name: (display_name, party, latest_meeting_date)}``.

    Only rows whose ``questioner_party`` is non-empty are considered — those
    are the ones the parser found a 会派 for. Where the same person appears
    in multiple meetings with different parties, the most recent meeting wins
    (sorted via :func:`_meeting_sort_key`, which handles both the Western and
    era-formatted ``meetings.date`` values).
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT q.questioner, q.questioner_party, m.date
        FROM questions q
        JOIN meetings m ON q.file_name = m.file_name
        WHERE COALESCE(q.questioner_party, '') != ''
          AND COALESCE(q.questioner, '') != ''
        """
    ).fetchall()
    conn.close()

    latest: Dict[str, Tuple[str, str, _dt.date]] = {}
    for r in rows:
        name = r["questioner"]
        key = _normalize_name(name)
        party = (r["questioner_party"] or "").strip()
        meeting_date = _meeting_sort_key(r["date"] or "")
        existing = latest.get(key)
        if existing is None or meeting_date > existing[2]:
            latest[key] = (name, party, meeting_date)
    return latest


def merge_into_csv(csv_path: Path, fresh: Dict[str, Tuple[str, str, str]]) -> Dict[str, int]:
    """In-place merge of ``fresh`` into ``csv_path``.

    Preserves existing rows whose member isn't in ``fresh``. For names that
    appear in both, the party is replaced; the existing Name spelling is
    kept (so casing/spacing in the CSV doesn't churn).
    """
    existing_rows: List[Dict[str, str]] = []
    if csv_path.exists():
        with csv_path.open(encoding="utf-8", newline="") as f:
            existing_rows = list(csv.DictReader(f))

    by_key: Dict[str, Dict[str, str]] = {
        _normalize_name(row.get("Name", "")): dict(row) for row in existing_rows
    }

    updated = 0
    added = 0
    for key, (display_name, party, _meeting_date) in fresh.items():
        if key in by_key:
            if by_key[key].get("Party") != party:
                by_key[key]["Party"] = party
                updated += 1
        else:
            by_key[key] = {"Name": display_name, "Party": party}
            added += 1

    # Stable sort by Name for human-friendly diffs.
    final_rows = sorted(by_key.values(), key=lambda r: r.get("Name", ""))

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Name", "Party"])
        writer.writeheader()
        for row in final_rows:
            writer.writerow({"Name": row.get("Name", ""), "Party": row.get("Party", "")})

    return {"updated": updated, "added": added, "total": len(final_rows)}


def refresh(municipality: str) -> Dict[str, int]:
    config = load(municipality)
    db_path = config["db_path"]
    csv_path = config.get("party_table_path")
    if not csv_path:
        raise ValueError(
            f"{municipality}: party_table_path not configured — nothing to refresh"
        )
    fresh = latest_party_per_member(db_path)
    stats = merge_into_csv(Path(csv_path), fresh)
    stats["from_parser"] = len(fresh)
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--municipality", default="sample")
    args = parser.parse_args()
    stats = refresh(args.municipality)
    print(
        f"refresh-party-table: parser→{stats['from_parser']} members, "
        f"csv updated={stats['updated']} added={stats['added']} "
        f"total={stats['total']}"
    )


if __name__ == "__main__":
    main()
