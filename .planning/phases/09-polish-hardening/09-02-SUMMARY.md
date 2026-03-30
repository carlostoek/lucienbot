---
phase: 09-polish-hardening
plan: "02"
subsystem: analytics
tags: [apscheduler, apscheduler-sqlalchemyjobstore, analytics, csv-export, metrics]

# Dependency graph
requires:
  - phase: "08-testing-and-technical-debt"
    provides: "Testing infrastructure, SQLAlchemy context managers, Session pattern"
  - phase: "09-01"
    provides: "Rate limiter, RedisStorage FSM persistence, backup script"
provides:
  - "APScheduler with SQLAlchemyJobStore (persistent jobs, no polling loop)"
  - "AnalyticsService with get_metrics() and export_activity_csv()"
  - "/analytics command for Custodios dashboard"
  - "/export command for 30-day activity CSV"
affects:
  - "Phase 10 (final phase)"
  - "Any phase using scheduler_service.py"
  - "Any phase adding admin commands"

# Tech tracking
tech-stack:
  added: [APScheduler==3.10.4]
  patterns: [APScheduler AsyncIOScheduler + SQLAlchemyJobStore, analytics dataclass, CSV export via io.StringIO]

key-files:
  created:
    - services/analytics_service.py
    - handlers/analytics_handlers.py
  modified:
    - bot.py
    - handlers/__init__.py
    - services/scheduler_service.py
    - requirements.txt

key-decisions:
  - "SQLAlchemyJobStore with bind=engine from models/database.py — uses same connection as app"
  - "SCHEDULER_MISFIRE_SECONDS env var (default 300s) — controls APScheduler misfire grace"
  - "io.BytesIO for Document in /export — binary buffer for Telegram send_document API"
  - "Preserved check_expired_subscriptions_on_startup in bot.py as safety net"

patterns-established:
  - "AnalyticsService as pure query layer (no business logic, no mutations)"
  - "AnalyticsMetrics dataclass for structured dashboard data"

requirements-completed: [SCHED-01, ANLY-01, ANLY-02]

# Metrics
duration: 5min
completed: 2026-03-30
---

# Phase 9 Plan 02 Summary

**APScheduler + SQLAlchemyJobStore scheduler, analytics dashboard (/analytics), and CSV export (/export) for Custodios**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-30T21:15:00Z
- **Completed:** 2026-03-30T21:20:00Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- APScheduler with SQLAlchemyJobStore replaces the 30-second asyncio.sleep polling loop in scheduler_service.py; jobs persist in the apscheduler_jobs table across bot restarts
- AnalyticsService provides get_metrics() (subscriptions, besitos, missions, channels) and export_activity_csv() (30-day rolling window)
- /analytics and /export Telegram commands for Custodios; both use IsSenderContact(is_admin) filter

## Task Commits

Each task was committed atomically:

1. **Task 1: AnalyticsService (ANLY-01, ANLY-02)** - `7f60a14` (feat)
2. **Task 2: Analytics Handlers (ANLY-01, ANLY-02)** - `d1588ed` (feat)
3. **Task 3: APScheduler Migration (SCHED-01)** - `f11ccf1` (feat)

**Plan metadata:** `b7c32f1` (docs: complete plan 09-02)

## Files Created/Modified

- `services/analytics_service.py` - AnalyticsService class with get_metrics() and export_activity_csv()
- `handlers/analytics_handlers.py` - analytics_router with cmd_analytics and cmd_export
- `handlers/__init__.py` - exports analytics_router
- `bot.py` - imports and registers analytics_router, startup check preserved
- `services/scheduler_service.py` - APScheduler + SQLAlchemyJobStore, no polling loop
- `requirements.txt` - added APScheduler==3.10.4

## Decisions Made

- SQLAlchemyJobStore uses `bind=engine` from models/database.py so it shares the same connection as the rest of the app (no separate DB config needed)
- SCHEDULER_MISFIRE_SECONDS env var (default 300s) controls APScheduler misfire grace time — allows jobs to run late after bot restart
- check_expired_subscriptions_on_startup() kept in bot.py as safety net even though the scheduler now handles expirations on a 60s interval
- io.BytesIO wrapping the CSV string buffer for Telegram's send_document API (expects bytes, not string)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness

- Phase 10 is the final phase; all Phase 9 infrastructure (rate limiter, RedisStorage FSM, backup script, analytics dashboard, persistent scheduler) is complete
- APScheduler requires running `alembic revision --autogenerate` to create the apscheduler_jobs table migration for PostgreSQL deployments
- No blockers for Phase 10

---
*Phase: 09-polish-hardening*
*Completed: 2026-03-30*
