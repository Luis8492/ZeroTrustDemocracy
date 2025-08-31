import html
import re
import urllib
import time

from playwright.sync_api import Playwright

from .BaseMinuteFetcher import BaseMinuteFetcher


class SetagayaFetcher(BaseMinuteFetcher):
    def set_search_setting_and_click_search(self, page) -> None:
        frame = page.frame(name="TOP")
        if not frame:
            raise RuntimeError("TOP iframe が見つかりませんでした")
        frame.locator("tr:nth-child(2) > td:nth-child(2) > input").first.uncheck()
        frame.locator("tr:nth-child(2) > td:nth-child(2) > input:nth-child(2)").uncheck()
        frame.locator("tr:nth-child(2) > td:nth-child(2) > input:nth-child(3)").check()
        frame.get_by_role("button", name="検索実行").click()
        time.sleep(2)

    def extract_minutes_urls(self, page):
        frame = page.frame(name="BOTTOM")
        if not frame:
            raise RuntimeError("iframe が見つかりませんでした")
        links = frame.locator("a[onclick^='winopen']").all()
        urls = []
        for link in links:
            onclick_attr = link.get_attribute("onclick")
            match = re.search(r"winopen\('([^']+)'", onclick_attr)
            if match:
                raw_url = match.group(1)
                html_decoded_url = html.unescape(raw_url)
                full_url = urllib.parse.urljoin(frame.url, html_decoded_url)
                urls.append(full_url)
        return urls

    def download_new_minutes(self, conn, context, url):
        if self.is_url_downloaded(conn, url):
            print(f"[SKIP] Already downloaded: {url}")
        else:
            detail_page = context.new_page()
            detail_page.goto(url)
            self._set_download_settings(detail_page)
            file_name = self._download_minute(detail_page)
            self.mark_as_downloaded(conn, url, file_name)
            print(f"[DONE] Downloaded: {url} → {file_name}")
            detail_page.close()

    def _set_download_settings(self, detail_page):
        detail_page.locator("frame[name=\"sidebar_head\"]").content_frame.get_by_role("radio", name="テキスト").check()
        detail_page.locator("frame[name=\"sidebar\"]").content_frame.locator("#all_check_b").check()

    def _download_minute(self, detail_page):
        with detail_page.expect_download() as download_info:
            detail_page.locator("frame[name=\"sidebar_head\"]").content_frame.get_by_role(
                "button", name="ダウンロード・印刷"
            ).click()
        download = download_info.value
        page_url = detail_page.url
        file_name = "raw_minutes/" + re.sub(r"\W+", "_", page_url[-14:]) + ".txt"
        download.save_as(file_name)
        return file_name
