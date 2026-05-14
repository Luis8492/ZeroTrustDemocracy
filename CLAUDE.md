# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**ZeroTrustDemocracy (世田谷区議会版)** structures Setagaya assembly minutes into question/answer pairs (QAs) and ships them as static JSON to a Svelte frontend hosted on Cloudflare Pages; users rate QAs locally and all ratings stay client-side in IndexedDB. The "zero trust" angle is that the server never sees user evaluations — in fact there is no application server in production. A weekly GitHub Actions cron re-fetches, re-analyzes, and re-exports.

This distribution ships with a single municipality (`setagaya`) containing two session sub-packages: `committee` (委員会) and `regular` (定例会). Other assemblies are addressed by **forking the repo** — see `docs/FORK_GUIDE.md`.

## Common commands

```bash
# Install deps
pip install -r requirements.txt
playwright install chromium     # only needed when running the fetcher

# Initialize a municipality's SQLite DB (creates minutes, meetings, downloaded_minutes_url_helper, questions tables)
python scripts/init_db.py setagaya         # one DB for both committee + regular sessions

# Fetch raw minutes (uses Playwright; non-headless by default — set FETCHER_HEADLESS=1 or CI=true for headless)
python app/fetch.py --municipality <municipality>

# Parse fetched minutes into structured QAs in SQLite
python app/minute_analyzer.py --municipality <municipality>   # municipality optional; processes all if omitted

# Export SQLite → static JSON (consumed by the frontend in production)
python scripts/export_static_data.py

# Serve the frontend (Svelte 5 + Vite) — reads static JSON from /data
cd frontend
npm install
npm run dev       # http://localhost:8001, serves frontend/public/data/* at /data

# Tests (pytest, no config file — discovers tests/ by default)
pytest                                # run all
pytest tests/test_setagaya_participants.py     # single file
pytest tests/test_setagaya_participants.py::test_name   # single test
```

The legacy `app/feederAPI.py` (FastAPI) still exists and can be run with `python -m uvicorn app.feederAPI:app`, but the frontend no longer talks to it — production is fully static.

## Architecture

### Four-stage data pipeline
1. **Fetcher** (`app/fetch.py` → `municipal_modules/<m>/fetchers/`): Playwright-driven scraper. Downloads raw text into `app/raw_minutes/`, records URL + `fetcher` name + deterministic UUID in `minutes` table with `analyzed=0`. UUIDs are `uuid5(NAMESPACE_URL, f"{fetcher_name}:{url}")` — stable across re-fetches.
2. **Analyzer** (`app/minute_analyzer.py` → `municipal_modules/<m>/parsers/`): reads `analyzed=0` rows, runs the municipality's parser, writes `meetings` + `questions` rows, flips `analyzed=1`. QA UUIDs are derived from the parent minute UUID + topic/qa indices, so a re-analysis produces stable IDs.
3. **Exporter** (`scripts/export_static_data.py`): reads the DB, applies anonymization + party resolution, writes `frontend/public/data/index.json` (selection-time metadata) + `frontend/public/data/meetings/<file_name>.json` (full payload per meeting). This is what the frontend actually reads.
4. **GitHub Actions** (`.github/workflows/update-data.yml`): runs stages 1–3 weekly and commits the updated DB and JSON. Cloudflare Pages rebuilds on push.

### Per-municipality plugin layout
Each municipality lives under `app/municipal_modules/<name>/` with:
- `config/<name>.yaml` — top-level shared fields (`db_path`, `pii_files`, `party_table_path`) plus per-session overrides under `fetchers.<FETCHER_NAME>` (`fetch_url`, `encoding`)
- `__init__.py` — exports `PARSERS = {fetcher_name: parser_class}` and `FETCHERS = {fetcher_name: fetcher_class}`
- one or more **session sub-packages** (e.g. `committee/`, `regular/`), each containing `fetchers/` and `parsers/` packages
- `base/` shared classes: `BaseMinuteFetcher`, `BaseMinuteParser`

Discovery: `app/municipal_modules/__init__.py:load_parsers_by_municipality()` and `load_fetchers_by_municipality()` import each top-level municipality package and read its `PARSERS` / `FETCHERS` dicts (falling back to scanning `parsers/` for legacy modules without explicit dicts). The set of municipalities the API accepts is derived at runtime by `config_loader.available_municipalities()` from `<name>/config/<name>.yaml` existence (and any `*.yaml` under `CONFIG_DIR`) — there is no hard-coded allowlist anywhere.

