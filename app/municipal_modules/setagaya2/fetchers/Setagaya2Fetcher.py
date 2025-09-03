"""Fetcher implementation for Setagaya regular session meeting minutes."""

from app.municipal_modules.base import BaseMinuteFetcher
from utils.logger import get_logger

logger = get_logger(__name__)


class Setagaya2Fetcher(BaseMinuteFetcher):
    """Fetcher implementation for Setagaya regular session meeting minutes."""

    FETCHER_NAME = "SetagayaRegularFetcher"

    def set_search_setting_and_click_search(self, page) -> None:
        """Set search conditions on the page and initiate search."""
        raise NotImplementedError("Search setting logic is not implemented.")

    def extract_minutes_urls(self, page):
        """Extract minute page URLs from the search results."""
        raise NotImplementedError("URL extraction logic is not implemented.")

    def download_new_minutes(self, conn, context, url):
        """Download new minute files and register them in the database."""
        raise NotImplementedError("Download logic is not implemented.")
