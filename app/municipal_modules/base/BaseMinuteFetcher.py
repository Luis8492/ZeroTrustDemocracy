"""Base classes for downloading municipal meeting minutes."""

import json
import sqlite3
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from config_loader import load
from utils.db import ensure_schema
from utils.logger import get_logger


logger = get_logger(__name__)


class BaseMinuteFetcher(ABC):
    """Common workflow for downloading raw meeting minutes."""

    def __init__(self, playwright, municipality: str):
        self.playwright = playwright
        self.municipality = municipality
        self.config = load(municipality)
        self.raw_minutes_dir = Path(__file__).resolve().parents[2] / "raw_minutes"

    def run(self) -> None:
        self._prepare_os_directories()
        conn = sqlite3.connect(self.config["db_path"])
        ensure_schema(conn)
        browser = self.playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(self.config["fetch_url"])
        urls = self.extract_minutes_urls(page, conn)
        for url in urls:
            self.download_new_minutes(conn, context, url)
        conn.close()
        browser.close()

    def _prepare_os_directories(self) -> None:
        Path(self.config["db_path"]).parent.mkdir(parents=True, exist_ok=True)
        self.raw_minutes_dir.mkdir(parents=True, exist_ok=True)

    def is_url_downloaded(self, conn: sqlite3.Connection, url: str) -> bool:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM minutes WHERE url = ?", (url,))
        return cur.fetchone() is not None

    def mark_as_downloaded(
        self,
        conn: sqlite3.Connection,
        url: str,
        file_path: str,
        fetcher_name: str,
    ) -> None:
        minute_uuid = self._generate_minute_uuid(url, fetcher_name)
        cur = conn.cursor()
        cur.execute(
            """
INSERT INTO minutes (uuid, url, file_name, fetcher, analyzed)
VALUES (?, ?, ?, ?, 0)
ON CONFLICT(url) DO UPDATE SET
    file_name=excluded.file_name,
    fetcher=excluded.fetcher,
    uuid=excluded.uuid
""",
            (minute_uuid, url, Path(file_path).name, fetcher_name),
        )
        conn.commit()

    # ------------------------------------------------------------------
    # Helper table utilities
    # ------------------------------------------------------------------

    def _ensure_helper_table(self, conn: sqlite3.Connection) -> None:
        """Create the helper table if it does not exist and ensure columns."""

        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS downloaded_minutes_url_helper (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,
                metadata TEXT
            )
            """
        )
        columns = {row[1] for row in cur.execute("PRAGMA table_info(downloaded_minutes_url_helper)")}
        if "metadata" not in columns:
            cur.execute(
                "ALTER TABLE downloaded_minutes_url_helper ADD COLUMN metadata TEXT"
            )
        conn.commit()

    def upsert_helper_metadata(
        self, conn: sqlite3.Connection, url: str, metadata: dict[str, Any] | None
    ) -> None:
        """Insert or update helper metadata for a downloaded minute URL."""

        self._ensure_helper_table(conn)
        metadata_json = (
            json.dumps(metadata, ensure_ascii=False) if metadata is not None else None
        )
        logger.info(
            "[HELPER][UPSERT] url=%s metadata=%s",
            url,
            metadata if metadata is not None else "<none>",
        )
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO downloaded_minutes_url_helper (url, metadata)
            VALUES (?, ?)
            ON CONFLICT(url) DO UPDATE SET metadata=excluded.metadata
            """,
            (url, metadata_json),
        )
        conn.commit()

    def is_helper_url_recorded(self, conn: sqlite3.Connection, url: str) -> bool:
        """Check whether the helper table already contains ``url``."""

        self._ensure_helper_table(conn)
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM downloaded_minutes_url_helper WHERE url = ?",
            (url,),
        )
        return cur.fetchone() is not None

    @staticmethod
    def _generate_minute_uuid(url: str, fetcher_name: str) -> str:
        """Generate a deterministic UUID based on URL and fetcher name."""

        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{fetcher_name}:{url}"))

    @abstractmethod
    def extract_minutes_urls(self, page, conn: sqlite3.Connection | None = None):
        pass

    @abstractmethod
    def download_new_minutes(self, conn: sqlite3.Connection, context, url: str) -> None:
        pass
