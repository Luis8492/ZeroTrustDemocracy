import html,re,urllib
from playwright.sync_api import Playwright, sync_playwright, expect
import sqlite3,os,time

def run(playwright: Playwright) -> None:
    prepare_os_dirctories()
    conn = sqlite3.connect("db/minutes.db")
    init_db(conn)
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://kugi.city.setagaya.tokyo.jp/voices/")
    set_search_setting_and_click_search(page)
    urls = extract_minutes_urls(page)
    for url in urls:
        download_new_minutes(conn,context,url)
    conn.close()
    browser.close()

def prepare_os_dirctories():
    os.makedirs("db", exist_ok=True)
    os.makedirs("raw_minutes", exist_ok=True)

def init_db(conn):
    cur = conn.cursor()
    cur.execute("""
CREATE TABLE IF NOT EXISTS minutes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE,
    file_name TEXT,
    analyzed INTEGER
)
""")
    conn.commit()

def set_search_setting_and_click_search(page):
    frame = page.frame(name="TOP")
    if not frame:
        raise RuntimeError("TOP iframe が見つかりませんでした")
    frame.locator("tr:nth-child(2) > td:nth-child(2) > input").first.uncheck()
    frame.locator("tr:nth-child(2) > td:nth-child(2) > input:nth-child(2)").uncheck()
    frame.locator("tr:nth-child(2) > td:nth-child(2) > input:nth-child(3)").check()
    frame.get_by_role("button", name="検索実行").click()
    time.sleep(2)

def extract_minutes_urls(page):
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

def download_new_minutes(conn,context,url):
    if is_url_downloaded(conn, url):
         print(f"[SKIP] Already downloaded: {url}")
    else:
        detail_page = context.new_page()
        detail_page.goto(url)
        set_download_settings(detail_page)
        file_name = download_minute(detail_page)
        mark_as_downloaded(conn, url, file_name)
        print(f"[DONE] Downloaded: {url} → {file_name}")
        detail_page.close()

def is_url_downloaded(conn, url):
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM minutes WHERE url = ?", (url,))
    return cur.fetchone() is not None

def set_download_settings(detail_page):
    detail_page.locator("frame[name=\"sidebar_head\"]").content_frame.get_by_role("radio", name="テキスト").check()
    detail_page.locator("frame[name=\"sidebar\"]").content_frame.locator("#all_check_b").check()

def download_minute(detail_page):
    with detail_page.expect_download() as download_info:
        detail_page.locator("frame[name=\"sidebar_head\"]").content_frame.get_by_role("button", name="ダウンロード・印刷").click()
    download = download_info.value
    file_name = "raw_minutes/" + re.sub(r'\W+', '_', detail_page.url[-14:]) + ".txt"
    download.save_as(file_name)
    return file_name

def mark_as_downloaded(conn, url, file_path):
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO minutes (url, file_name, analyzed) VALUES (?, ?, 0)",
        (url, file_path.split('/')[-1])
    )
    conn.commit()

with sync_playwright() as playwright:
    run(playwright)
