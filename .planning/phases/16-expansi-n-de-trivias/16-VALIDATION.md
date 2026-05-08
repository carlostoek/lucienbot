# Validation Architecture - Phase 16

**Phase:** 16 - Expansión de Trivias (Trivia Discount System)
**Generated:** 2026-05-08
**Status:** Verified

## Validation Framework

| Property | Value |
|----------|-------|
| Framework | pytest |
| Config | pytest.ini |
| Quick run | `pytest tests/unit/ -x` |
| Full suite | `pytest tests/ -v` |

## Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Command | File |
|--------|----------|-----------|---------|------|
| REQ-16-01 | Player builds streak, gets tier discount at threshold | unit | `pytest tests/unit/test_trivia_discount_service.py::test_streak_tier_reached -x` | tests/unit/test_trivia_discount_service.py |
| REQ-16-02 | Each tier has independent code pool | unit | `pytest tests/unit/test_trivia_discount_service.py::test_tier_pool_independent -x` | tests/unit/test_trivia_discount_service.py |
| REQ-16-03 | Player can retire and claim code | unit | `pytest tests/unit/test_trivia_discount_service.py::test_player_retire -x` | tests/unit/test_trivia_discount_service.py |
| REQ-16-04 | Wrong answer invalidates code | unit | `pytest tests/unit/test_trivia_discount_service.py::test_wrong_answer_invalidates -x` | tests/unit/test_trivia_discount_service.py |
| REQ-16-05 | Admin wizard creates promotion with tiers | integration | `pytest tests/integration/test_trivia_discount_admin.py -x` | tests/integration/test_trivia_discount_admin.py |
| REQ-16-06 | Daily limits respected per user type | unit | `pytest tests/unit/test_trivia_config_service.py::test_daily_limits -x` | tests/unit/test_trivia_config_service.py |
| REQ-16-07 | Atomic code generation prevents duplicates | unit | `pytest tests/unit/test_trivia_discount_service.py::test_code_generation_atomic -x` | tests/unit/test_trivia_discount_service.py |

## Success Criteria Coverage

| CE ID | Criteria | Test Coverage |
|-------|----------|---------------|
| CE-01 | Player completes streak and claims discount | test_player_complete_streak_and_claim (integration) |
| CE-02 | Each tier has independent code pool | test_tier_pool_independent (unit) |
| CE-03 | Admin creates promotion with 3 tiers | test_admin_create_promotion_with_tiers (integration) |
| CE-04 | Exhausted tier no longer offered | test_tier_pool_independent (unit) |
| CE-05 | Daily limits respected | test_daily_limits (unit) |
| CE-06 | 2-minute timeout invalidates code | APScheduler job test (unit) |
| CE-07 | Statistics show codes per tier | test_admin_view_promotion_stats (integration) |

## Wave 0 Gaps

- [ ] `tests/unit/test_trivia_discount_service.py` - covers REQ-16-01 through 04, 07
- [ ] `tests/unit/test_trivia_config_service.py` - covers REQ-16-06
- [ ] `tests/integration/test_trivia_discount_admin.py` - covers REQ-16-05, CE-03, CE-07
- [ ] `tests/integration/test_trivia_discount_player.py` - covers CE-01
- [ ] `tests/unit/test_trivia_models.py` - model behavior tests

## Framework Installation

pytest already in requirements.txt