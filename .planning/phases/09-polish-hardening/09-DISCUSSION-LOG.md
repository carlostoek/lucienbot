# Phase 9: Polish & Hardening - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-30
**Phase:** 09-polish-hardening
**Mode:** auto (--auto flag)

---

## Areas Discussed (All Auto-Resolved)

### Area: Rate Limiting Strategy
| Option | Description | Selected |
|--------|-------------|----------|
| Redis-backed rate limiting | External Redis store for distributed limiting | ✗ |
| Middleware + in-memory (Recommended) | Custom aiogram middleware with sliding window per user | ✓ |
| aiogram-dialog throttling | Use aiogram-dialog's built-in throttling | ✗ |

**[auto]** Rate Limiting — Q: "Which approach for rate limiting?" → Selected: Middleware + in-memory (recommended default)
**Notes:** No new external dependency, sufficient for single-instance on Railway, Railway ephemeral filesystem prevents Redis use without Upstash addon.

### Area: FSM Persistence Storage
| Option | Description | Selected |
|--------|-------------|----------|
| RedisStorage (Recommended) | aiogram.contrib.fsm_storage.redis with Redis | ✓ |
| SQLiteStorage | aiogram SQLite storage, adds DB dependency | ✗ |
| Keep MemoryStorage | No change, state lost on restart | ✗ |

**[auto]** FSM Storage — Q: "Which approach for persistent FSM?" → Selected: RedisStorage (recommended default)
**Notes:** Standard aiogram 3.x approach. Requires Redis on Railway (Upstash Redis addon). Graceful fallback to MemoryStorage if Redis unavailable.

### Area: Backup Strategy
| Option | Description | Selected |
|--------|-------------|----------|
| Railway-native + script (Recommended) | Railway PostgreSQL snapshots + local backup script | ✓ |
| Full custom S3 solution | S3 bucket, IAM roles, custom uploader | ✗ |
| Manual only | No automated backups | ✗ |

**[auto]** Backup Strategy — Q: "Which approach for automated backups?" → Selected: Railway-native + script (recommended default)
**Notes:** Railway PostgreSQL has built-in snapshots. Add pg_dump script for exportable backups. SQLite dev gets sqlite3 CLI backup script.

### Area: Persistent Job Queue
| Option | Description | Selected |
|--------|-------------|----------|
| APScheduler + SQLAlchemyJobStore (Recommended) | Use existing DB as job store, survives restarts | ✓ |
| Celery / RQ | Separate worker process, over-engineered | ✗ |
| Keep polling 30s | Status quo, loses state on restart | ✗ |

**[auto]** Job Queue — Q: "Which approach for persistent job queue?" → Selected: APScheduler + SQLAlchemyJobStore (recommended default)
**Notes:** Replaces fixed 30s polling with event-driven scheduling. Uses existing PostgreSQL, no new external dependencies. Single-instance only.

### Area: Analytics & Metrics
| Option | Description | Selected |
|--------|-------------|----------|
| Telegram command only (Recommended) | /analytics and /export commands, no web service | ✓ |
| Separate web dashboard | New web service, significant scope | ✗ |
| Third-party BI tool | External service, integration overhead | ✗ |

**[auto]** Analytics — Q: "Which approach for analytics dashboard?" → Selected: Telegram command only (recommended default)
**Notes:** Keep it simple — no external web service. /analytics for metrics, /export for CSV data. Lucien voice for output.

---

## Claude's Discretion

The following were auto-deferred to implementation-time judgment:
- Rate limit exact thresholds: 5 actions per 60 seconds (env var configurable)
- Redis FSM TTL: 7 days (env var configurable)
- Backup retention: 7 days (env var configurable)
- APScheduler misfire_grace_time: env var configurable
- Exact analytics metrics and formatting
- Rate limit error message wording
- Backup schedule timing

## Deferred Ideas

- Web analytics dashboard — belongs in a future web integration phase
- Distributed rate limiting with Redis — would need Upstash Redis addon on Railway
- Celery/RQ for job queue — over-engineered for single-instance deployment

---

*Discussion log: 2026-03-30 (auto mode)*
