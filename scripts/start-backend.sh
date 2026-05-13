#!/bin/bash
set -euo pipefail

MUNICIPALITY="${MUNICIPALITY:-setagaya}"

if [[ "${INIT_DB_ON_START:-false}" == "true" ]]; then
  python scripts/init_db.py "${MUNICIPALITY}"
fi

if [[ "${RUN_FETCH_ON_START:-false}" == "true" ]]; then
  python app/fetch.py --municipality "${MUNICIPALITY}"
  python app/minute_analyzer.py --municipality "${MUNICIPALITY}"
fi

HOST="${UVICORN_HOST:-0.0.0.0}"
PORT="${UVICORN_PORT:-8000}"

exec uvicorn app.feederAPI:app --host "${HOST}" --port "${PORT}"
