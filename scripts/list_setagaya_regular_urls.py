"""Temporary script to print Setagaya regular session question URLs."""

from playwright.sync_api import sync_playwright

from app.municipal_modules.setagaya.regular.fetchers.setagaya_regular_fetcher import (
    SetagayaRegularFetcher,
)


def main() -> None:
    with sync_playwright() as p:
        fetcher = SetagayaRegularFetcher(p, "setagaya")
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.city.setagaya.lg.jp/gikai/")
        session_map = fetcher.extract_minutes_urls(page)
        for urls in session_map.values():
            for url in urls:
                print(url)
        browser.close()


if __name__ == "__main__":
    main()
