---
phase: 11
slug: critical-services-tests
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-02
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x + pytest-asyncio |
| **Config file** | `pyproject.toml` (exists — `[tool.pytest.ini_options]`) |
| **Quick run command** | `python -m pytest tests/unit/ -q --tb=short` |
| **Full suite command** | `python -m pytest tests/ -v --tb=short` |
| **Coverage command** | `python -m pytest tests/ --cov=services --cov-report=term-missing` |
| **Estimated runtime** | ~60 seconds (full suite with 9 new test files) |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -q --tb=short`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green + coverage >= 70%
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| TBD-01 | 11-01 | 1 | StoreService | unit | `pytest tests/unit/test_store_service.py -v` | W0 | pending |
| TBD-02 | 11-01 | 1 | Race conditions | unit | `pytest tests/unit/test_store_service.py::TestRaceConditions -v` | W0 | pending |
| TBD-03 | 11-02 | 1 | PromotionService | unit | `pytest tests/unit/test_promotion_service.py -v` | W0 | pending |
| TBD-04 | 11-02 | 1 | BroadcastService | unit | `pytest tests/unit/test_broadcast_service.py -v` | W0 | pending |
| TBD-05 | 11-03 | 1 | StoryService | unit | `pytest tests/unit/test_story_service.py -v` | W0 | pending |
| TBD-06 | 11-03 | 1 | AnalyticsService | unit | `pytest tests/unit/test_analytics_service.py -v` | W0 | pending |
| TBD-07 | 11-03 | 1 | UserService | unit | `pytest tests/unit/test_user_service.py -v` | W0 | pending |
| TBD-08 | 11-04 | 2 | Free channel E2E | integration | `pytest tests/integration/test_free_entry_flow.py -v` | W0 | pending |
| TBD-09 | 11-04 | 2 | VIP ritual E2E | integration | `pytest tests/integration/test_vip_ritual_flow.py -v` | W0 | pending |
| TBD-10 | 11-04 | 2 | LucienVoice | integration | `pytest tests/integration/test_lucien_voice.py -v` | W0 | pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_store_service.py` — stubs + race condition tests
- [ ] `tests/unit/test_promotion_service.py` — stubs
- [ ] `tests/unit/test_broadcast_service.py` — stubs
- [ ] `tests/unit/test_story_service.py` — stubs
- [ ] `tests/unit/test_analytics_service.py` — stubs
- [ ] `tests/unit/test_user_service.py` — stubs
- [ ] `tests/integration/test_free_entry_flow.py` — stubs
- [ ] `tests/integration/test_vip_ritual_flow.py` — stubs
- [ ] `tests/integration/test_lucien_voice.py` — stubs
- [ ] `tests/conftest.py` — add: sample_package, sample_promotion_code, sample_story_node, sample_archetype fixtures
- [ ] `pyproject.toml` — confirm `--cov` / `--strict-markers` / `asyncio_mode` configured

*Existing infrastructure covers all phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Race condition fix verification | StoreService.complete_order | Requires real concurrency (not mocks) | Run `pytest tests/unit/test_store_service.py::TestRaceConditions` — test should FAIL on current code, then PASS after fix |
| LucienVoice consistency | All services | Code audit, not unit test | `grep -rn "mensaje\|bienvenida\|gracias\|error" services/*.py --include="*.py" | grep -v "message\|template\|_msg\|text="` — no results expected |
| Admin wizard E2E | Reward creation wizard | Requires bot context + admin session | Manual test: `/admin` → Rewards → Create → fill all steps |

*Manual verifications are supplementary to automated tests.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
