from datetime import date

from utils.date_filter import (
    cutoff_date,
    is_within_cutoff,
    is_year_within_cutoff,
    parse_committee_url_date,
    parse_label_year,
    parse_meeting_date_string,
)


def test_cutoff_date_default_subtracts_four_years():
    assert cutoff_date(today=date(2026, 5, 14)) == date(2022, 5, 14)


def test_cutoff_date_handles_feb_29():
    assert cutoff_date(today=date(2024, 2, 29)) == date(2020, 2, 29)
    # leap-day target landing on a non-leap year clamps to Feb 28
    assert cutoff_date(max_age_years=1, today=date(2024, 2, 29)) == date(2023, 2, 28)


def test_parse_committee_url_date_extracts_reiwa_date():
    url = (
        "https://kugi.city.setagaya.tokyo.jp/voices/CGI/voiweb.exe?"
        "ACT=200&UNID=k_R08031844014"
    )
    assert parse_committee_url_date(url) == date(2026, 3, 18)


def test_parse_committee_url_date_returns_none_for_unknown():
    assert parse_committee_url_date("") is None
    assert parse_committee_url_date("https://example.com/no-unid") is None
    # Invalid date components
    assert parse_committee_url_date("UNID=k_R08139944014") is None


def test_parse_label_year_handles_reiwa_and_heisei():
    assert parse_label_year("令和8年第1回区議会定例会") == 2026
    assert parse_label_year("令和元年第3回定例会") == 2019
    assert parse_label_year("平成31年第1回定例会") == 2019
    assert parse_label_year("") is None
    assert parse_label_year("特に年号なし") is None


def test_parse_meeting_date_string_handles_committee_format():
    assert parse_meeting_date_string("2026年03月27日02号") == date(2026, 3, 27)
    assert parse_meeting_date_string("2025年10月8日") == date(2025, 10, 8)
    assert parse_meeting_date_string("") is None
    assert parse_meeting_date_string("令和8年") is None  # era format not handled here


def test_is_within_cutoff_pass_through_for_unknown():
    cutoff = date(2022, 5, 14)
    assert is_within_cutoff(None, cutoff) is True
    assert is_within_cutoff(date(2022, 5, 14), cutoff) is True
    assert is_within_cutoff(date(2022, 5, 13), cutoff) is False
    assert is_within_cutoff(date(2026, 1, 1), cutoff) is True


def test_is_year_within_cutoff_uses_year_only():
    cutoff = date(2022, 5, 14)
    assert is_year_within_cutoff(None, cutoff) is True
    assert is_year_within_cutoff(2022, cutoff) is True  # any 2022 date could qualify
    assert is_year_within_cutoff(2021, cutoff) is False
    assert is_year_within_cutoff(2026, cutoff) is True
