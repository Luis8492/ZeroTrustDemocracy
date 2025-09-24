"""Database utility helpers for ensuring application schema."""

from __future__ import annotations

from sqlite3 import Connection


SCHEMA_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS minutes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE,
        file_name TEXT,
        fetcher TEXT NOT NULL DEFAULT "SetagayaCommitteeFetcher",
        analyzed INTEGER NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS meetings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name TEXT,
        date TEXT,
        name TEXT,
        participants TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS downloaded_minutes_url_helper (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE,
        metadata TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name TEXT,
        topic_intro TEXT,
        QA TEXT,
        questioner TEXT
    )
    """,
)


def ensure_schema(conn: Connection) -> None:
    """Ensure that the SQLite database has the expected schema."""

    cur = conn.cursor()
    for statement in SCHEMA_STATEMENTS:
        cur.execute(statement)
    conn.commit()
