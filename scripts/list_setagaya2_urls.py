"""Temporary script to print Setagaya regular session question URLs."""

from playwright.sync_api import sync_playwright

from app.municipal_modules.setagaya2.fetchers.Setagaya2Fetcher import (
    Setagaya2Fetcher,
)


def main() -> None:
    with sync_playwright() as p:
        fetcher = Setagaya2Fetcher(p, "setagaya2")
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.city.setagaya.lg.jp/gikai/")
        urls = fetcher.extract_minutes_urls(page)
        for url in urls:
            print(url)
        browser.close()


if __name__ == "__main__":
    main()
