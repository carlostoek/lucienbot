# Codebase Concerns

**Analysis Date:** 2026-05-07

## Tech Debt

**Scheduler Job Serialization Risk:**
- Issue: APScheduler with SQLAlchemyJobStore requires module-level job functions to avoid pickling errors. The `_sync_question_sets()` function is called at startup before scheduler starts, but `GameService._active_question_set_path` is a class-level mutable attribute modified by scheduler jobs.
- Files: `services/scheduler_service.py`
- Impact: If scheduler jobs run in multiple instances, the class-level cache in `GameService` could become inconsistent across instances.
- Fix approach: Consider using Redis or database to store active question set path instead of class-level cache, or add distributed locking.

**GameService Instance-Level Caching:**
- Issue: `_questions`, `_vip_questions`, `_last_loaded_path`, `_last_loaded_vip_path` are instance-level caches. Each handler instantiation creates a new service instance, potentially causing stale question data to persist longer than expected.
- Files: `services/game_service.py` (lines 487-491)
- Impact: During long-running trivia sessions, if the question set file changes, users may see inconsistent questions within the same streak session.
- Fix approach: Use a shared cache (Redis) for question sets, or invalidate cache on question set sync.

**FSM State Loss with MemoryStorage:**
- Issue: When `REDIS_URL` is not set, `MemoryStorage` is used. This means FSM state (including trivia streak progress) is lost on bot restart.
- Files: `bot.py` (lines 83-106)
- Impact: Users in the middle of a trivia streak lose all progress if the bot restarts.
- Fix approach: Document this limitation clearly, or make Redis required for production deployments.

---

## Known Bugs

**Duplicate Exception Handler in Scheduler:**
- Issue: `_process_pending_requests()` has a nested `except Exception` block inside another `except Exception` block (lines 143-164 of `scheduler_service.py`). The inner `except` will never catch exceptions from the `try` block since all exceptions are already caught by the outer handler.
- Files: `services/scheduler_service.py:143-164`
- Trigger: Any exception in the inner try block (lines 109-142) gets caught by outer except (line 162), not the more specific inner handler (line 143).
- Workaround: The outer handler logs and rolls back, which is acceptable for most failure modes.

**Trivia Streak Session Not Fully Tracked:**
- Issue: The streak timeout mechanism (`_check_streak_timeout`) tracks `streak_started_at` via state, but if the user continues within the streak session, the timeout is not reset between questions. A user's streak could expire mid-session if they take too long on question 5 when they started at question 1.
- Files: `services/game_service.py:1165-1176`, `handlers/game_user_handlers.py:181-196`
- Trigger: User starts trivia, takes a long time to answer each question, exceeds 2-minute total from first answer.
- Workaround: Not implemented - streak could expire unexpectedly.

---

## Security Considerations

**Rate Limiting Uses In-Memory Storage:**
- Issue: `ThrottlingMiddleware` uses in-memory `_limiters` dict. This means:
  1. Rate limits reset when bot restarts
  2. Rate limits are not shared across multiple bot instances
  3. Memory grows unbounded if cleanup fails (mitigated by `_LIMITER_TTL`)
- Files: `handlers/rate_limit_middleware.py`
- Current mitigation: `_LIMITER_TTL = 300` (5-minute cleanup) and `ADMIN_BYPASS` flag.
- Recommendations: For production with multiple instances, consider Redis-backed rate limiting.

**Admin Validation Pattern:**
- Issue: Admin checks use `is_admin()` helper function in each handler, but this is a simple `in` check against `bot_config.ADMIN_IDS`. No audit logging of admin actions is performed.
- Files: `handlers/admin_handlers.py:39-40`
- Current mitigation: Admin IDs are stored in configuration, not code.
- Recommendations: Add audit logging for all admin actions.

**Callback Data ID Validation:**
- Issue: Some handlers parse callback data with `split()` and `int()` conversions without try/except. Invalid callback data could cause unhandled exceptions.
- Files: `handlers/game_user_handlers.py:171-173`
- Current mitigation: Telegram usually validates callback data format.
- Recommendations: Wrap callback data parsing in try/except.

---

## Performance Bottlenecks

**Large Question Sets Loaded on Every GameService Instantiation:**
- Issue: `load_trivia_questions()` reads the entire question JSON file from disk. With instance-level caching and no TTL, if `docs/preguntas.json` is large (100+ questions), memory usage grows.
- Files: `services/game_service.py:896-916`
- Cause: Questions are loaded as full JSON objects with all options stored in memory.
- Improvement path: Add LRU cache with TTL to `load_trivia_questions()`, or load questions lazily.

**Database Session Management in Loops:**
- Issue: `_process_pending_requests()` and `_process_expired_subscriptions()` create new sessions for each iteration in loops. While correct, this pattern could be optimized with bulk operations.
- Files: `services/scheduler_service.py:97-167`, `199-253`
- Cause: Processing one subscription at a time with individual commits.
- Improvement path: Batch operations where possible.

