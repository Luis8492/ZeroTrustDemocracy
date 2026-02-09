#!/bin/bash
set -euo pipefail

APP_USER="${APP_USER:-appuser}"
APP_GROUP="${APP_GROUP:-appgroup}"

mkdir -p /app/logs /app/db /app/app/raw_minutes /app/app/exports

if [[ "$(id -u)" -eq 0 ]]; then
  chown -R "${APP_USER}:${APP_GROUP}" /app/logs /app/db /app/app/exports

  if command -v su >/dev/null 2>&1; then
    exec su -s /bin/bash "${APP_USER}" -c "/app/scripts/start-backend.sh"
  fi

  echo "Warning: 'su' command not available; starting backend as root." >&2
fi

exec /app/scripts/start-backend.sh
