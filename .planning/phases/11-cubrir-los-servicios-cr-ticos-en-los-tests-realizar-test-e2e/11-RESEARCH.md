# Phase 11: Critical Services Test Coverage + E2E Tests - Research

**Researched:** 2026-04-02
**Domain:** Python unit/integration testing with pytest, aiogram async testing, race condition verification
**Confidence:** HIGH

## Summary

The project has a solid pytest-based test infrastructure with SQLite in-memory DB, transaction-per-test isolation, and coverage reporting at 70% fail-under threshold. Nine test files exist across unit and integration directories. The critical gap is that 7 services have zero tests. More critically, several services have documented race conditions that are tested only via mock verification (not actual concurrency) and one confirmed race condition in StoreService.complete_order is not protected by any locking.

**Primary recommendation:** Prioritize StoreService (most critical race condition), PromotionService, and BroadcastService unit tests, then E2E flow coverage. All async methods (PackageService.deliver_package_to_user, RewardService.deliver_reward) need pytest.mark.asyncio tests.

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Cover existing 4 services (VIPService, ChannelService, BesitoService, MissionService) — already tested, verify completeness
- Add StoreService, PromotionService, StoryService, AnalyticsService, UserService, BackupService, BroadcastService, DailyGiftService, RewardService, PackageService coverage
- Test race conditions for store, token redemption, besito transfers
- E2E tests for entry flows (free 30s, VIP 3-phase ritual)

### Claude's Discretion
- How to organize PLAN.md files (number of sub-plans)
- Specific test fixtures to add
- Testing framework setup beyond existing pytest.ini

### Deferred Ideas (OUT OF SCOPE)
- UI/frontend tests, performance/load testing, DB migration tests, Redis-dependent tests, multi-user concurrent stress tests

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REQ-11-01 | Unit tests for StoreService | Confirmed: zero existing tests; critical race condition found in complete_order |
| REQ-11-02 | Unit tests for PromotionService | Confirmed: zero existing tests; express_interest has no locking |
| REQ-11-03 | Unit tests for StoryService | Partial: atomicity tests exist but no CRUD/node/archetype tests |
| REQ-11-04 | Unit tests for AnalyticsService | Confirmed: zero existing tests; only 2 methods need coverage |
| REQ-11-05 | Unit tests for UserService | Confirmed: zero existing tests; 10 methods need coverage |
| REQ-11-06 | Unit tests for DailyGiftService | Confirmed: zero existing tests; 8 methods need coverage |
| REQ-11-07 | Unit tests for BroadcastService | Confirmed: zero existing tests; register_reaction has no locking |
| REQ-11-08 | Unit tests for RewardService | Confirmed: zero existing tests; deliver_reward is async |
| REQ-11-09 | Unit tests for PackageService | Confirmed: zero existing tests; deliver_package_to_user is async |
| REQ-11-10 | E2E free channel entry flow | Confirmed: no E2E tests; scheduler module-level functions testable |
| REQ-11-11 | E2E VIP 3-phase ritual | Confirmed: no E2E tests; handler logic testable with FSM mocks |
| REQ-11-12 | Store race condition test | Critical: confirmed unprotected race in complete_order |
| REQ-11-13 | LucienVoice consistency check | Grep-based test for hardcoded strings in services |
| REQ-11-14 | Cross-service transaction atomicity | StoryService.advance_to_node already has atomicity tests; verify others |

## Standard Stack

### Testing Framework
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | latest | Test runner | Project already uses pytest |
| pytest-asyncio | latest | Async test support | Services have async methods |
| pytest-cov | latest | Coverage reporting | pyproject.toml configures 70% threshold |
| sqlalchemy | (same as project) | DB access in tests | SQLite in-memory for test DB |

**Installation:** Already configured in pyproject.toml. No new installs needed.

**Version verification:** Project uses existing dependencies. Verify pytest-asyncio is installed:
```bash
pip show pytest-asyncio 2>/dev/null | head -1
```

## Architecture Patterns

