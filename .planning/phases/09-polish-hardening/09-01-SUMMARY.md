---
phase: 09-polish-hardening
plan: "01"
subsystem: infra
tags: [security, redis, rate-limiting, backup, fsm, aiogram]

# Dependency graph
requires:
  - phase: 08-testing-and-technical-debt
    provides: Testing infrastructure, session management fixes
provides:
  - In-memory sliding window rate limiter middleware
  - Redis-backed FSM storage with graceful MemoryStorage fallback
  - Automated database backup script for SQLite and PostgreSQL
affects: [all phases, infra, security]

# Tech tracking
tech-stack:
  added: [redis==5.0.1]
  patterns: [SlidingWindow rate limiting, RedisStorage with try/except fallback, aiogram BaseMiddleware]

key-files:
  created: [utils/rate_limiter.py, scripts/backup_db.py]
  modified: [bot.py, config/settings.py, handlers/common_handlers.py, handlers/gamification_user_handlers.py, handlers/store_user_handlers.py, .env.example, requirements.txt]

key-decisions:
  - "RedisStorage preferred over SQLiteStorage for FSM persistence (Redis already needed for production)"
  - "aiogram FlagGenerator pattern for rate_limited decorator instead of non-existent with_flag function"
  - "In-memory sliding window (no external deps) for rate limiting; single-instance only"

patterns-established:
  - "aiogram BaseMiddleware for cross-cutting concerns (rate limiting)"
  - "RedisStorage with graceful MemoryStorage fallback pattern"

requirements-completed: [SEC-01, SEC-02, BACK-01]

# Metrics
duration: 12min
completed: 2026-03-30
---

# Phase 09 Plan 01: Security and Operational Resilience Infrastructure Summary

**In-memory sliding window rate limiter, Redis-backed FSM persistence with graceful fallback, and automated database backup script for SQLite and PostgreSQL.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-30 (inferred)
- **Completed:** 2026-03-30
- **Tasks:** 3
- **Files modified:** 11

## Accomplishments
- Rate limiter middleware blocks users after 5 actions per 60 seconds on protected handlers
- FSM state persists across bot restarts when Redis is available; gracefully degrades to MemoryStorage otherwise
- Automated backup script runs on both SQLite (dev) and PostgreSQL (production) with retention cleanup

## Task Commits

Each task was committed atomically:

1. **Task 1: Rate Limiter Middleware (SEC-01)** - `43b523c` (feat)
2. **Task 2: Persistent FSM with RedisStorage + Fallback (SEC-02)** - `144364a` (feat)
3. **Task 3: Automated Backup Script (BACK-01)** - `a3703a6` (feat)

## Files Created/Modified

- `utils/rate_limiter.py` - SlidingWindow rate limiter and RateLimitMiddleware; exports `RateLimitMiddleware`, `SlidingWindow`, `rate_limited` decorator
- `scripts/backup_db.py` - Standalone backup script with SQLite (`shutil.copy2`) and PostgreSQL (`pg_dump`) support; retention cleanup
- `bot.py` - RedisStorage with try/except MemoryStorage fallback; RateLimitMiddleware registered on message and callback_query dispatchers
- `config/settings.py` - Added `REDIS_URL`, `FSM_TTL_SECONDS`, `RATE_LIMIT_MAX`, `RATE_LIMIT_WINDOW` to `BotConfig`
- `handlers/common_handlers.py` - `@rate_limited()` on `cmd_start`
- `handlers/gamification_user_handlers.py` - `@rate_limited()` on `daily_gift_menu` and `claim_daily_gift`
- `handlers/store_user_handlers.py` - `@rate_limited()` on `shop_menu`
- `.env.example` - Added Phase 9 environment variables documentation
- `requirements.txt` - Added `redis==5.0.1` dependency

## Decisions Made

- Used `aiogram.dispatcher.flags.FlagGenerator` pattern for `rate_limited()` decorator (aiogram 3.x does not have `with_flag`)
- RedisStorage preferred for FSM persistence over SQLiteStorage since Redis is already needed for production deployment
- Rate limiter is in-memory (no external deps) since single-instance deployment is the current scaling model

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added missing redis package to requirements.txt**
- **Found during:** Task 2 (bot.py import check)
- **Issue:** `from aiogram.fsm.storage.redis import RedisStorage` failed with `ModuleNotFoundError: No module named 'redis'`
- **Fix:** Added `redis==5.0.1` to requirements.txt
- **Files modified:** requirements.txt
- **Verification:** `import bot` succeeded after pip install
- **Committed in:** `43b523c` (Task 1 commit)

**2. [Rule 1 - Bug] Fixed rate_limited decorator import error**
- **Found during:** Task 1 (verification)
- **Issue:** `from aiogram.dispatcher.flags import with_flag` failed — `with_flag` does not exist in aiogram 3.4.1
- **Fix:** Replaced with `FlagGenerator` pattern: `from aiogram.dispatcher.flags import FlagGenerator; rate_limited = FlagGenerator()`
- **Files modified:** utils/rate_limiter.py
- **Verification:** `import utils.rate_limiter` succeeded
- **Committed in:** `43b523c` (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both auto-fixes essential for functionality. No scope creep.

## Issues Encountered

None beyond the two deviations documented above.

## Next Phase Readiness

- Rate limiting infrastructure ready for tuning
- FSM persistence ready for Redis deployment
- Backup script ready for Railway cron integration

## Checklist Verification

- [x] `utils/rate_limiter.py` contains `RateLimitMiddleware` and `rate_limited` exportable
- [x] `bot.py` has `RedisStorage` with `try/except` fallback to `MemoryStorage`
- [x] `config/settings.py` has all Phase 9 env vars in `BotConfig`
- [x] `scripts/backup_db.py` handles both SQLite and PostgreSQL with retention cleanup
- [x] `.env.example` has all Phase 9 env vars documented

---
*Phase: 09-polish-hardening*
*Completed: 2026-03-30*
