# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**ZeroTrustDemocracy (世田谷区議会版)** structures Setagaya assembly minutes into question/answer pairs (QAs) served by a FastAPI backend; a static frontend lets users rate them while keeping all ratings client-side in IndexedDB. The "zero trust" angle is that the server never sees user evaluations.

This distribution ships with a single municipality (`setagaya`) containing two session sub-packages: `committee` (委員会) and `regular` (定例会). Other assemblies are addressed by **forking the repo** — see `docs/FORK_GUIDE.md`.

## Common commands

```bash
# Install deps (Playwright is used for fetching, installed via mcr.microsoft.com/playwright/python image in Docker)
pip install -r requirements.txt

# Initialize a municipality's SQLite DB (creates minutes, meetings, downloaded_minutes_url_helper, questions tables)
python scripts/init_db.py setagaya         # one DB for both committee + regular sessions

# Fetch raw minutes (uses Playwright; non-headless by default)
python app/fetch.py --municipality <municipality>

# Parse fetched minutes into structured QAs in SQLite
python app/minute_analyzer.py --municipality <municipality>   # municipality optional; processes all if omitted

# Run the API (must be launched from repo root so config_loader.py is importable)
python -m uvicorn app.feederAPI:app --host 0.0.0.0 --port 8000

# Serve the frontend (Svelte 5 + Vite)
cd frontend
npm install
npm run dev       # http://localhost:8001, proxies /api to :8000

# Tests (pytest, no config file — discovers tests/ by default)
pytest                                # run all
pytest tests/test_setagaya_participants.py     # single file
pytest tests/test_setagaya_participants.py::test_name   # single test
```

Docker (`docker compose up --build`) runs both services. Toggle init/fetch on container start via `INIT_DB_ON_START`, `RUN_FETCH_ON_START`, and `MUNICIPALITY` env vars (see README "オプション" table).

## Architecture

### Three-stage data pipeline
1. **Fetcher** (`app/fetch.py` → `municipal_modules/<m>/fetchers/`): Playwright-driven scraper. Downloads raw text into `app/raw_minutes/`, records URL + `fetcher` name + deterministic UUID in `minutes` table with `analyzed=0`. UUIDs are `uuid5(NAMESPACE_URL, f"{fetcher_name}:{url}")` — stable across re-fetches.
2. **Analyzer** (`app/minute_analyzer.py` → `municipal_modules/<m>/parsers/`): reads `analyzed=0` rows, runs the municipality's parser, writes `meetings` + `questions` rows, flips `analyzed=1`. QA UUIDs are derived from the parent minute UUID + topic/qa indices, so a re-analysis produces stable IDs.
3. **API** (`app/feederAPI.py`): serves QAs from the DB, anonymizing on read.

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

When `CONFIG_DIR` matches an external dir, relative paths inside the YAML (`db_path`, `pii_files`, etc.) are resolved against `CONFIG_DIR` instead of the repo root — this is what makes the Docker `./config:/app/config` mount work.

### Database
SQLite, one file per municipality (e.g. `db/setagaya.db`). Schema is defined in two places — `scripts/init_db.py` (initial creation) and `utils/db.py:ensure_schema` (idempotent + adds missing columns at runtime). Fetchers and the analyzer call `ensure_schema` on startup, so legacy DBs auto-upgrade. Tables:
- `minutes` — one row per downloaded URL (uuid, url, file_name, fetcher, analyzed)
- `meetings` — one row per parsed file (file_name, date, name, participants JSON)
- `questions` — one row per QA sequence (uuid, file_name, topic_intro JSON, QA JSON, questioner)
- `downloaded_minutes_url_helper` — extra metadata (e.g. `questioner_party`, `questioner_name`) keyed by minute URL, used as a fallback for party lookup when the CSV `party_table` doesn't match

### Anonymization
`Anonymizer` does naive string replacement of every line in the `pii_files` with `***`. Applied on read in `format_QA`, not at parse time — raw text in `raw_minutes/` and `questions.QA` JSON is **not** anonymized.

### Frontend
**Svelte 5 + Vite + TypeScript**, built to `frontend/dist/` and served by Nginx in Docker (multi-stage build). `Dockerfile.frontend` runs `npm run build` in a Node stage.

- Routing: `svelte-spa-router` hash-based (`#/`, `#/result`, `#/settings`).
- IndexedDB (`EvalDB` v2): `evaluations` store (legacy keyed by `QA_id`) + `settings` store (theme etc.).
- Themes are CSS-variable based, switched by `<html data-theme="...">`. Shipped: `plain`, `chat`, `scroll` (縦書き和紙), `hud` (SF/glassmorphism). Add a new theme by extending `src/themes/themes.css` and adding `:global([data-theme='X'])` overrides in components.
- `src/lib/config.ts` reads `VITE_API_BASE` and `VITE_MUNICIPALITY` from env, so a fork can repoint without touching code.

## Notes when extending

- Adding a municipality should generally happen via **forking** (see `docs/FORK_GUIDE.md`). Within this repo, drop in `app/municipal_modules/<name>/{config,<session>...}` and export `PARSERS` / `FETCHERS` from the package — both the analyzer/fetch CLI and the API auto-discover them.
- Setagaya now lives at `app/municipal_modules/setagaya/` with `committee/` and `regular/` sub-packages. The unified DB is `db/setagaya.db`; `minutes.fetcher` distinguishes session types.
- `app/feederAPI.py` does `sys.path.append(...)` to import `config_loader` from the repo root. Always launch the API from the repo root, not from inside `app/`.
- On Windows, scripts that print Japanese need `PYTHONIOENCODING=utf-8` — otherwise CP932 mojibake.
