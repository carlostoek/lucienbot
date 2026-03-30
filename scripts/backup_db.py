#!/usr/bin/env python3
"""
Backup Script - Lucien Bot

Automated database backup supporting SQLite (dev) and PostgreSQL (production).
Run via: python scripts/backup_db.py

Retention: Keeps last N backups (configurable via BACKUP_RETENTION_DAYS env var).
"""
import os
import sys
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from config.settings import bot_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "7"))
BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "backups"))
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"


def ensure_backup_dir():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def backup_sqlite(db_url: str) -> Path:
    """Backup SQLite database using sqlite3 CLI."""
    # Extract file path from sqlite:///path/to/file.db
    db_path = db_url.replace("sqlite:///", "")
    backup_name = f"lucien_bot_{datetime.now().strftime(TIMESTAMP_FORMAT)}.db"
    backup_path = BACKUP_DIR / backup_name
    shutil.copy2(db_path, backup_path)
    logger.info(f"SQLite backup created: {backup_path}")
    return backup_path


def backup_postgresql(db_url: str) -> Path:
    """Backup PostgreSQL database using pg_dump via subprocess."""
    # Check pg_dump exists before attempting
    if shutil.which("pg_dump") is None:
        raise RuntimeError("pg_dump not found in PATH — install postgresql-client")

    # Parse postgresql://user:pass@host:port/dbname
    import urllib.parse
    parsed = urllib.parse.urlparse(db_url)
    user = parsed.username or "postgres"
    password = parsed.password or ""
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    dbname = parsed.path.lstrip("/") or "lucien_bot"

    backup_name = f"lucien_bot_{datetime.now().strftime(TIMESTAMP_FORMAT)}.sql"
    backup_path = BACKUP_DIR / backup_name

    env = os.environ.copy()
    if password:
        env["PGPASSWORD"] = password

    import subprocess
    cmd = [
        "pg_dump",
        "-h", host,
        "-p", str(port),
        "-U", user,
        "-d", dbname,
        "-f", str(backup_path),
        "--no-owner",
        "--no-acl",
    ]

    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"pg_dump failed: {result.stderr}")
        raise RuntimeError(f"pg_dump failed: {result.stderr}")

    logger.info(f"PostgreSQL backup created: {backup_path}")
    return backup_path


def cleanup_old_backups():
    """Remove backups older than BACKUP_RETENTION_DAYS."""
    cutoff = datetime.now() - timedelta(days=BACKUP_RETENTION_DAYS)
    removed = 0
    for backup_file in BACKUP_DIR.glob("lucien_bot_*.db") + BACKUP_DIR.glob("lucien_bot_*.sql"):
        mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
        if mtime < cutoff:
            backup_file.unlink()
            logger.info(f"Removed old backup: {backup_file}")
            removed += 1
    logger.info(f"Cleanup complete: {removed} old backup(s) removed")


def main():
    ensure_backup_dir()
    db_url = bot_config.DATABASE_URL

    logger.info(f"Starting backup of: {db_url}")

    try:
        if "sqlite" in db_url:
            backup_sqlite(db_url)
        elif "postgresql" in db_url or "postgres" in db_url:
            backup_postgresql(db_url)
        else:
            logger.error(f"Unsupported database driver in DATABASE_URL: {db_url}")
            sys.exit(1)

        cleanup_old_backups()
        logger.info("Backup completed successfully")

    except Exception as e:
        logger.error(f"Backup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
