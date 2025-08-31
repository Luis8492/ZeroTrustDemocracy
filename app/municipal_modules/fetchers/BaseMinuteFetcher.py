"""Base classes for downloading municipal meeting minutes."""

import os
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

    def run(self) -> None:
        self._prepare_os_directories()
        conn = sqlite3.connect(self.config["db_path"])
        browser = self.playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(self.config["fetch_url"])
        self.set_search_setting_and_click_search(page)
        urls = self.extract_minutes_urls(page)
        for url in urls:
            self.download_new_minutes(conn, context, url)
        conn.close()
        browser.close()

    def _prepare_os_directories(self) -> None:
        Path(self.config["db_path"]).parent.mkdir(parents=True, exist_ok=True)
        os.makedirs("raw_minutes", exist_ok=True)

    def is_url_downloaded(self, conn: sqlite3.Connection, url: str) -> bool:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM minutes WHERE url = ?", (url,))
        return cur.fetchone() is not None

    def mark_as_downloaded(self, conn: sqlite3.Connection, url: str, file_path: str) -> None:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO minutes (url, file_name, analyzed) VALUES (?, ?, 0)",
            (url, file_path.split('/')[-1]),
        )
        conn.commit()

    @abstractmethod
    def set_search_setting_and_click_search(self, page) -> None:
        pass

    @abstractmethod
    def extract_minutes_urls(self, page) -> list[str]:
        pass

    @abstractmethod
    def download_new_minutes(self, conn: sqlite3.Connection, context, url: str) -> None:
        pass
