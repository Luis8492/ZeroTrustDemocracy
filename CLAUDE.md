# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**ZeroTrustDemocracy** is a framework for structuring assembly minutes into question/answer pairs (QAs) and shipping them as static JSON to a Svelte frontend hosted on Cloudflare Pages; users rate QAs locally and all ratings stay client-side in IndexedDB. The "zero trust" angle is that the server never sees user evaluations — in fact there is no application server in production. Each real-assembly deployment runs a weekly GitHub Actions cron that re-fetches, re-analyzes, and re-exports.

This repository is **framework code only**. The only bundled plugin is `sample` — a synthetic reference assembly that uses local fixtures (no Playwright, no network) so the pipeline can be exercised after a fresh clone. Real assembly deployments live in **private operations repos** that import this framework as a git submodule and supply their own `municipal_modules/<name>/` plugin. See `docs/FORK_GUIDE.md` §A for the submodule layout (recommended) and the fork layout as a fallback.

## Common commands

```bash
# Install deps
pip install -r requirements.txt
playwright install chromium     # only needed when running real fetchers (sample is Playwright-free)

# Initialize the bundled sample plugin's SQLite DB
python scripts/init_db.py sample           # creates db/sample.db

# Fetch raw minutes (sample uses local fixtures; real fetchers use Playwright)
python app/fetch.py --municipality sample

# Parse fetched minutes into structured QAs in SQLite
python app/minute_analyzer.py --municipality sample   # municipality optional; processes all if omitted

# Export SQLite → static JSON (consumed by the frontend in production)
python scripts/export_static_data.py --municipality sample

# Serve the frontend (Svelte 5 + Vite) — reads static JSON from /data
cd frontend
npm install
npm run dev       # http://localhost:8001, serves frontend/public/data/* at /data

# Tests
pytest                                # run all
pytest tests/test_sample_parser.py    # single file
```

The legacy `app/feederAPI.py` (FastAPI) still exists and can be run with `python -m uvicorn app.feederAPI:app`, but the frontend no longer talks to it — production is fully static.

## Architecture

### Four-stage data pipeline
1. **Fetcher** (`app/fetch.py` → `<plugin>/fetchers/`): downloads raw text into `raw_minutes_dir` (default `app/raw_minutes/`, overridable via config YAML or `RAW_MINUTES_DIR` env), records URL + `fetcher` name + deterministic UUID in `minutes` table with `analyzed=0`. UUIDs are `uuid5(NAMESPACE_URL, f"{fetcher_name}:{url}")` — stable across re-fetches. Fetchers that don't need Playwright set `REQUIRES_PLAYWRIGHT=False` (e.g. `sample`).
2. **Analyzer** (`app/minute_analyzer.py` → `<plugin>/parsers/`): reads `analyzed=0` rows, runs the plugin's parser, writes `meetings` + `questions` rows, flips `analyzed=1`. QA UUIDs are derived from the parent minute UUID + topic/qa indices, so a re-analysis produces stable IDs.
3. **Exporter** (`scripts/export_static_data.py`): reads the DB, applies anonymization + party resolution, writes `<out>/data/index.json` (selection-time metadata, includes `data_sources` from the config YAML) + `<out>/data/meetings/<file_name>.json` (full payload per meeting). `out` defaults to `frontend/public` but is overridable via `--out` or `EXPORT_OUTPUT_DIR`.
4. **GitHub Actions** (in each private operations repo): runs stages 1–3 on its own cron. The framework repo itself only carries a CI workflow (`pytest`).

### Per-plugin layout
Each plugin lives under one of:
- **Bundled**: `app/municipal_modules/<name>/` (only `sample` ships here).
- **External**: any directory listed in `MUNICIPAL_MODULES_PATH` (OS-native separator; `;` on Windows, `:` on POSIX). Private repos use this to keep their plugin alongside their data.

Plugin contents:
- `config/<name>.yaml` — top-level shared fields (`db_path`, `raw_minutes_dir`, `pii_files`, `party_table_path`, optional `data_sources`) plus per-session overrides under `fetchers.<FETCHER_NAME>` (`fetch_url`, `encoding`)
- `__init__.py` — exports `PARSERS = {fetcher_name: parser_class}` and `FETCHERS = {fetcher_name: fetcher_class}`
- one or more **session sub-packages** (e.g. `committee/`, `regular/`), each containing `fetchers/` and `parsers/` packages
- `base/` shared classes (kept in the framework, not duplicated): `BaseMinuteFetcher`, `BaseMinuteParser`