### Recommended Project Structure (Test Files)
```
tests/
├── unit/
│   ├── test_vip_service.py        # existing - COMPLETE
│   ├── test_channel_service.py    # existing - COMPLETE
│   ├── test_besito_service.py     # existing - COMPLETE
│   ├── test_mission_service.py    # existing - COMPLETE
│   ├── test_store_service.py       # NEW
│   ├── test_promotion_service.py   # NEW
│   ├── test_story_service.py       # existing atomicity - ADD CRUD/archetype
│   ├── test_analytics_service.py   # NEW
│   ├── test_user_service.py        # NEW
│   ├── test_daily_gift_service.py  # NEW
│   ├── test_broadcast_service.py   # NEW
│   ├── test_reward_service.py      # NEW
│   └── test_package_service.py     # NEW
├── integration/
│   ├── test_vip_flow.py           # existing
│   ├── test_free_entry_flow.py     # NEW - E2E free channel
│   └── test_vip_ritual_flow.py     # NEW - E2E VIP 3-phase
├── e2e/
│   ├── test_lucien_voice.py       # NEW - voice consistency
│   └── test_cross_service_atomicity.py  # NEW
└── conftest.py                     # existing - ADD fixtures
```

### Pattern 1: Transaction-Per-Test Isolation (Already in Use)
The existing `conftest.py` db_session fixture creates a new session per test with rollback on teardown. This is the correct pattern for unit tests.

### Pattern 2: Mock Bot for Async Service Tests
`mock_bot` fixture (AsyncMock) should be used for services with async methods (StoreService.complete_order, PackageService.deliver_package_to_user, RewardService.deliver_reward).

### Pattern 3: Race Condition Verification via Mock Chain
Existing pattern in test_vip_service.py and test_besito_service.py: mock the SQLAlchemy query chain to verify `with_for_update()` is called. This verifies locking at the method-call level but does NOT test actual concurrency. For actual concurrency testing, see Section: Race Condition Scenarios.

### Pattern 4: Async Fixture Pattern for E2E Tests
Handlers use aiogram FSM and bot API calls. E2E tests should use:
- `FSMContext` mock for wizard states
- `AsyncMock` for bot API calls
- `db_session` fixture for database assertions

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Async bot API calls in tests | Real bot calls | AsyncMock | Real calls require Telegram API key |
| Database isolation | Shared DB across tests | Transaction-per-test + rollback | SQLite in-memory with session-per-test pattern already exists |
| Concurrent race testing | Actual threading | Mock chain verification | True concurrency testing requires separate DB process and is deferred to Phase 12 |

**Key insight:** The project already has the right patterns. The work is expanding coverage, not inventing new approaches.

## Runtime State Inventory

> This section is not applicable to Phase 11 as it involves adding new tests, not renaming/refactoring/migrating existing runtime state.

## Common Pitfalls

### Pitfall 1: StoreService.complete_order Race Condition
**What goes wrong:** Two concurrent `complete_order` calls both see sufficient balance, both debit, both decrement stock. The debit is protected by `with_for_update` inside `debit_besitos`, but the STOCK DECREMENT happens OUTSIDE the debit transaction. Two threads can both read `stock=1`, both pass, both decrement to `stock=0` (should have been -1).

**Why it happens:** `complete_order` does not use `with_for_update` on the Product query. The stock decrement at `product.stock -= order_item.quantity` is not locked.

**How to avoid:** Add `with_for_update()` to the product query in `complete_order`, OR use a database-level atomic UPDATE with a WHERE clause that checks stock, OR move stock decrement into the same transaction with proper locking.

**Warning signs:** Coverage will show `complete_order` has branches not tested, specifically the stock decrement path under concurrent load.

### Pitfall 2: PromotionService.express_interest Race Condition
**What goes wrong:** Two concurrent calls both check `is_user_blocked` = False and `has_user_expressed_interest` = False, both pass, both create PromotionInterest records. User gets duplicate interest entries.

**Why it happens:** No locking on user interest check + insert sequence.

**How to avoid:** Add unique constraint on (user_id, promotion_id) at DB level AND verify it in service. Alternatively, add `with_for_update` locking.

