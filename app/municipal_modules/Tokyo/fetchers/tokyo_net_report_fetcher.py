"""Fetcher for the Tokyo Metropolitan Assembly net report."""

from __future__ import annotations

from collections import deque
from html.parser import HTMLParser
import re
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple
from urllib.parse import urljoin, urlparse

from playwright.sync_api import Page

from app.municipal_modules.base import BaseMinuteFetcher
from utils.logger import get_logger


logger = get_logger(__name__)


class _HrefCollector(HTMLParser):
    """Simple HTML parser to collect anchor href attributes."""

    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:  # type: ignore[override]
        if tag.lower() != "a":
            return
        for attr, value in attrs:
            if attr.lower() == "href" and value:
                self.hrefs.append(value)


class TokyoNetReportFetcher(BaseMinuteFetcher):
    """Fetcher implementation for the Tokyo Metropolitan Assembly net report."""

    FETCHER_NAME = "tokyo_net_report"

    def extract_minutes_urls(self, page: Page, conn=None) -> List[str]:  # type: ignore[override]
        context = page.context
        index_queue: deque[Tuple[str, str]] = deque([(page.url, page.content())])
        visited_index_pages: set[str] = set()
        year_links: list[str] = []

        while index_queue:
            current_url, html = index_queue.popleft()
            if current_url in visited_index_pages:
                continue
            visited_index_pages.add(current_url)

            year_candidates, archive_links = self._parse_index_page(current_url, html)
            year_links.extend(link for link in year_candidates if link not in year_links)

            for archive_url in archive_links:
                if archive_url in visited_index_pages:
                    continue
                logger.info("[TOKYO] Visiting archive index: %s", archive_url)
                archive_page = context.new_page()
                try:
                    archive_page.goto(archive_url)
                    archive_html = archive_page.content()
                finally:
                    archive_page.close()
                index_queue.append((archive_url, archive_html))

        member_urls: list[str] = []
        seen_members: set[str] = set()
        for year_url in year_links:
            logger.info("[TOKYO] Processing session page: %s", year_url)
            for member_url in self._collect_member_links(context, year_url):
                if member_url not in seen_members:
                    seen_members.add(member_url)
                    member_urls.append(member_url)
        return member_urls

    def download_new_minutes(self, conn, context, url: str) -> None:  # type: ignore[override]
        if self.is_url_downloaded(conn, url):
            logger.info("[TOKYO][SKIP] Already downloaded: %s", url)
            return

        logger.info("[TOKYO] Downloading: %s", url)
        detail_page = context.new_page()
        try:
            detail_page.goto(url)
            detail_page.wait_for_load_state("load")
            content = detail_page.content()
        finally:
            detail_page.close()

        file_path = self._save_minute_html(url, content)
        self.mark_as_downloaded(conn, url, file_path, fetcher_name=self.FETCHER_NAME)
        logger.info("[TOKYO][DONE] Saved to %s", file_path)

    def _parse_index_page(self, page_url: str, html: str) -> Tuple[list[str], list[str]]:
        collector = _HrefCollector()
        collector.feed(html)

        year_links: list[str] = []
        archive_links: list[str] = []
        for href in collector.hrefs:
            if not href or href.startswith("#"):
                continue
            absolute = urljoin(page_url, href)
            if self._is_archive_link(absolute):
                archive_links.append(absolute)
            elif self._is_year_link(absolute):
                year_links.append(absolute)
        return self._deduplicate(year_links), self._deduplicate(archive_links)

    def _collect_member_links(self, context, year_url: str) -> Sequence[str]:
        session_page = context.new_page()
        try:
            session_page.goto(year_url)
            session_page.wait_for_load_state("load")
            html = session_page.content()
        finally:
            session_page.close()
        return self._parse_member_links(year_url, html)

    def _parse_member_links(self, page_url: str, html: str) -> list[str]:
        collector = _HrefCollector()
        collector.feed(html)

        member_links: list[str] = []
        for href in collector.hrefs:
            if not href or href.startswith("#"):
                continue
            absolute = urljoin(page_url, href)
            if not self._is_member_link(absolute):
                continue
            if absolute not in member_links:
                member_links.append(absolute)
        return member_links

    def _save_minute_html(self, url: str, content: str) -> str:
        parsed = urlparse(url)
        segments = [segment for segment in parsed.path.split("/") if segment]
        slug = Path(parsed.path).stem or "minute"
        parts = [self.FETCHER_NAME]
        if len(segments) >= 3:
            # ``.../netreport/<year>/<session>/<file>``
            year = segments[-3]
            session = segments[-2]
            parts.extend([year, session])
        elif len(segments) >= 2:
            parts.append(segments[-2])
        parts.append(slug)
        file_name = "_".join(parts) + ".html"
        file_path = self.raw_minutes_dir / file_name
        with file_path.open("w", encoding="utf-8") as f:
            f.write(content)
        return str(file_path)

    @staticmethod
    def _deduplicate(urls: Iterable[str]) -> list[str]:
        seen: set[str] = set()
        deduped: list[str] = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                deduped.append(url)
        return deduped

    @staticmethod
    def _is_archive_link(url: str) -> bool:
        parsed = urlparse(url)
        if "/netreport/" not in parsed.path:
            return False
        return bool(re.search(r"archive[^/]*\.html$", parsed.path, re.IGNORECASE))

    @staticmethod
    def _is_year_link(url: str) -> bool:
        parsed = urlparse(url)
        path = parsed.path
        if "/netreport/" not in path:
            return False
        segments = [seg for seg in path.split("/") if seg]
        try:
            netreport_index = segments.index("netreport")
        except ValueError:
            return False
        subsegs = segments[netreport_index + 1 :]
        if len(subsegs) < 2:
            return False
        year, report = subsegs[0], subsegs[1]
        if not year.isdigit() or len(year) != 4:
            return False
        if not report.startswith("report"):
            return False
        if len(subsegs) > 2 and subsegs[2] not in {"", "index.html"}:
            return False
        return True

    @staticmethod
    def _is_member_link(url: str) -> bool:
        parsed = urlparse(url)
        if "/netreport/" not in parsed.path:
            return False
        if not parsed.path.endswith(".html"):
            return False
        file_name = Path(parsed.path).name
        if file_name == "index.html":
            return False
        return bool(re.fullmatch(r"\d+\.html", file_name))
