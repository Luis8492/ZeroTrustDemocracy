#!/bin/bash
set -euo pipefail

mkdir -p /app/logs /app/db
chown -R pwuser:pwuser /app/logs /app/db

if command -v su >/dev/null 2>&1; then
  exec su -s /bin/bash pwuser -c "/app/scripts/start-backend.sh"
fi

echo "Warning: 'su' command not available; starting backend as root." >&2
exec /app/scripts/start-backend.sh
