"""Fetcher implementation for Setagaya regular session meeting minutes."""

import re
import urllib.parse
import sqlite3
from typing import Iterable

from app.municipal_modules.base import BaseMinuteFetcher
from app.municipal_modules.setagaya2.parsers.setagaya2_parser import Setagaya2Parser
from utils.logger import get_logger

logger = get_logger(__name__)


class Setagaya2Fetcher(BaseMinuteFetcher):
    """Fetcher implementation for Setagaya regular session meeting minutes."""

    FETCHER_NAME = Setagaya2Parser.FETCHER_NAME

    def _navigate_to_results_page(self, page) -> None:
        """Navigate from the top page to the results listing page.

        The top page contains a link labelled "定例会・臨時会の結果" which
        leads to the page listing the results of regular and extraordinary
        sessions. This method clicks that link and waits until the browser
        has navigated to the expected results page under ``/gikai/teirei/``.
        """

        page.get_by_role("link", name="定例会・臨時会の結果").click()
        page.wait_for_url(
            re.compile(r"https://www\.city\.setagaya\.lg\.jp/gikai/teirei/.*")
        )

    def extract_minutes_urls(self, page, conn: sqlite3.Connection | None = None) -> dict[str, list[str]]:
        """Collect representative and general question URLs keyed by session URL."""
        QUESTION_LABELS: Iterable[str] = ("代表質問", "一般質問")

        self._navigate_to_results_page(page)

        session_links = page.locator("ul.idx_menu li a").all()
        session_map: dict[str, list[str]] = {}
        seen: set[str] = set()

        for link in session_links:
            href = link.get_attribute("href")
            if not href:
                continue
            session_url = urllib.parse.urljoin(page.url, href)
            if conn and self.is_parent_url_processed(conn, session_url):
                logger.info(f"[SKIP] Season already processed: {session_url}")
                continue

            session_page = page.context.new_page()
            collected: list[str] = []
            try:
                session_page.goto(session_url)

                for label in QUESTION_LABELS:
                    locator = session_page.get_by_role("link", name=label)
                    if locator.count() == 0:
                        continue
                    detail_href = locator.first.get_attribute("href")
                    if not detail_href:
                        continue
                    detail_url = urllib.parse.urljoin(session_page.url, detail_href)
                    if detail_url in seen:
                        continue
                    seen.add(detail_url)
                    collected.append(detail_url)
            finally:
                session_page.close()

            session_map[session_url] = collected

        return session_map

    def _ensure_helper_table(self, conn: sqlite3.Connection) -> None:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS downloaded_minutes_url_helper (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE
            )
            """
        )
        conn.commit()

    def is_parent_url_processed(self, conn: sqlite3.Connection, url: str) -> bool:
        self._ensure_helper_table(conn)
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM downloaded_minutes_url_helper WHERE url = ?", (url,)
        )
        return cur.fetchone() is not None

    def mark_parent_url_processed(self, conn: sqlite3.Connection, url: str) -> None:
        self._ensure_helper_table(conn)
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO downloaded_minutes_url_helper (url) VALUES (?)",
            (url,),
        )
        conn.commit()

    def run(self) -> None:
        self._prepare_os_directories()
        conn = sqlite3.connect(self.config["db_path"])
        browser = self.playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(self.config["fetch_url"])
        session_map = self.extract_minutes_urls(page, conn)
        for season_url, urls in session_map.items():
            for url in urls:
                self.download_new_minutes(conn, context, url)
            self.mark_parent_url_processed(conn, season_url)
        conn.close()
        browser.close()

    def download_new_minutes(self, conn, context, url):
        """Download new minute files and register them in the database."""
        if self.is_url_downloaded(conn, url):
            logger.info(f"[SKIP] Already downloaded: {url}")
            return None
        for attempt in range(3):
            page = None
            try:
                page = context.new_page()
                page.goto(url)
                content = page.content()
                sanitized = re.sub(r"\W+", "_", url[-50:])
                file_path = self.raw_minutes_dir / f"{self.FETCHER_NAME}_{sanitized}.html"
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.mark_as_downloaded(conn, url, str(file_path), fetcher_name=self.FETCHER_NAME)
                logger.info(f"[DONE] Downloaded: {url} → {file_path}")
                return {"url": url, "path": str(file_path)}
            except Exception as e:
                logger.error(f"Error downloading {url} (attempt {attempt+1}/3): {e}")
                if attempt == 2:
                    raise
            finally:
                if page:
                    page.close()
        return None
