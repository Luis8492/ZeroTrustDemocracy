import sys
import shutil
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.municipal_modules import load_parsers, load_parsers_by_municipality


def test_load_parsers_skips_failing_modules():
    base = Path(__file__).resolve().parent.parent / "app" / "municipal_modules"
    broken = base / "broken"
    (broken / "parsers").mkdir(parents=True, exist_ok=True)
    (broken / "__init__.py").write_text("")
    (broken / "parsers" / "__init__.py").write_text("")
    (broken / "parsers" / "bad_parser.py").write_text(
        "raise RuntimeError('boom')\n"
    )

    try:
        flat = load_parsers()
        grouped = load_parsers_by_municipality()

        # Flat mapping is keyed by fetcher_name now that one municipality can
        # host multiple sessions.
        assert "SampleFetcher" in flat
        assert "sample" in grouped
        assert "broken" not in grouped
    finally:
        shutil.rmtree(broken)