### Pitfall 3: BroadcastService.register_reaction Race Condition
**What goes wrong:** Two rapid reactions both see `has_user_reacted` = False, both credit besitos, both create reaction records.

**Why it happens:** `has_user_reacted` check and `register_reaction` insert are not atomic.

**How to avoid:** Add `with_for_update` on the BroadcastReaction query, OR unique constraint on (broadcast_id, user_id).

### Pitfall 4: Missing Async Markers on Async Service Tests
**What goes wrong:** Services like `PackageService.deliver_package_to_user` and `RewardService.deliver_reward` are async methods. Tests calling them without `@pytest.mark.asyncio` will silently pass but not actually await the coroutine (in pytest-asyncio auto mode this works, but explicit is better).

**Why it happens:** pyproject.toml has `asyncio_mode = "auto"` so async tests work without the marker. However, the marker is explicit documentation and required by `--strict-markers`.

**How to avoid:** Add `@pytest.mark.asyncio` to all async tests. The `async def test_` convention works in auto mode but violates strict markers.

### Pitfall 5: Incomplete Fixtures for New Models
**What goes wrong:** New tests need fixtures for StoreProduct, Package, PackageFile, Promotion, PromotionInterest, StoryNode, StoryChoice, etc. Without fixtures, each test creates its own data, leading to code duplication and fragile tests.

**Why it happens:** `conftest.py` only has fixtures for VIP/Channel/Besito models.

**How to avoid:** Add fixtures for ALL models used in tests. Follow the existing pattern: each fixture creates an instance, commits, and returns it.

## Code Examples

### Example: StoreService Unit Test Pattern
```python
# tests/unit/test_store_service.py
import pytest
from services.store_service import StoreService
from models.models import StoreProduct, CartItem, Order, OrderStatus, Package

@pytest.mark.unit
class TestStoreService:
    def test_create_product(self, db_session):
        service = StoreService(db_session)
        product = service.create_product(
            name="Test Package",
            description="A test",
            package_id=None,
            price=100
        )
        assert product.id is not None
        assert product.name == "Test Package"
        assert product.stock == -1  # unlimited by default

    def test_add_to_cart_insufficient_balance(self, db_session, sample_user):
        service = StoreService(db_session)
        product = service.create_product(name="Expensive", package_id=None, price=999999, stock=10)
        success, msg = service.add_to_cart(sample_user.id, product.id)
        # Should fail or show error on checkout
```

### Example: Race Condition Mock Verification
```python
# Pattern already in test_vip_service.py — apply to StoreService
def test_complete_order_uses_lock_on_product(self, db_session, sample_balance):
    service = StoreService(db_session)
    # Mock the query chain to verify with_for_update is called on product
    mock_query = MagicMock()
    mock_filtered = MagicMock()
    mock_with_lock = MagicMock()
    mock_first = MagicMock(return_value=mock_product)

    mock_query.filter.return_value = mock_filtered
    mock_filtered.with_for_update.return_value = mock_with_lock
    mock_with_lock.first.return_value = mock_product

    with patch.object(db_session, 'query', return_value=mock_query):
        # Note: This verifies the pattern but doesn't test actual concurrency.
        # For actual concurrency, would need separate DB sessions in threads.
```

### Example: E2E VIP Ritual Flow Test
```python
# tests/integration/test_vip_ritual_flow.py
@pytest.mark.integration
class TestVIPRitualFlow:
    @pytest.mark.asyncio
    async def test_vip_ritual_completes_on_ready(self, db_session, sample_user, sample_subscription, mock_bot):
        """Test: redeem token (stage 1) -> advance (stage 2) -> ready (stage 3, gets link)."""
        vip_service = VIPService(db_session)

        # Stage 1: redeem sets pending_entry, stage=1
        subscription = vip_service.redeem_token("TESTCODE", sample_user.telegram_id)
        assert subscription is not None
        db_session.refresh(sample_user)
        assert sample_user.vip_entry_status == "pending_entry"
        assert sample_user.vip_entry_stage == 1

        # Stage 2: advance_vip_entry_stage
        new_stage = vip_service.advance_vip_entry_stage(sample_user.telegram_id)
        assert new_stage == 2
        db_session.refresh(sample_user)
        assert sample_user.vip_entry_stage == 2

        # Stage 3: complete_vip_entry
        result = vip_service.complete_vip_entry(sample_user.telegram_id)
        assert result is True
        db_session.refresh(sample_user)
        assert sample_user.vip_entry_status == "active"

    @pytest.mark.asyncio
    async def test_vip_ritual_blocked_on_expired_subscription(self, db_session, sample_user, sample_vip_channel):
        """Test: expired subscription blocks ritual continuation."""
        from models.models import Subscription, Token, TokenStatus
        # Create expired subscription
        expired = Subscription(
            user_id=sample_user.id, channel_id=sample_vip_channel.id,
            end_date=datetime.utcnow() - timedelta(days=1), is_active=True
        )
        # Ritual should not proceed
```

