from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime, timedelta

# Determine project root and log directory
BASE_DIR = Path(__file__).resolve().parents[1]
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "app.log"

MAX_BYTES = 1 * 1024 * 1024  # 1MB
BACKUP_COUNT = 5


def clean_old_logs(retention_days: int = 30) -> None:
    """Delete log files older than ``retention_days`` days."""
    if not LOG_DIR.exists():
        return

    cutoff = datetime.now() - timedelta(days=retention_days)
    for log_file in LOG_DIR.glob("app.log*"):
        try:
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if mtime < cutoff:
                log_file.unlink()
        except OSError:
            # Ignore issues deleting log files
            pass


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger with a rotating file handler."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT
    )
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


# Clean old logs when module is imported
clean_old_logs()
