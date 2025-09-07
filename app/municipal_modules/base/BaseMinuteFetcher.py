"""Base classes for downloading municipal meeting minutes."""

import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path

from config_loader import load


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
        cur = conn.cursor()
        cur.execute(
            """
INSERT INTO minutes (url, file_name, fetcher, analyzed)
VALUES (?, ?, ?, 0)
ON CONFLICT(url) DO UPDATE SET
    file_name=excluded.file_name,
    fetcher=excluded.fetcher
""",
            (url, Path(file_path).name, fetcher_name),
        )
        conn.commit()

    @abstractmethod
    def extract_minutes_urls(self, page, conn: sqlite3.Connection | None = None):
        pass

    @abstractmethod
    def download_new_minutes(self, conn: sqlite3.Connection, context, url: str) -> None:
        pass
