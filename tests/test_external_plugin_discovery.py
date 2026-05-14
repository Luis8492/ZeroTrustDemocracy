"""Verify MUNICIPAL_MODULES_PATH lets the framework load plugins from outside
the bundled ``app/municipal_modules`` tree — the property the submodule
operating model depends on.
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def external_plugin(tmp_path, monkeypatch):
    """Mirror the recommended private-repo layout::

        <project_root>/
        ├── municipal_modules/        <- MUNICIPAL_MODULES_PATH points here
        │   └── external_assembly/
        │       ├── __init__.py
        │       └── config/external_assembly.yaml
        ├── db/        (created by analyzer)
        └── raw_minutes/  (created by fetcher)
    """
    project_root = tmp_path / "project"
    plugin_dir = project_root / "municipal_modules"
    pkg = plugin_dir / "external_assembly"
    (pkg / "config").mkdir(parents=True)
    (pkg / "config" / "external_assembly.yaml").write_text(
        textwrap.dedent(
            """\
            db_path: db/external_assembly.db
            raw_minutes_dir: raw_minutes/external_assembly
            pii_files: []

            fetchers:
              ExternalFetcher:
                fetch_url: external://noop
                encoding: utf-8
            """
        ),
        encoding="utf-8",
    )
    (pkg / "__init__.py").write_text(
        textwrap.dedent(
            """\
            from app.municipal_modules.base.base_minute_parser import BaseMinuteParser


            class ExternalParser(BaseMinuteParser):
                FETCHER_NAME = "ExternalFetcher"

                def convert(self, text):
                    return {"meeting": {"date": "", "name": ""}, "topics": [], "QAs": []}


            PARSERS = {ExternalParser.FETCHER_NAME: ExternalParser}
            """
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("MUNICIPAL_MODULES_PATH", str(plugin_dir))
    monkeypatch.delenv("CONFIG_DIR", raising=False)

    for mod_name in [
        "app.municipal_modules",
        "config_loader",
        "external_assembly",
    ]:
        sys.modules.pop(mod_name, None)

    yield project_root, "external_assembly"

    sys.modules.pop("external_assembly", None)


def test_external_plugin_appears_in_discovery(external_plugin):
    _, name = external_plugin
    from app.municipal_modules import load_parsers_by_municipality

    grouped = load_parsers_by_municipality()
    assert name in grouped
    assert "ExternalFetcher" in grouped[name]


def test_external_plugin_visible_to_available_municipalities(external_plugin):
    _, name = external_plugin
    from config_loader import available_municipalities

    assert name in available_municipalities()


def test_external_plugin_paths_resolve_against_project_root(external_plugin):
    project_root, name = external_plugin
    from config_loader import load

    data = load(name)
    expected = project_root.resolve()
    assert Path(data["raw_minutes_dir"]).resolve() == expected / "raw_minutes" / name
    assert Path(data["db_path"]).resolve() == expected / "db" / f"{name}.db"
