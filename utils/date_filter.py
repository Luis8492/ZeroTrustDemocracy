"""Date-based recency filtering for fetched meeting minutes.

Used to limit the data scope to a recent window (default: 4 years) so that
the fetcher does not pull or process minutes that are no longer relevant
for the published service.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Optional


DEFAULT_MAX_AGE_YEARS = 4


def _reiwa_to_western(reiwa_year: int) -> int:
    """令和X年 → 西暦 (令和元年 = 2019年)."""
    return 2018 + reiwa_year


def _heisei_to_western(heisei_year: int) -> int:
    """平成X年 → 西暦 (平成元年 = 1989年)."""
    return 1988 + heisei_year


def cutoff_date(
    max_age_years: int = DEFAULT_MAX_AGE_YEARS,
    today: Optional[date] = None,
) -> date:
    """Return the oldest date that should still be considered in-scope."""
    if today is None:
        today = date.today()
    try:
        return today.replace(year=today.year - max_age_years)
    except ValueError:
        # Feb 29 on a non-leap target year
        return today.replace(month=2, day=28, year=today.year - max_age_years)


_COMMITTEE_UNID_RE = re.compile(r"UNID=k?_?R(\d{2})(\d{2})(\d{2})", re.IGNORECASE)


def parse_committee_url_date(url: str) -> Optional[date]:
    """Extract the meeting date from a Setagaya committee minute URL.

    Committee URLs end with ``UNID=k_R<YY><MM><DD>...`` where ``R`` denotes
    the 令和 era. Returns ``None`` if the pattern is not present or the date
    components are invalid.
    """
    if not url:
        return None
    m = _COMMITTEE_UNID_RE.search(url)
    if not m:
        return None
    yy, mm, dd = (int(g) for g in m.groups())
    try:
        return date(_reiwa_to_western(yy), mm, dd)
    except ValueError:
        return None


_REIWA_YEAR_RE = re.compile(r"令和\s*(元|\d+)\s*年")
_HEISEI_YEAR_RE = re.compile(r"平成\s*(元|\d+)\s*年")


def _era_token_to_int(token: str) -> int:
    return 1 if token == "元" else int(token)


def parse_label_year(text: str) -> Optional[int]:
    """Extract the Western-calendar year from a Japanese era-formatted label.

    Recognises ``令和X年`` and ``平成X年`` (with optional spacing and the
    ``元`` first-year marker). Returns ``None`` if no era pattern matches.
    """
    if not text:
        return None
    m = _REIWA_YEAR_RE.search(text)
    if m:
        return _reiwa_to_western(_era_token_to_int(m.group(1)))
    m = _HEISEI_YEAR_RE.search(text)
    if m:
        return _heisei_to_western(_era_token_to_int(m.group(1)))
    return None


_COMMITTEE_DATE_RE = re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日")


def parse_meeting_date_string(text: str) -> Optional[date]:
    """Extract the first ``YYYY年M月D日`` date in *text*.

    Used by the analyzer / exporter to interpret stored ``meetings.date``
    values such as ``2026年03月27日02号``. Returns ``None`` if no Western
    date is present (e.g. era-formatted strings — combine with
    :func:`parse_label_year` for those).
    """
    if not text:
        return None
    m = _COMMITTEE_DATE_RE.search(text)
    if not m:
        return None
    y, mo, d = (int(g) for g in m.groups())
    try:
        return date(y, mo, d)
    except ValueError:
        return None


def is_within_cutoff(target: Optional[date], cutoff: date) -> bool:
    """``True`` if *target* is on/after *cutoff*. Unknown dates pass through."""
    if target is None:
        return True
    return target >= cutoff


def is_year_within_cutoff(year: Optional[int], cutoff: date) -> bool:
    """``True`` if *year* could contain dates on/after *cutoff*."""
    if year is None:
        return True
    return year >= cutoff.year