**GameService Class-Level Cache Race Condition:**
- Issue: `GameService._active_question_set_path` is a class attribute modified by scheduler jobs (`_sync_question_sets`). If the scheduler syncs while a user is mid-trivia, the question pool changes mid-streak.
- Files: `services/game_service.py:46-47`, `services/scheduler_service.py:312-423`
- Cause: Non-atomic read/write to shared class variable.
- Improvement path: Use atomic operations or a lock around question set switching.

---

## Fragile Areas

**Trivia Discount Tier Calculation:**
- Files: `services/trivia_discount_service.py:557-564`
- Why fragile: `get_tier_for_streak()` iterates tiers in reverse to find the highest matching tier. If tiers are not sorted or have gaps, behavior may be unexpected.
- Safe modification: Always sort tiers before processing, add validation on config creation.

**Handler Creates Service Instance Outside Context Manager:**
- Files: `handlers/game_user_handlers.py:217`, `handlers/game_user_handlers.py:665`, `handlers/game_user_handlers.py:711`, `handlers/game_user_handlers.py:780`
- Why fragile: Several handlers create `GameService()` directly without using `get_service()` context manager, potentially leaking database sessions.
- Safe modification: Always use `with get_service(GameService) as service:` pattern.

**Auto-Reset Duration Calculation:**
- Files: `services/trivia_discount_service.py:226-234`
- Why fragile: `get_time_remaining()` auto-resets with 25% of original duration. This magic number is not configurable and could cause confusion.
- Safe modification: Document this behavior, consider making reset_duration configurable.

---

## Scaling Limits

**FSM State Storage:**
- Current capacity: MemoryStorage limited to single instance memory; RedisStorage limited to Redis memory.
- Limit: When bot reaches ~10,000 concurrent users in trivia streaks, FSM state storage becomes critical.
- Scaling path: Implement RedisStorage with cluster, implement state TTL.

**Database Connection Pool:**
- Current capacity: `pool_size=30, max_overflow=50` for PostgreSQL.
- Limit: ~80 concurrent connections before queuing.
- Scaling path: Increase pool size with PgBouncer or increase Railway PostgreSQL tier.

**Question Set File:**
- Current capacity: Entire JSON loaded into memory per GameService instance.
- Limit: ~5,000 questions before memory becomes concern.
- Scaling path: Implement database-backed questions or paginated loading.

---

## Dependencies at Risk

**aiogram 3.x:**
- Risk: The codebase uses aiogram 3.x which has breaking changes from 2.x. Some deprecated patterns may stop working in future versions.
- Impact: Large refactoring would be needed to upgrade.
- Migration plan: Pin to specific minor version, test upgrades in staging before production.

**APScheduler with SQLAlchemyJobStore:**
- Risk: Job serialization issues require module-level functions. The workaround is fragile and may break with code refactoring.
- Impact: Scheduler jobs may silently fail if serialization issues occur.
- Migration plan: Consider migrating to a more robust job queue (Celery, Dramatiq) for critical jobs.

---

## Missing Critical Features

**Trivia Streak Persistence:**
- Problem: If a user is mid-streak and the bot restarts, they lose their progress.
- Blocks: Users losing accumulated discounts due to infrastructure restarts.

**User Session Continuity:**
- Problem: No mechanism to track user session across bot restarts for ongoing workflows.
- Blocks: Any multi-step user journey (trivia streak, store checkout, story progression).

**Health Checks and Monitoring:**
- Problem: No health endpoint, no metrics, no alerting for scheduler job failures.
- Blocks: Proactive detection of issues before users report them.

---

## Test Coverage Gaps

**Trivia Discount Service:**
- What's not tested: `get_tier_for_streak()`, `get_next_tier()`, `parse_discount_tiers()` with malformed JSON.
- Files: `services/trivia_discount_service.py`
- Risk: Corrupted discount_tiers JSON in database could cause unhandled exceptions.
- Priority: Medium

**Scheduler Job Handlers:**
- What's not tested: `_process_pending_requests()` error handling, `_sync_question_sets()` with concurrent modifications.
- Files: `services/scheduler_service.py`
- Risk: Scheduler jobs silently failing could go unnoticed.
- Priority: Medium

**FSM State Transitions:**
- What's not tested: Timeout handling, state transitions between streak states.
- Files: `handlers/game_user_handlers.py`
- Risk: Race conditions between timeout check and state update could cause inconsistent behavior.
- Priority: High

**Database Session Handling:**
- What's not tested: Session leak scenarios, transaction rollback behavior.
- Files: `services/*.py` (various)
- Risk: Unclosed sessions could cause connection pool exhaustion over time.
- Priority: High

---

*Concerns audit: 2026-05-07*