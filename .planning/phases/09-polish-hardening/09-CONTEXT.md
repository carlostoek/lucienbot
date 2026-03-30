# Phase 9: Polish & Hardening - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Production hardening for Lucien Bot: rate limiting, persistent FSM, automated backups, persistent job queue, and analytics dashboard for Custodios.

**In scope:** Security middleware, state persistence, operational resilience, monitoring.
**Out of scope:** Multi-instance scaling, web frontend, i18n, native mobile app.

</domain>

<decisions>
## Implementation Decisions

### Rate Limiting (SEC-01)
- **D-01:** Middleware-based rate limiting via `aiogram` middleware pattern
  - Decision: Custom aiogram middleware using in-memory sliding window per user
  - Rationale: No new external dependency (Redis), sufficient for single-instance, Railway ephemeral filesystem
  - Scope: Protect `/start`, `/buy`, `/gift`, `/hug`, `/daily` handlers
  - Limits: 5 actions per 60 seconds per user for protected commands
  - Error response: Inform user they're being rate limited, no silent drops
- **Claude's Discretion:** Exact limit thresholds (5/60s) can be tuned via env vars

### Persistent FSM (SEC-02)
- **D-02:** `RedisStorage` from `aiogram.contrib.fsm_storage.redis`
  - Decision: Redis for FSM persistence, keyed by user_id
  - Rationale: Standard aiogram 3.x approach, survives bot restarts
  - Railway integration: REDIS_URL env var for Redis connection, use Upstash Redis addon
  - Fallback: If Redis unavailable, degrade gracefully to MemoryStorage with warning log
- **Claude's Discretion:** Redis key TTL can be set to 7 days for abandoned conversations

### Automated Backups (BACK-01)
- **D-03:** Railway-native PostgreSQL backups + local SQLite backup script
  - For PostgreSQL (production): Railway's automatic daily snapshots + `pg_dump` script on Railway cron
  - For SQLite (dev): `scripts/backup_db.py` using `sqlite3` CLI or SQLAlchemy
  - Backup destination: Railway persistent volume or S3-compatible storage
  - Retention: Keep last 7 daily backups
  - Command: `python scripts/backup_db.py` callable from Railway startup script
- **Claude's Discretion:** Exact retention count and backup timing

### Persistent Job Queue (SCHED-01)
- **D-04:** APScheduler with database-backed job store
  - Decision: `APScheduler` with `SQLAlchemyJobStore` using existing PostgreSQL
  - Rationale: Survives bot restarts, no new external dependency, single-instance only
  - Replaces: Fixed 30s polling loop in `scheduler_service.py`
  - Migration: Refactor existing scheduler_service.py to use APScheduler with persistent store
  - Dynamic scheduling: Jobs scheduled based on actual expiry times, not fixed intervals
- **Claude's Discretion:** APScheduler misfire_grace_time setting

### Analytics Dashboard (ANLY-01, ANLY-02)
- **D-05:** Telegram command-based analytics — no external web service
  - `AnalyticsService` class with query methods for Custodios
  - New handler: `/analytics` command showing:
    - Active subscriptions count, new today, expiring this week
    - Total besitos sent today, daily gift recipients
    - Mission completion rates (last 7 days)
    - Channel member counts (Free + VIP)
  - Data export: `/export` admin command generating CSV of user activity
  - No web dashboard — keep it in Telegram for simplicity
- **Claude's Discretion:** Exact metrics shown, chart formatting in Telegram

### Claude's Discretion
- Rate limit exact values (5 per 60s) → env var `RATE_LIMIT_MAX` / `RATE_LIMIT_WINDOW`
- Redis FSM TTL (7 days) → env var `FSM_TTL_SECONDS`
- Backup retention (7 days) → env var `BACKUP_RETENTION_DAYS`
- APScheduler misfire_grace_time → env var `SCHEDULER_MISFIRE_SECONDS`
- Analytics metrics and formatting → implementer's judgment

### Folded Todos
No pending todos matched Phase 9 scope.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture & Stack
- `bot.py` — Bot initialization, FSM storage setup, startup/shutdown hooks (line ~181: `MemoryStorage`)
- `services/scheduler_service.py` — Current scheduler implementation (30s polling loop to replace)
- `.planning/codebase/ARCHITECTURE.md` — FSM and scheduler data flow patterns
- `.planning/codebase/CONCERNS.md` — Known issues (no rate limiting, MemoryStorage, scheduler polling, no backups)
- `.planning/codebase/STACK.md` — Tech stack: aiogram 3.4.1, SQLAlchemy 2.0, Railway + PostgreSQL

### Requirements
- `ROADMAP.md` Phase 9 success criteria — SEC-01, SEC-02, BACK-01, SCHED-01, ANLY-01, ANLY-02
- `REQUIREMENTS.md` — v2 requirements: SEC-01, SEC-02, BACK-01, SCHED-01, ANLY-01, ANLY-02

### Prior Phase Artifacts
- `services/vip_service.py` — VIP expiry logic that scheduler needs to cover
- `services/channel_service.py` — Pending request approval logic that scheduler needs to cover
- `models/database.py` — Database session management (Phase 8 context managers)

### Testing (Phase 8)
- `pyproject.toml` — pytest configuration (reference for new test patterns)
- `tests/conftest.py` — Existing fixtures for mocking aiogram objects

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `utils/lucien_voice.py` — Use for rate limit error messages and analytics reports
- `keyboards/inline_keyboards.py` — Analytics can reuse inline keyboard patterns
- Existing `models/` — SQLAlchemy models for analytics queries
- Phase 8 `_owns_session` pattern — Use for backup script database access

### Established Patterns
- Services use `with_for_update()` for concurrency (Phase 8) — continue this pattern
- Middleware pattern exists in aiogram 3.x — rate limiter should be a middleware class
- Context managers for DB sessions (Phase 8) — backup script should follow same pattern
- Lucien voice in Spanish — all analytics output should use Lucien voice

### Integration Points
- `bot.py` — Replace `MemoryStorage()` with `RedisStorage()` on startup
- `services/scheduler_service.py` — Refactor to use APScheduler with SQLAlchemyJobStore
- `handlers/` — Register rate limiting middleware in dispatcher
- `services/` — New `analytics_service.py`, new `rate_limiter.py` module

</code_context>

<specifics>
## Specific Ideas

- Rate limiter middleware should be transparent — doesn't block, just warns and delays
- Analytics export CSV format: `user_id, action, timestamp, metadata` per row
- Backup script should be idempotent — safe to run multiple times
- APScheduler jobs should be registered at startup, not dynamically created
- Redis FSM should have graceful degradation if Redis is unreachable at startup

</specifics>

<deferred>
## Deferred Ideas

### Reviewed Todos (not folded)
None — no pending todos matched Phase 9 scope.

## Ideas Outside Phase Scope
- Web dashboard for analytics — belongs in a future web phase
- Redis-based distributed rate limiting — would need Redis; single-instance memory approach sufficient for current scale
- Celery/RQ job queue — over-engineered for single-instance; APScheduler + DB store is sufficient

</deferred>

---

*Phase: 09-polish-hardening*
*Context gathered: 2026-03-30*