### Example: LucienVoice Consistency Grep Test
```python
# tests/e2e/test_lucien_voice.py
@pytest.mark.e2e
class TestLucienVoiceConsistency:
    def test_no_hardcoded_spanish_in_services(self):
        """Grep services/ for hardcoded Spanish strings outside lucien_voice.py."""
        import subprocess
        # Find strings in services that look like user-facing messages
        result = subprocess.run(
            ["grep", "-r", "-n", "--include=*.py",
             "-E", "[A-Z][a-z].*((Ha|El|La|Los|Las|¿|¡|no |si |Su |El )|[aeiou]{3,})",
             "services/", "handlers/"],
            capture_output=True, text=True
        )
        # Filter out: lucien_voice.py, logging, comments, __init__
        lines = [l for l in result.stdout.split("\n")
                 if l and "lucien_voice" not in l
                 and "logger" not in l
                 and "class " not in l
                 and "# " not in l.split(":")[-1]]
        assert len(lines) == 0, f"Hardcoded strings found:\n" + "\n".join(lines[:5])
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|-----------------|--------------|--------|
| No tests | pytest + SQLite in-memory | Phase 1 | Fast, isolated unit tests |
| MagicMock for all | Mock chain verification for with_for_update | Phase 10 security fixes | Confirms locking is used |
| Strict markers disabled | --strict-markers enabled | pyproject.toml | Catches unregistered markers |
| asyncio_mode=auto | asyncio_mode=auto | pyproject.toml | Async tests work without marker |

**Deprecated/outdated:**
- `pytest-asyncio` explicit `pytest.fixture(scope="event_loop")` pattern — not needed with `asyncio_mode = "auto"`
- Patch-based mocking for SQLAlchemy queries — mock chain pattern is clearer

## Open Questions

1. **Should StoreService.complete_order be fixed before or during test writing?**
   - The race condition is a pre-existing bug. The test can verify the current behavior (demonstrating the bug) or assume it's fixed first.
   - Recommendation: Write tests that ASSUME proper locking. If tests fail on the current code, that proves the race condition exists. This aligns with Phase 11's goal of "coverage" — but also consider fixing the race as part of Phase 11.

2. **Should E2E tests use real APScheduler job execution or mock the scheduler?**
   - Real APScheduler execution requires a database connection for SQLAlchemyJobStore and proper bot token setup.
   - Recommendation: Test module-level functions (`_send_free_welcome_job`, `_process_pending_requests`) directly with mocked `_get_bot`, rather than testing through the scheduler.

3. **How to test async handlers (FSM-based wizards)?**
   - Handlers use aiogram FSM (`state.set_state`, `FSMContext`). Testing requires mocking FSMContext.
   - Recommendation: Write integration tests for the service layer (VIPService, ChannelService) that verify state transitions, and E2E tests for handler output (mock bot.send_message assertions).

4. **Is the `asyncio_mode = "auto"` in pyproject.toml compatible with `@pytest.mark.asyncio` strict markers?**
   - Yes. Auto mode means `async def test_` functions are automatically treated as async. The marker is still honored. However, with `--strict-markers`, ALL async test functions should either use the marker OR the project should remove `--strict-markers`.
   - Recommendation: Add `@pytest.mark.asyncio` to all async tests for explicitness and strict-marker compliance.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| pytest | All tests | check: `pytest --version` | configured | — |
| pytest-asyncio | Async service tests | check: `pip show pytest-asyncio` | configured | — |
| pytest-cov | Coverage reporting | check: `pip show pytest-cov` | configured | — |
| SQLite | In-memory test DB | built-in (Python stdlib) | 3.x | — |
| Python 3.12+ | Project requirement | `python3 --version` | 3.12+ | — |

**Missing dependencies with no fallback:**
- None — all test infrastructure is configured in pyproject.toml

**Missing dependencies with fallback:**
- None

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio |
| Config file | pyproject.toml (tool.pytest.ini_options) |
| Quick run command | `pytest tests/unit/ -x -q --no-cov` |
| Full suite command | `pytest tests/ -v --cov=services --cov=models --cov=handlers --cov-report=term-missing` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|---------------|
| REQ-11-01 | StoreService CRUD + transactions | unit | `pytest tests/unit/test_store_service.py -x` | NO - NEW |
| REQ-11-02 | PromotionService CRUD + interest | unit | `pytest tests/unit/test_promotion_service.py -x` | NO - NEW |
| REQ-11-03 | StoryService nodes + archetypes | unit | `pytest tests/unit/test_story_service.py -x` | PARTIAL - ADD |
| REQ-11-04 | AnalyticsService metrics + CSV | unit | `pytest tests/unit/test_analytics_service.py -x` | NO - NEW |
| REQ-11-05 | UserService CRUD + roles | unit | `pytest tests/unit/test_user_service.py -x` | NO - NEW |
| REQ-11-06 | DailyGiftService claim + cooldown | unit | `pytest tests/unit/test_daily_gift_service.py -x` | NO - NEW |
| REQ-11-07 | BroadcastService reactions | unit | `pytest tests/unit/test_broadcast_service.py -x` | NO - NEW |
| REQ-11-08 | RewardService deliver types | unit | `pytest tests/unit/test_reward_service.py -x` | NO - NEW |
| REQ-11-09 | PackageService CRUD + delivery | unit | `pytest tests/unit/test_package_service.py -x` | NO - NEW |
| REQ-11-10 | Free entry 30s + approve flow | integration | `pytest tests/integration/test_free_entry_flow.py -x` | NO - NEW |
| REQ-11-11 | VIP 3-phase ritual completion | integration | `pytest tests/integration/test_vip_ritual_flow.py -x` | NO - NEW |
| REQ-11-12 | Store stock race condition | unit | `pytest tests/unit/test_store_service.py::TestRaceConditions -x` | NO - NEW |
| REQ-11-13 | LucienVoice hardcoded strings | e2e | `pytest tests/e2e/test_lucien_voice.py -x` | NO - NEW |
| REQ-11-14 | Cross-service atomicity | integration | `pytest tests/integration/test_cross_service.py -x` | NO - NEW |

### Sampling Rate
- **Per task commit:** `pytest tests/unit/ -x -q --no-cov` (< 30s expected)
- **Per wave merge:** `pytest tests/ -v --cov=services --cov=models --cov=handlers` (< 2 min expected)
- **Phase gate:** Full suite green + coverage >= 70% before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_store_service.py` — covers REQ-11-01, REQ-11-12
- [ ] `tests/unit/test_promotion_service.py` — covers REQ-11-02
- [ ] `tests/unit/test_analytics_service.py` — covers REQ-11-04
- [ ] `tests/unit/test_user_service.py` — covers REQ-11-05
- [ ] `tests/unit/test_daily_gift_service.py` — covers REQ-11-06
- [ ] `tests/unit/test_broadcast_service.py` — covers REQ-11-07
- [ ] `tests/unit/test_reward_service.py` — covers REQ-11-08
- [ ] `tests/unit/test_package_service.py` — covers REQ-11-09
- [ ] `tests/integration/test_free_entry_flow.py` — covers REQ-11-10
- [ ] `tests/integration/test_vip_ritual_flow.py` — covers REQ-11-11
- [ ] `tests/e2e/test_lucien_voice.py` — covers REQ-11-13
- [ ] `tests/conftest.py` — ADD fixtures: sample_store_product, sample_package, sample_promotion, sample_story_node, sample_archetype, sample_daily_gift_claim
- [ ] Framework install: `pip install pytest-asyncio pytest-cov` — verify if not already installed

