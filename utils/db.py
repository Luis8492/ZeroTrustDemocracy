"""Database utility helpers for ensuring application schema."""

from __future__ import annotations

from sqlite3 import Connection


SCHEMA_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS minutes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uuid TEXT UNIQUE,
        url TEXT UNIQUE,
        file_name TEXT,
        fetcher TEXT NOT NULL,
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
        uuid TEXT UNIQUE,
        file_name TEXT,
        topic_intro TEXT,
        QA TEXT,
        questioner TEXT,
        questioner_party TEXT
    )
    """,
)


def ensure_schema(conn: Connection) -> None:
    """Ensure that the SQLite database has the expected schema."""

    cur = conn.cursor()
    for statement in SCHEMA_STATEMENTS:
        cur.execute(statement)
    _ensure_columns(
        conn,
        "minutes",
        {
            "uuid": "TEXT UNIQUE",
        },
    )
    _ensure_columns(
        conn,
        "questions",
        {
            "uuid": "TEXT UNIQUE",
            "questioner_party": "TEXT",
        },
    )
    conn.commit()


def _ensure_columns(conn: Connection, table: str, columns: dict[str, str]) -> None:
    cur = conn.cursor()
    existing = {row[1] for row in cur.execute(f"PRAGMA table_info({table})")}
    for column, definition in columns.items():
        if column not in existing:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
