import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / 'db' / 'minutes.db'
SETAGAYA_ID = 13112


def add_column_and_set_value(conn, table: str):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cur.fetchall()]
    if 'municipality_id' not in columns:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN municipality_id INTEGER")
    cur.execute(f"UPDATE {table} SET municipality_id = ?", (SETAGAYA_ID,))
    conn.commit()


def main():
    conn = sqlite3.connect(DB_PATH)
    add_column_and_set_value(conn, 'meetings')
    add_column_and_set_value(conn, 'questions')
    conn.close()


if __name__ == '__main__':
    main()