Config resolution for a single fetcher: `config_loader.load_for_fetcher(municipality, fetcher_name)` merges the shared top-level fields with the per-session overrides under `fetchers.<FETCHER_NAME>`, returning a flat dict. The `BaseMinuteFetcher` constructor and the analyzer both use this helper.

Minute/QA payload format (parser output, also stored as JSON strings in SQLite) is documented in `app/municipal_modules/base/README.md` — `mark` field `◆` denotes the questioner, `○` the chair, `◎` the respondent.

### Config resolution
`config_loader.py` resolves config in this priority:
1. `CONFIG_PATH` env var (absolute path to a global config YAML)
2. `CONFIG_DIR` env var (looks for `config.yaml` and `<municipality>.yaml` under that dir, also `<municipality>/<municipality>.yaml` and `<municipality>/config/<municipality>.yaml`)
3. Repo-root `config.yaml` and bundled `app/municipal_modules/<m>/config/<m>.yaml`

When `CONFIG_DIR` matches an external dir, relative paths inside the YAML (`db_path`, `pii_files`, etc.) are resolved against `CONFIG_DIR` instead of the repo root.

### Database
SQLite, one file per municipality (e.g. `db/setagaya.db`). Schema is defined in two places — `scripts/init_db.py` (initial creation) and `utils/db.py:ensure_schema` (idempotent + adds missing columns at runtime). Fetchers and the analyzer call `ensure_schema` on startup, so legacy DBs auto-upgrade. Tables:
- `minutes` — one row per downloaded URL (uuid, url, file_name, fetcher, analyzed)
- `meetings` — one row per parsed file (file_name, date, name, participants JSON)
- `questions` — one row per QA sequence (uuid, file_name, topic_intro JSON, QA JSON, questioner)
- `downloaded_minutes_url_helper` — extra metadata (e.g. `questioner_party`, `questioner_name`) keyed by minute URL, used as a fallback for party lookup when the CSV `party_table` doesn't match

### Anonymization
`Anonymizer` does naive string replacement of every line in the `pii_files` with `***`. Applied at **export time** by `scripts/export_static_data.py`, not at parse time — so raw text in `app/raw_minutes/` and `questions.QA` JSON inside the DB are **not** anonymized; the exported JSON under `frontend/public/data/` is.

### Frontend
**Svelte 5 + Vite + TypeScript**, built to `frontend/dist/` and deployed via Cloudflare Pages.

- Routing: `svelte-spa-router` hash-based (`#/`, `#/result`, `#/settings`).
- IndexedDB (`EvalDB` v2): `evaluations` store (legacy keyed by `QA_id`) + `settings` store (theme etc.).
- Themes are CSS-variable based, switched by `<html data-theme="...">`. Shipped: `plain`, `chat`, `scroll` (縦書き和紙), `hud` (SF/glassmorphism). Add a new theme by extending `src/themes/themes.css` and adding `:global([data-theme='X'])` overrides in components.
- `src/lib/api.ts` loads `/data/index.json` once and per-meeting JSON on demand from `/data/meetings/<file_name>.json`; the weighted-random "next QA" pick happens client-side.
- `src/lib/config.ts` reads `VITE_DATA_BASE` (defaults to `/data`) and `VITE_MUNICIPALITY` from env, so a fork can repoint without touching code.

## Notes when extending

- Adding a municipality should generally happen via **forking** (see `docs/FORK_GUIDE.md`). Within this repo, drop in `app/municipal_modules/<name>/{config,<session>...}` and export `PARSERS` / `FETCHERS` from the package — both the analyzer/fetch CLI and the API auto-discover them.
- Setagaya now lives at `app/municipal_modules/setagaya/` with `committee/` and `regular/` sub-packages. The unified DB is `db/setagaya.db`; `minutes.fetcher` distinguishes session types.
- `app/feederAPI.py` does `sys.path.append(...)` to import `config_loader` from the repo root. Always launch the API from the repo root, not from inside `app/`.
- On Windows, scripts that print Japanese need `PYTHONIOENCODING=utf-8` — otherwise CP932 mojibake.
