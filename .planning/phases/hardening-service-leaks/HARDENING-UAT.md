---
status: pass
phase: hardening-service-leaks
source: telegram-bot-hardener skill
started: 2026-05-07T00:00:00Z
updated: 2026-05-07T00:00:00Z
---

## Tests

### 1. GameService Leaks — No Direct Instantiation
expected: |
  game_user_handlers.py must not have `= GameService()` outside of `with get_service(GameService)`.
  All 4 instances of direct instantiation (lines ~217, ~665, ~711, ~780) must be replaced
  with `random.choice(GameService.STREAK_TEMPLATES[...])` to avoid creating unnecessary DB sessions.
result: pass
evidence: |
  - test_no_direct_gameservice_instantiation_in_game_handlers: PASS
  - test_streak_handlers_use_class_templates_not_instance: PASS
  - Confirmed: `random.choice(GameService.STREAK_TEMPLATES)` found in source

### 2. GameService Leaks — streak_continue_wrong Handler
expected: Handler uses `random.choice(GameService.STREAK_TEMPLATES[...])` instead of `GameService()`.
result: pass
evidence: |
  grep confirmed: `header = random.choice(GameService.STREAK_TEMPLATES['continue_wrong_header'])`
  No `= GameService()` found in this handler.

### 3. GameService Leaks — streak_retire Handler
expected: Handler uses `random.choice(GameService.STREAK_TEMPLATES[...])` instead of `GameService()`.
result: pass
evidence: |
  grep confirmed: `header = random.choice(GameService.STREAK_TEMPLATES['retire_success_header'])`
  No `= GameService()` found in this handler.

### 4. GameService Leaks — streak_exit Handler
expected: Handler uses `random.choice(GameService.STREAK_TEMPLATES[...])` instead of `GameService()`.
result: pass
evidence: |
  grep confirmed: `header = random.choice(GameService.STREAK_TEMPLATES['exit_header'])`
  No `= GameService()` found in this handler.

### 5. GameService Leaks — streak_continue Handler
expected: Handler uses `random.choice(GameService.STREAK_TEMPLATES[...])` instead of `GameService()`.
result: pass
evidence: |
  grep confirmed: `header = random.choice(GameService.STREAK_TEMPLATES['continue_header'])`
  No `= GameService()` found in this handler.

### 6. VIPService Leaks — show_node Handler
expected: |
  show_node() creates `VIPService()` inside `with get_service(StoryService)` but must call
  `vip_service.close()` in a `finally` block to prevent connection leaks.
result: pass
evidence: |
  - test_vip_service_properly_closed_in_show_node: PASS
  - grep confirmed: `finally:` + `vip_service.close()` at lines 233-234
  - Function structure verified with inspect.getsource()

### 7. VIPService Leaks — make_choice Handler
expected: |
  make_choice() creates `VIPService()` inside `with get_service(StoryService)` but must call
  `vip_service.close()` in a `finally` block to prevent connection leaks.
result: pass
evidence: |
  - test_vip_service_properly_closed_in_make_choice: PASS
  - grep confirmed: `finally:` + `vip_service.close()` at lines 298-299
  - Function structure verified with inspect.getsource()

### 8. VIPService Leaks — All Instantiations Protected
expected: All VIPService() instantiations in story_user_handlers.py must have close() in their function.
result: pass
evidence: |
  - test_all_vip_service_instantiations_have_close: PASS
  - Verified show_node() and make_choice() both have vip_service.close()

---

## Summary

total: 8
passed: 8
issues: 0
pending: 0
skipped: 0

---

## Artifacts

### Fixed Files
- `handlers/game_user_handlers.py` — Removed 4 `GameService()` instantiations, replaced with `random.choice(GameService.TEMPLATES[...])`
- `handlers/story_user_handlers.py` — Added `try/finally` with `vip_service.close()` in `show_node()` and `make_choice()`

### New Files
- `tests/unit/test_handler_service_leaks.py` — Regression tests for service leak detection

---

## Regression Tests

File: `tests/unit/test_handler_service_leaks.py`

| Test | Purpose | Result |
|------|---------|--------|
| test_no_direct_gameservice_instantiation_in_game_handlers | Verify no `= GameService()` outside context manager | PASS |
| test_streak_handlers_use_class_templates_not_instance | Verify use of `random.choice(GameService.STREAK_TEMPLATES)` | PASS |
| test_vip_service_properly_closed_in_show_node | Verify `try/finally` with `vip_service.close()` | PASS |
| test_vip_service_properly_closed_in_make_choice | Verify `try/finally` with `vip_service.close()` | PASS |
| test_all_vip_service_instantiations_have_close | Verify all VIPService() have close() in parent function | PASS |
