import argparse
from playwright.sync_api import sync_playwright

from app.municipal_modules.fetchers import SetagayaFetcher

FETCHERS = {
    "setagaya": SetagayaFetcher,
}


def main():
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
