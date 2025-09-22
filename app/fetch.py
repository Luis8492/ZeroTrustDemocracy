import argparse
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

# Ensure repository root is importable when running as a script
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Fetchers are organized under `municipal_modules/<municipality>/fetchers`
from municipal_modules.Tokyo.fetchers import TokyoNetReportFetcher
from municipal_modules.setagaya.fetchers import SetagayaFetcher
from municipal_modules.setagaya2.fetchers import Setagaya2Fetcher

FETCHERS = {
    "setagaya": SetagayaFetcher,
    "setagaya2": Setagaya2Fetcher,
    "Tokyo": TokyoNetReportFetcher,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch minutes for a municipality")
    parser.add_argument("--municipality", required=True, help="target municipality")
    args = parser.parse_args()

    fetcher_cls = FETCHERS.get(args.municipality)
    if not fetcher_cls:
        raise ValueError(f"Unknown municipality: {args.municipality}")

    with sync_playwright() as playwright:
        fetcher = fetcher_cls(playwright, args.municipality)
        fetcher.run()


if __name__ == "__main__":
    main()

