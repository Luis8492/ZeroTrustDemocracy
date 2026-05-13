import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.municipal_modules.setagaya.regular.dev.pattern_classifier import (
    classify_files,
    classify_pattern,
)


def test_classify_pattern_variants():
    pattern1_html = (
        "<ul><li>Topic<ul><li><strong>質問</strong>Q</li>"
        "<li><strong>答弁</strong>A</li></ul></li></ul>"
    )
    pattern2_html = (
        "<ul><li><strong>Topic<br>質問</strong>Q<br><strong>答弁</strong>A</li></ul>"
    )
    pattern3_html = (
        "<ul><li><strong>Topic</strong><br><strong>質問</strong>Q"
        "<br><strong>答弁</strong>A</li></ul>"
    )
    assert classify_pattern(pattern1_html) == "Pattern1"
    assert classify_pattern(pattern2_html) == "Pattern2"
    assert classify_pattern(pattern3_html) == "Pattern3"
    assert classify_pattern("<li>no match</li>") == "Unknown"


def test_classify_real_files():
    base = Path("app/raw_minutes")
    files = [
        base
        / "SetagayaRegularFetcher_https_www_city_setagaya_lg_jp_02030_9739_html.html",
        base
        / "SetagayaRegularFetcher_https_www_city_setagaya_lg_jp_02030_11415_html.html",
        base
        / "SetagayaRegularFetcher_https_www_city_setagaya_lg_jp_02030_20655_html.html",
    ]
    assert classify_files(files) == ["Pattern1", "Pattern2", "Pattern3"]
