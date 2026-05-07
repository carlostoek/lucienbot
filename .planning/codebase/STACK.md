# Technology Stack

**Analysis Date:** 2026-05-07

## Languages

**Primary:**
- Python 3.11.8 - Core bot implementation, all services and handlers

**Secondary:**
- SQL - Database queries via SQLAlchemy ORM

## Runtime

**Environment:**
- Python 3.11+ (specified in `runtime.txt`, `railway.toml` uses nixpacks with Python 3.11)

**Package Manager:**
- pip (via `requirements.txt`)
- Lockfile: Not committed (`.gitignore` excludes `*.db` and backup files)

## Frameworks

**Core:**
- aiogram 3.24.0 - Telegram Bot Framework (async modern framework)
- SQLAlchemy 2.0.28 - ORM for database operations
- alembic 1.12.1 - Database migration management

**Testing:**
- pytest 8.1.1 - Test runner
- pytest-asyncio 0.23.5 - Async test support
- pytest-cov 5.0.0 - Coverage reporting

**Background Jobs:**
- APScheduler 3.10.4 - Task scheduler with SQLAlchemyJobStore for persistence

**Build/Dev:**
- ruff - Linting and formatting (configured in `pyproject.toml`)
- nixpacks - Build backend for Railway deployment

## Key Dependencies

**Critical:**
- aiogram 3.24.0 - Telegram Bot API client, FSM storage, middleware
- SQLAlchemy 2.0.28 - ORM, connection pooling, transactions
- psycopg2-binary 2.9.9 - PostgreSQL driver for production

**Infrastructure:**
- redis 5.0.1 - Redis async client for FSM storage (RedisStorage when REDIS_URL is set)
- alembic 1.12.1 - Schema migrations for PostgreSQL/SQLite
- python-dotenv 1.0.1 - Environment variable loading from `.env`

**Utilities:**
- APScheduler 3.10.4 - Background job scheduling (backup, pending requests, reminders)
- aiolimiter 1.2.1 - Rate limiting middleware
- pytz 2024.1 - Timezone handling
- python-dateutil 2.9.0 - Date/time utilities

## Configuration

**Environment:**
- `.env` file with `python-dotenv` loading
- Key configs: `BOT_TOKEN`, `ADMIN_IDS`, `DATABASE_URL`, `TIMEZONE`, `CREATOR_USERNAME`
- Config class: `config/settings.py` with `BotConfig`, `MessagesConfig`, `RateLimitConfig`

**Build:**
- `pyproject.toml` - Project metadata, pytest, ruff config
- `railway.toml` - Railway deployment config
- `alembic.ini` - Migration configuration
- `runtime.txt` - Python version specification

## Platform Requirements

**Development:**
- Python 3.11+
- SQLite for local development (`DATABASE_URL=sqlite:///lucien_bot.db`)

**Production:**
- Railway PostgreSQL (connection via `DATABASE_URL` env var)
- Redis (optional, for FSM persistence via `REDIS_URL`)
- `pg_dump` CLI tool for PostgreSQL backups

---

*Stack analysis: 2026-05-07*