*(Existing test infrastructure covers: VIPService, ChannelService, BesitoService, MissionService, Scheduler, RateLimit, BackupService, StoryService atomicity)*

## Existing Coverage Audit

### COMPLETE (Existing Tests That Satisfy Requirements)
| Service | Test File | Lines | Coverage |
|---------|-----------|-------|----------|
| VIPService | test_vip_service.py | ~488 | COMPLETE - tariffs, tokens, subscriptions, VIP entry state, race conditions (mock) |
| ChannelService | test_channel_service.py | ~287 | COMPLETE - channels, pending requests, auto-approval |
| BesitoService | test_besito_service.py | ~355 | COMPLETE - balance, transactions, history, stats, debit commit param |
| MissionService | test_mission_service.py | ~305 | COMPLETE - CRUD, progress, increment, set_progress, stats |
| Scheduler | test_scheduler.py | ~87 | COMPLETE - trigger verification, Telegram channel ID bug regression |
| RateLimit | test_rate_limit_middleware.py | ~180 | COMPLETE - per-user limiters, admin bypass, idle cleanup |
| BackupService | test_backup_service.py | ~129 | COMPLETE - PGPASSWORD env var, credential extraction, error handling |
| StoryService | test_story_service.py | ~189 | PARTIAL - atomicity of advance_to_node, BigInteger overflow only. Missing: node CRUD, archetype quiz, story branching, achievement system |

