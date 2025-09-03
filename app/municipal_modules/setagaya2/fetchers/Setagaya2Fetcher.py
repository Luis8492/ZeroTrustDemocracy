"""Fetcher implementation for Setagaya regular session meeting minutes."""

import re

from app.municipal_modules.base import BaseMinuteFetcher
from utils.logger import get_logger

logger = get_logger(__name__)


class Setagaya2Fetcher(BaseMinuteFetcher):
    """Fetcher implementation for Setagaya regular session meeting minutes."""

    FETCHER_NAME = "SetagayaRegularFetcher"

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

    def extract_minutes_urls(self, page):
        """Extract minute page URLs from the search results."""
        self._navigate_to_results_page(page)
        raise NotImplementedError("URL extraction logic is not implemented.")

    def download_new_minutes(self, conn, context, url):
        """Download new minute files and register them in the database."""
        raise NotImplementedError("Download logic is not implemented.")