Discovery: `app/municipal_modules/__init__.py:load_parsers_by_municipality()` and `load_fetchers_by_municipality()` import each top-level plugin package (bundled and from `MUNICIPAL_MODULES_PATH`) and read its `PARSERS` / `FETCHERS` dicts (falling back to scanning `parsers/` for legacy modules without explicit dicts). The set of municipalities the API accepts is derived at runtime by `config_loader.available_municipalities()` from `<name>/config/<name>.yaml` existence (and any `*.yaml` under `CONFIG_DIR`) — there is no hard-coded allowlist anywhere.

Config resolution for a single fetcher: `config_loader.load_for_fetcher(municipality, fetcher_name)` merges the shared top-level fields with the per-session overrides under `fetchers.<FETCHER_NAME>`, returning a flat dict. The `BaseMinuteFetcher` constructor and the analyzer both use this helper.

Minute/QA payload format (parser output, also stored as JSON strings in SQLite) is documented in `app/municipal_modules/base/README.md` — `mark` field `◆` denotes the questioner, `○` the chair, `◎` the respondent.

### Config resolution
`config_loader.py` resolves config in this priority:
1. `CONFIG_PATH` env var (absolute path to a global config YAML)
2. `CONFIG_DIR` env var (looks for `config.yaml` and `<municipality>.yaml` under that dir, also `<municipality>/<municipality>.yaml` and `<municipality>/config/<municipality>.yaml`)
3. Any plugin dir under `MUNICIPAL_MODULES_PATH`
4. Repo-root `config.yaml` and bundled `app/municipal_modules/<m>/config/<m>.yaml`

When `CONFIG_DIR` matches an external dir, relative paths inside the YAML (`db_path`, `pii_files`, `raw_minutes_dir`, etc.) are resolved against `CONFIG_DIR` instead of the repo root.

### Database
SQLite, one file per assembly (e.g. `db/sample.db`). Schema is defined in two places — `scripts/init_db.py` (initial creation) and `utils/db.py:ensure_schema` (idempotent + adds missing columns at runtime). Fetchers and the analyzer call `ensure_schema` on startup, so legacy DBs auto-upgrade. Tables:
- `minutes` — one row per downloaded URL (uuid, url, file_name, fetcher, analyzed)
- `meetings` — one row per parsed file (file_name, date, name, participants JSON)
- `questions` — one row per QA sequence (uuid, file_name, topic_intro JSON, QA JSON, questioner)
- `downloaded_minutes_url_helper` — extra metadata (e.g. `questioner_party`, `questioner_name`) keyed by minute URL, used as a fallback for party lookup when the CSV `party_table` doesn't match

### Anonymization
`Anonymizer` does naive string replacement of every line in the `pii_files` with `***`. Applied at **export time** by `scripts/export_static_data.py`, not at parse time — so raw text in `raw_minutes/` and `questions.QA` JSON inside the DB are **not** anonymized; the exported JSON under `<out>/data/` is.

### Frontend
**Svelte 5 + Vite + TypeScript**, built to `frontend/dist/` and deployed via Cloudflare Pages.

- Routing: `svelte-spa-router` hash-based (`#/`, `#/result`, `#/settings`).
- IndexedDB (`EvalDB` v2): `evaluations` store (legacy keyed by `QA_id`) + `settings` store (theme etc.).
- Themes are CSS-variable based, switched by `<html data-theme="...">`. Shipped: `plain`, `chat`, `scroll` (縦書き和紙), `hud` (SF/glassmorphism). Add a new theme by extending `src/themes/themes.css` and adding `:global([data-theme='X'])` overrides in components.
- `src/lib/api.ts` loads `/data/index.json` once and per-meeting JSON on demand from `/data/meetings/<file_name>.json`; the weighted-random "next QA" pick happens client-side. Also exposes `fetchDataSources()` which returns `index.json#data_sources`.
- `src/lib/config.ts` reads `VITE_DATA_BASE` / `VITE_MUNICIPALITY` / `VITE_ASSEMBLY_NAME` / `VITE_SITE_TAGLINE` / `VITE_PROJECT_REPO_URL` from env, so a fork can repoint and rebrand without touching code. Defaults in `frontend/.env` point at the bundled `sample`.

## Notes when extending

- New real assemblies should be added by **standing up a private operations repo** that consumes this framework as a submodule (see `docs/FORK_GUIDE.md` §A). The framework repo itself ships only the `sample` reference plugin — do not add real-assembly plugins here.
- `app/feederAPI.py` does `sys.path.append(...)` to import `config_loader` from the repo root. Always launch the API from the repo root, not from inside `app/`.
- On Windows, scripts that print Japanese need `PYTHONIOENCODING=utf-8` — otherwise CP932 mojibake.
