# External Integrations

**Analysis Date:** 2026-05-07

## APIs & External Services

**Telegram Bot API:**
- aiogram 3.24.0 - Telegram Bot Framework
  - SDK/Client: Built-in aiogram client
  - Auth: `BOT_TOKEN` (from @BotFather)
  - Features used: Polling, FSM, Middleware, Bot commands, Chat member management

**Telegram API Calls in Code:**
- `bot.ban_chat_member()` / `bot.unban_chat_member()` - VIP subscription management in `bot.py:141-149`
- `bot.send_message()` - Admin notifications, welcome messages, reminders
- `ParseMode.HTML` - HTML formatting for messages

## Data Storage

**Databases:**
- **SQLite** (development)
  - Connection: `sqlite:///lucien_bot.db`
  - Client: SQLAlchemy 2.0.28 with sqlite dialect
- **PostgreSQL** (production on Railway)
  - Connection: `DATABASE_URL` env var (e.g., `postgresql://postgres:<password>@gondola.proxy.rlwy.net:53750/railway`)
  - Client: SQLAlchemy 2.0.28 with psycopg2-binary driver
  - Connection pooling: `pool_size=30`, `max_overflow=50` (production config in `models/database.py:14-20`)

**File Storage:**
- Local filesystem: `backups/` directory for database backups
- Backup files: `lucien_YYYYMMDD_HHMMSS.[sql|db]`

**FSM Storage:**
- **Redis** (optional, production)
  - Connection: `REDIS_URL` env var
  - Client: `redis.asyncio.Redis`
  - TTL: 1 day for state and data
  - Used by: aiogram FSM for conversation state persistence
- **MemoryStorage** (fallback for development without Redis)

## Authentication & Identity

**Telegram Authentication:**
- Bot token from @BotFather (`BOT_TOKEN`)
- Admin verification via `ADMIN_IDS` list in `config/settings.py`
- User identification via `telegram_id` in `User` model

**Admin Authorization:**
- `is_admin()` checks if user is in `bot_config.ADMIN_IDS`
- Used throughout handlers before admin-only actions
- Admin bypass available for rate limiting (`ADMIN_BYPASS=True`)

## Monitoring & Observability

**Logging:**
- Python standard logging (`logging.basicConfig` in `bot.py:72-79`)
- Output: `lucien_bot.log` file + stdout
- Log levels configurable via `LOG_LEVEL` env var
- Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

**Error Tracking:**
- None - No external error tracking service integrated

**Metrics:**
- `AnalyticsService` (`services/analytics_service.py`) - Internal dashboard stats
  - Total users, active VIP subscriptions, besitos in circulation
  - CSV export capability
  - Access: Custodios only

## CI/CD & Deployment

**Hosting:**
- **Railway** - Primary deployment platform
  - Config: `railway.toml`
  - Build: nixpacks with Python 3.11
  - Start command: `alembic upgrade head && python bot.py`

**CI Pipeline:**
- **GitHub Actions** (`.github/workflows/ci.yml`)
  - Lint: ruff check
  - Test: pytest with SQLite test database
  - Coverage upload to artifacts
  - Triggers: push to main, pull requests

**Dependency Management:**
- **Dependabot** (`.github/dependabot.yml`)
  - Weekly pip updates on Sundays
  - Max 3 open PRs, labels: dependencies, automated

## Environment Configuration

**Required env vars:**
- `BOT_TOKEN` - Telegram bot token (REQUIRED)
- `ADMIN_IDS` - Comma-separated admin user IDs (REQUIRED for admin features)

**Optional env vars:**
- `DATABASE_URL` - Database connection (default: SQLite)
- `TIMEZONE` - Timezone (default: America/Mexico_City)
- `CREATOR_USERNAME` - Content creator username for promotions
- `REDIS_URL` - Redis connection for FSM persistence
- `VIP_CHANNEL_ID` / `FREE_CHANNEL_ID` - Channel identifiers
- `LOG_LEVEL` - Logging level
- `DEBUG` - Debug mode flag

**Secrets location:**
- `.env` file (local development) - NOT committed to git
- Railway dashboard variables (production)

## Webhooks & Callbacks

**Incoming:**
- Telegram updates via long polling (aiogram default in `bot.py:298`)
- No webhook configuration currently active

**Outgoing:**
- Telegram API calls for messages, ban/unban, commands
- `pg_dump` subprocess for PostgreSQL backups
- `sqlite3` CLI for SQLite backups

---

*Integration audit: 2026-05-07*