### ZERO Coverage (No Tests)
| Service | Methods to Cover | Priority |
|---------|-----------------|----------|
| StoreService | create_product, add_to_cart, create_order, complete_order, stock management | CRITICAL - has race condition |
| PromotionService | create_promotion, express_interest, block_user, is_user_blocked | HIGH - has race condition |
| BroadcastService | register_reaction, create_broadcast_message, has_user_reacted | MEDIUM - has race condition |
| PackageService | create_package, add_file_to_package, deliver_package_to_user (async), stock mgmt | HIGH - async |
| RewardService | create_reward_*, deliver_reward (async), deliver types (besitos/package/VIP) | HIGH - async |
| UserService | create_user, get_or_create_user, is_admin, set_admin, role management | MEDIUM |
| DailyGiftService | can_claim, claim_gift, get_last_claim, get_config, cooldown logic | MEDIUM |
| AnalyticsService | get_dashboard_stats, export_users_csv, export_activity_csv | LOW - 3 methods only |

### Partial Coverage
| Service | Missing | Priority |
|---------|---------|----------|
| StoryService | create_node, get_node_choices, advance_to_node (node loading, archetype calc, achievement grants), archetype quiz, story stats | HIGH |

## Sources

### Primary (HIGH confidence)
- Project pyproject.toml — test configuration, coverage thresholds
- tests/conftest.py — existing fixture patterns
- tests/unit/test_vip_service.py — VIPService test patterns (mock chain for with_for_update)
- services/store_service.py — confirmed race condition at `product.stock -=`
- services/promotion_service.py — confirmed no locking on express_interest
- services/broadcast_service.py — confirmed no locking on register_reaction

### Secondary (MEDIUM confidence)
- Project CLAUDE.md — architecture rules, service patterns
- services/CLAUDE.md — complete list of services and their methods
- handlers/CLAUDE.md — handler patterns (no business logic in handlers)
- utils/lucien_voice.py — all message templates, confirms voice consistency scope

### Tertiary (LOW confidence)
- Grep-based hardcoded string detection — regex approach may have false positives/negatives, needs validation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — pytest infrastructure already configured and working
- Architecture: HIGH — existing patterns are excellent, no invention needed
- Pitfalls: HIGH — race conditions confirmed by reading source code directly
- Missing services: HIGH — confirmed by directory listing + no test files exist

**Research date:** 2026-04-02
**Valid until:** 90 days (testing infrastructure is stable, Python/pytest ecosystem moves slowly)
