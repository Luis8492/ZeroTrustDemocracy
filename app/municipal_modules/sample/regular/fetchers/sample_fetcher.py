"""Local-file fetcher for the synthetic 'sample' assembly.

A real fetcher subclass drives Playwright to scrape a live web page. The
sample fetcher instead copies bundled fixtures into ``raw_minutes_dir`` and
registers them in the ``minutes`` table, so the rest of the pipeline
(analyzer, exporter, frontend) can run end-to-end without any network.

The abstract ``extract_minutes_urls`` / ``download_new_minutes`` are stubbed
out because ``run`` is overridden to skip the Playwright workflow entirely.
"""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

from app.municipal_modules.base.BaseMinuteFetcher import BaseMinuteFetcher
from utils.db import ensure_schema
from utils.logger import get_logger

logger = get_logger(__name__)


class SampleFetcher(BaseMinuteFetcher):
    FETCHER_NAME = "SampleFetcher"
    REQUIRES_PLAYWRIGHT = False

    def __init__(self, playwright=None, municipality: str = "sample"):
        super().__init__(playwright, municipality)
        self.fixtures_dir = Path(__file__).resolve().parents[1] / "samples"

    def run(self) -> None:
        self._prepare_os_directories()
        conn = sqlite3.connect(self.config["db_path"])
        ensure_schema(conn)
        try:
            fixtures = sorted(self.fixtures_dir.glob("*.txt"))
            if not fixtures:
                logger.warning(
                    "[sample] no fixtures found under %s", self.fixtures_dir
                )
                return
            for fixture in fixtures:
                dest = self.raw_minutes_dir / fixture.name
                shutil.copyfile(fixture, dest)
                synthetic_url = f"sample://fixtures/{fixture.name}"
                self.mark_as_downloaded(
                    conn, synthetic_url, str(dest), self.FETCHER_NAME
                )
                logger.info("[sample] staged %s", fixture.name)
        finally:
            conn.close()

    def extract_minutes_urls(self, page, conn: sqlite3.Connection | None = None):
        return []

    def download_new_minutes(self, conn: sqlite3.Connection, context, url: str) -> None:
        return None
