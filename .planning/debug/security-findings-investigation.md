---
status: resolved
trigger: "Fix 5 confirmed security/logic issues in priority order"
created: 2026-04-02T00:00:00Z
updated: 2026-04-02T00:00:00Z
---

## Current Focus
All 5 findings resolved. 76 tests pass.

## Findings Status

### FINDING #1 (HIGH) — Global Rate Limiter causes DoS
- **File:** handlers/rate_limit_middleware.py
- **Status:** RESOLVED
- **Fix:** Replaced single `self.limiter` with per-user dict `self._limiters` keyed by user_id.
  Each user gets their own `AsyncLimiter` instance. Added `asyncio.Lock` for thread-safe dict access.
  Added TTL-based cleanup (5 min idle) to prevent memory leaks.
- **Tests:** tests/unit/test_rate_limit_middleware.py (6 new tests)

### FINDING #2 (HIGH) — Transaction Atomicity in advance_to_node
- **Files:** services/besito_service.py, services/story_service.py
- **Status:** RESOLVED
- **Fix:** Added `commit: bool = True` param to `debit_besitos()`. When called from `advance_to_node`,
  passes `commit=False`. Removed `db.commit()` from `_add_archetype_points()`. The single
  `db.commit()` at end of `advance_to_node` now covers besitos + progress atomically.
- **Tests:** tests/unit/test_besito_service.py (3 new tests), tests/unit/test_story_service.py (2 new tests)

### FINDING #3 (MEDIUM) — Credentials in pg_dump CLI args
- **File:** services/backup_service.py
- **Status:** RESOLVED
- **Fix:** Parse DATABASE_URL with `urllib.parse.urlparse`, extract PGPASSWORD and pass via
  `env["PGPASSWORD"]` instead of CLI. CLI args now use `-h`, `-p`, `-U`, `-d` flags only.
  Password never appears in `ps aux` output.
- **Tests:** tests/unit/test_backup_service.py (4 new tests)

### FINDING #4 (MEDIUM) — Race Condition in VIP Entry
- **Files:** services/vip_service.py, handlers/vip_handlers.py
- **Status:** RESOLVED
- **Fix:** Added `get_vip_entry_state_for_update()` with `with_for_update()` locking in vip_service.py.
  Changed `vip_entry_ready` handler to use `get_vip_entry_state_for_update()` instead of
  `get_vip_entry_state()`, holding the lock from state check through invite link creation.
- **Tests:** tests/unit/test_vip_service.py (2 new tests)

### FINDING #5 (LOW) — Integer Overflow on Besitos
- **Files:** models/models.py, alembic/versions/c90055bca411_upgrade_besitos_and_broadcast_reactions_.py
- **Status:** RESOLVED
- **Fix:** Changed all besito-related Integer columns to BigInteger:
  - BesitoBalance: balance, total_earned, total_spent
  - BesitoTransaction: amount
  - BroadcastReaction: besitos_awarded
  Alembic migration generated and ready to apply.
- **Tests:** tests/unit/test_story_service.py (3 new BigInteger type tests)

## Resolution
root_cause: All 5 issues confirmed and fixed.
fix: All 5 fixes implemented with tests.
verification: "76 passed" — all new and existing tests pass.
files_changed:
  - handlers/rate_limit_middleware.py
  - services/besito_service.py
  - services/story_service.py
  - services/backup_service.py
  - services/vip_service.py
  - handlers/vip_handlers.py
  - models/models.py
  - alembic/versions/c90055bca411_upgrade_besitos_and_broadcast_reactions_.py
  - tests/unit/test_rate_limit_middleware.py (new)
  - tests/unit/test_backup_service.py (new)
  - tests/unit/test_story_service.py (new)
  - tests/unit/test_besito_service.py (updated)
  - tests/unit/test_vip_service.py (updated)
  - tests/conftest.py (updated sys.path)
