---
phase: 16
slug: expansion-de-trivias
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-07
---

# Phase 16 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | tests/conftest.py (existing) |
| **Quick run command** | `pytest tests/ -x -q --tb=short` |
| **Full suite command** | `pytest tests/ -v --tb=short` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q --tb=short`
- **After every plan wave:** Run `pytest tests/ -v --tb=short`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 16-01-01 | 16-01 | 1 | Phase 16 success criteria | T-16-01 | N/A (model change) | unit | `pytest tests/test_game_service.py -x -q` | ✅ | ⬜ pending |
| 16-01-02 | 16-01 | 1 | Phase 16 success criteria | T-16-01 | Besitos debited atomically | unit | `pytest tests/test_besito_service.py -x -q` | ✅ | ⬜ pending |
| 16-02-01 | 16-02 | 1 | Phase 16 success criteria | T-16-02 | FSM state isolation | unit | `pytest tests/test_game_user_handlers.py -x -q` | ✅ | ⬜ pending |
| 16-03-01 | 16-03 | 1 | Phase 16 success criteria | T-16-03 | Protection cost validation | integration | `pytest tests/ -k trivia -x -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_game_service.py` — extend for trivia_free, trivia_promo, protection cost
- [ ] `tests/test_besito_service.py` — extend for PROTECTION transaction source
- [ ] `tests/test_game_user_handlers.py` — extend for trivia menu, protection callbacks

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual keyboard layout | UI-SPEC criteria | Requires human judgment | Verify inline keyboard renders correctly in Telegram |
| Promo active detection | Success criterion 1 | Requires promo state | Check menu shows promo button only when `has_active_promo()` returns true |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending