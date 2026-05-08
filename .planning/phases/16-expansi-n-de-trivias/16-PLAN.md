---
phase: 16
plan: Expansión de Trivias (Trivia Discount System)
type: feature
wave: 1
depends_on: []
files_modified:
  - "models/models.py"
  - "services/game_service.py"
  - "handlers/game_user_handlers.py"
  - "keyboards/inline_keyboards.py"
  - "bot.py"
  - "utils/lucien_voice.py"
autonomous: false
must_haves:
  - "TriviaPromotionConfig model (NEW, separate from commercial Promotion)"
  - "Tier model with independent code pool per tier"
  - "DiscountCode model with AVAILABLE/CLAIMED/USED/CANCELLED/EXPIRED status"
  - "UserStreak model with streak tracking"
  - "TriviaGameRecord model for game history"
  - "QuestionSet and Question models for themed question loading"
  - "TriviaConfig singleton for daily limits"
  - "TriviaDiscountService with atomic code generation (SELECT FOR UPDATE)"
  - "GameService expanded with trivia discount gameplay"
  - "QuestionSetService for JSON question loading"
  - "TriviaAdminService for admin operations"
  - "TriviaDiscountAdminHandlers with 6-step wizard FSM"
  - "TriviaDiscountUserHandlers with player FSM (idle/waiting_answer/streak_choice/waiting_retire)"
  - "APScheduler integration for 2-minute streak timeout"
  - "Unit tests for atomic code gen, tier independence, streak logic"
  - "Integration tests for admin wizard and player flow"
---

# Phase 16: Expansión de Trivias (Trivia Discount System)

## Context
- **Phase:** 16
- **Goal:** Implement gambling-style trivia with progressive discount tiers, completely separate from commercial PromotionService
- **Input:** Updated RESEARCH.md at `16-RESEARCH.md`, SPEC.md
- **Key Clarification:** TriviaDiscountService is COMPLETELY SEPARATE from commercial PromotionService — different models, different code paths

## Architectural Principle
**Trivia Promotion != Commercial Promotion**
- `PromotionService` (existing) — "Me Interesa" for MXN peso purchases
- `TriviaDiscountService` (NEW) — Streak-building trivia with discount codes
- No shared code, no shared models, no shared flows

---

## Phase Summary

| Aspect | Detail |
|--------|--------|
| **Models** | 8 new models (TriviaPromotionConfig, Tier, DiscountCode, UserStreak, TriviaGameRecord, QuestionSet, Question, TriviaConfig) |
| **Services** | 4 new/expanded (TriviaDiscountService, GameService expanded, QuestionSetService, TriviaAdminService) |
| **Handlers** | 2 new (trivia_discount_admin_handlers.py, trivia_discount_user_handlers.py) |
| **Tests** | Unit + Integration as specified in verification checkpoints |
| **Integration** | APScheduler for streak timeout, existing GameRecord extended |

---

## Layer 1: Models

<task>
<id>1.1</id>
<layer>Models</layer>
<title>Add Enums for Trivia Discount System</title>
<description>Add DiscountCodeStatus and GameResult enums before model definitions</description>
<files>["models/models.py"]</files>
<verification>Enums usable in model definitions</verification>
<checkpoint>checkpoint:human-verify</checkpoint>
</task>

<task>
<id>1.2</id>
<layer>Models</layer>
<title>Add TriviaPromotionConfig Model</title>
<description>Promotion config for trivia discounts (completely separate from Promotion model)</description>
<files>["models/models.py"]</files>
<verification>Model exists, relationships work</verification>
<checkpoint>checkpoint:human-verify</checkpoint>
</task>

<task>
<id>1.3</id>
<layer>Models</layer>
<title>Add Tier Model</title>
<description>Discount tier with independent code pool</description>
<files>["models/models.py"]</files>
<verification>Tier.codes_generated tracks independently per tier</verification>
<checkpoint>checkpoint:human-verify</checkpoint>
</task>

<task>
<id>1.4</id>
<layer>Models</layer>
<title>Add DiscountCode Model</title>
<description>Individual discount code with status tracking</description>
<files>["models/models.py"]</files>
<verification>Code status transitions correctly</verification>
<checkpoint>checkpoint:human-verify</checkpoint>
</task>

<task>
<id>1.5</id>
<layer>Models</layer>
<title>Add UserStreak Model</title>
<description>Active streak tracking per user per promotion</description>
<files>["models/models.py"]</files>
<verification>Streak increments/resets correctly</verification>
<checkpoint>checkpoint:human-verify</checkpoint>
</task>

<task>
<id>1.6</id>
<layer>Models</layer>
<title>Add TriviaGameRecord Model</title>
<description>Game history (separate from existing GameRecord for dice/trivia besitos)</description>
<files>["models/models.py"]</files>
<verification>Records created with correct fields</verification>
<checkpoint>checkpoint:human-verify</checkpoint>
</task>

<task>
<id>1.7</id>
<layer>Models</layer>
<title>Add QuestionSet and Question Models</title>
<description>Themed question groups loaded from JSON</description>
<files>["models/models.py"]</files>
<verification>Questions load from JSON via QuestionSetService</verification>
<checkpoint>checkpoint:human-verify</checkpoint>
</task>

<task>
<id>1.8</id>
<layer>Models</layer>
<title>Add TriviaConfig Singleton</title>
<description>Global trivia configuration (daily limits, streak timeout)</description>
<files>["models/models.py"]</files>
<verification>Config editable by admin</verification>
<checkpoint>checkpoint:human-verify</checkpoint>
</task>

<task>
<id>1.9</id>
<layer>Models</layer>
<title>Create Alembic Migrations</title>
<description>All 8 models migratable</description>
<files>["alembic/versions/*.py"]</files>
<verification>alembic upgrade head succeeds</verification>
<checkpoint>checkpoint:human-verify</checkpoint>
</task>

---

## Layer 2: Services

<task>
<id>2.1</id>
<layer>Services</layer>
<title>Implement TriviaDiscountService</title>
<description>Core business logic for promotions, tiers, and discount codes with atomic code generation</description>
<files>["services/trivia_discount_service.py"]</files>
<verification>Unit tests pass for atomic code gen and tier pool independence</verification>
<checkpoint>checkpoint:human-verify</checkpoint>
</task>

<task>
<id>2.2</id>
<layer>Services</layer>
<title>Expand GameService for Trivia Discount</title>
<description>Add trivia discount gameplay to existing GameService</description>
<files>["services/game_service.py"]</files>
<verification>Player flow works: entry → question → answer → streak update → tier threshold choice</verification>
<checkpoint>checkpoint:human-verify</checkpoint>
</task>

<task>
<id>2.3</id>
<layer>Services</layer>
<title>Implement QuestionSetService</title>
<description>Load questions from JSON files</description>
<files>["services/question_set_service.py"]</files>
<verification>Questions load correctly from JSON</verification>
<checkpoint>checkpoint:human-verify</checkpoint>
</task>

<task>
<id>2.4</id>
<layer>Services</layer>
<title>Implement TriviaAdminService</title>
<description>Admin operations for trivia system</description>
<files>["services/trivia_admin_service.py"]</files>
<verification>Admin can view stats and export CSV</verification>
<checkpoint>checkpoint:human-verify</checkpoint>
</task>

<task>
<id>2.5</id>
<layer>Services</layer>
<title>Integrate Streak Timeout with APScheduler</title>
<description>2-minute timeout invalidates active streak</description>
<files>["services/scheduler_service.py"]</files>
<verification>Streak invalidates after 2 minutes of inactivity</verification>
<checkpoint>checkpoint:human-verify</checkpoint>
</task>

---

## Layer 3: Handlers

<task>
<id>3.1</id>
<layer>Handlers</layer>
<title>Implement TriviaDiscountAdminHandlers</title>
<description>6-step wizard for creating trivia promotions</description>
<files>["handlers/trivia_discount_admin_handlers.py"]</files>
<verification>Admin can create promotion with 3 tiers in wizard</verification>
<checkpoint>checkpoint:human-verify</checkpoint>
</task>

<task>
<id>3.2</id>
<layer>Handlers</layer>
<title>Implement TriviaDiscountUserHandlers</title>
<description>Player FSM for trivia discount gameplay</description>
<files>["handlers/trivia_discount_user_handlers.py"]</files>
<verification>Player can complete streak and claim discount code</verification>
<checkpoint>checkpoint:human-verify</checkpoint>
</task>

<task>
<id>3.3</id>
<layer>Handlers</layer>
<title>Add Trivia Discount Menu Entry</title>
<description>Add "Trivia Descuentos" to games menu (separate from existing "Trivia" for besitos)</description>
<files>["handlers/game_user_handlers.py"]</files>
<verification>Both trivia entries appear in games menu</verification>
<checkpoint>checkpoint:human-verify</checkpoint>
</task>

---

## Layer 4: Tests

<task>
<id>4.1</id>
<layer>Tests</layer>
<title>Unit Tests - TriviaDiscountService</title>
<description>Core business logic tested</description>
<files>["tests/unit/test_trivia_discount_service.py"]</files>
<verification>pytest tests/unit/test_trivia_discount_service.py -x passes</verification>
<checkpoint>checkpoint:human-verify</checkpoint>
</task>

<task>
<id>4.2</id>
<layer>Tests</layer>
<title>Unit Tests - TriviaConfigService</title>
<description>Daily limits respected per user type</description>
<files>["tests/unit/test_trivia_config_service.py"]</files>
<verification>pytest tests/unit/test_trivia_config_service.py -x passes</verification>
<checkpoint>checkpoint:human-verify</checkpoint>
</task>

<task>
<id>4.3</id>
<layer>Tests</layer>
<title>Unit Tests - Models</title>
<description>Models behave correctly</description>
<files>["tests/unit/test_trivia_models.py"]</files>
<verification>pytest tests/unit/test_trivia_models.py -x passes</verification>
<checkpoint>checkpoint:human-verify</checkpoint>
</task>

<task>
<id>4.4</id>
<layer>Tests</layer>
<title>Integration Tests - Admin Wizard</title>
<description>6-step wizard creates promotion correctly</description>
<files>["tests/integration/test_trivia_discount_admin.py"]</files>
<verification>pytest tests/integration/test_trivia_discount_admin.py -x passes</verification>
<checkpoint>checkpoint:human-verify</checkpoint>
</task>

<task>
<id>4.5</id>
<layer>Tests</layer>
<title>Integration Tests - Player Flow</title>
<description>Complete player flow tested</description>
<files>["tests/integration/test_trivia_discount_player.py"]</files>
<verification>pytest tests/integration/test_trivia_discount_player.py -x passes</verification>
<checkpoint>checkpoint:human-verify</checkpoint>
</task>

---

## Layer 5: Integration Points

<task>
<id>5.1</id>
<layer>Integration</layer>
<title>Keyboard Inline Updates</title>
<description>Add trivia discount keyboards</description>
<files>["keyboards/inline_keyboards.py"]</files>
<verification>Keyboards render correctly in mockups</verification>
<checkpoint>checkpoint:human-verify</checkpoint>
</task>

<task>
<id>5.2</id>
<layer>Integration</layer>
<title>Register Handlers in Bot</title>
<description>Handlers available in bot</description>
<files>["bot.py"]</files>
<verification>Bot responds to trivia discount commands</verification>
<checkpoint>checkpoint:human-verify</checkpoint>
</task>

<task>
<id>5.3</id>
<layer>Integration</layer>
<title>Voice/Templates for Trivia Discount</title>
<description>Consistent Lucien voice in trivia discount</description>
<files>["utils/lucien_voice.py"]</files>
<verification>Templates render correctly</verification>
<checkpoint>checkpoint:human-verify</checkpoint>
</task>

---

## Verification Summary

| Layer | Tasks | Files | Checkpoints |
|-------|-------|-------|-------------|
| Models | 9 | 9 (+ 1 migration file) | 9 human-verify |
| Services | 5 | 4 (+ 1 expand) | 5 human-verify |
| Handlers | 3 | 2 (+ 1 modify) | 3 human-verify |
| Tests | 5 | 5 | 5 human-verify |
| Integration | 3 | 3 | 3 human-verify |
| **Total** | **25** | **24** | **25** |

---

## Success Criteria (from SPEC.md Section 10)

| ID | Criteria | Validation |
|----|----------|------------|
| CE-01 | Un jugador puede completar una racha y reclamar un descuento | Test E2E |
| CE-02 | Cada tier tiene pool independiente de códigos | Test unitario |
| CE-03 | Admin puede crear promoción con 3 tiers, cada uno con cantidad diferente de códigos | Test E2E |
| CE-04 | Al agotar códigos de un tier, ese tier ya no se ofrece | Test unitario |
| CE-05 | Los límites diarios se respetan | Test unitario |
| CE-06 | El timeout de 2 min invalida el código | Test |
| CE-07 | Estadísticas muestran códigos por tier | Test E2E |

---

## File Summary

**NEW Files:**
- `models/models.py` (expand with 8 new models/enums)
- `services/trivia_discount_service.py`
- `services/question_set_service.py`
- `services/trivia_admin_service.py`
- `services/game_service.py` (expand)
- `handlers/trivia_discount_admin_handlers.py`
- `handlers/trivia_discount_user_handlers.py`
- `tests/unit/test_trivia_discount_service.py`
- `tests/unit/test_trivia_config_service.py`
- `tests/unit/test_trivia_models.py`
- `tests/integration/test_trivia_discount_admin.py`
- `tests/integration/test_trivia_discount_player.py`
- `alembic/versions/???_add_trivia_discount_models.py`

**MODIFY Files:**
- `models/models.py`
- `services/game_service.py`
- `handlers/game_user_handlers.py`
- `keyboards/inline_keyboards.py`
- `bot.py`
- `utils/lucien_voice.py`