# Phase 16: Expansión de Trivias - Research

**Researched:** 2026-05-08
**Domain:** Trivia Discount System (gambling-style trivia with progressive discount tiers)
**Confidence:** HIGH (verified against SPEC.md, existing trivia codebase, and trivia-timeout worktree)

## User Constraints (from CONTEXT.md)

### Locked Decisions
- TriviaDiscountService, GameService (expanded), TriviaAdminService architecture
- Streak-based tier system with independent code pools per tier
- 2-minute streak timeout with APScheduler
- FSM player flow: idle → waiting_answer → (streak_choice | game_over) → waiting_retire → idle
- Admin wizard with specific steps defined in SPEC.md section 5.2

### Claude's Discretion
- File structure (follow existing patterns)
- FSM storage (MemoryStorage or RedisStorage)
- Specific implementation patterns for models, services, handlers

### Deferred Ideas
- Trivia VIP (separate spec later)
- Besitos/rewards system (already exists)
- Narrative/stories (already exists)

---

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REQ-16-01 | Gambling-style trivia with streak thresholds | game_service.py trivia pattern + SPEC.md section 2.1 |
| REQ-16-02 | Discount tiers with independent code pools | TriviaPromotionConfig model from worktree, SPEC.md section 3.2 |
| REQ-16-03 | Player choice: retire with code or continue gambling | SPEC.md section 2.1 flow diagram |
| REQ-16-04 | 2-minute streak timeout invalidates code | SPEC.md section 4.5, APScheduler pattern |
| REQ-16-05 | Admin 17-step promotion creation wizard | PromotionWizardStates pattern in promotion_admin_handlers.py |
| REQ-16-06 | Daily limits by user type (free/VIP) | TriviaConfig singleton pattern, existing GameService limits |
| REQ-16-07 | Tier pool independence (atomic code generation) | SELECT FOR UPDATE pattern from StoreService |

---

## Summary

Phase 16 implements a **gambling-style trivia** where players build streaks of correct answers to unlock progressively higher discount tiers. Each tier has its own independent pool of codes — when a tier is exhausted, it's no longer offered. Players can retire and claim their discount or continue gambling for higher tiers. Wrong answer = streak reset + code invalidated. 2-minute timeout = code expired.

**Key distinction from existing trivia:** The current `game_service.py` trivia is simple "play for besitos" with streak counting but no discount codes, no tiers, no player choice, and no timeout. Phase 16 is a **separate system** with its own models, services, FSM states, and player flows.

**Primary recommendation:** Adopt the trivia-timeout worktree's patterns for TriviaPromotionConfig, QuestionSet, and TriviaConfig singleton, but adapt the model names and relationships to match SPEC.md exactly. Use the existing PromotionWizardStates as reference for the 17-step admin wizard.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Discount code generation | API/Backend | — | TriviaDiscountService.generate_code() with atomic lock |
| Streak tracking | API/Backend | — | UserStreak model, updated per answer |
| Streak timeout | API/Backend | — | APScheduler job triggers invalidate_streak() |
| Tier pool management | API/Backend | — | TriviaDiscountService.get_available_codes_count() |
| Question loading | API/Backend | — | QuestionSet loads from JSON, GameService uses it |
| Player FSM | API/Backend | — | TriviaStreakStates in handlers, MemoryStorage/RedisStorage |
| Admin wizard | API/Backend | — | TriviaDiscountStates FSM, 17 steps |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| aiogram 3.x | 3.4+ | Telegram bot framework | Project uses aiogram for all handlers |
| SQLAlchemy | 2.x | ORM for database models | Same as existing models.py |
| Alembic | — | Database migrations | Existing migration infrastructure |
| APScheduler | — | Streak timeout jobs | Already used in SchedulerService |

### Existing Patterns (to leverage)
| Pattern | Source | Usage |
|---------|--------|-------|
| Wizard FSM | `promotion_admin_handlers.py` PromotionWizardStates | 17-step admin creation flow |
| Service-with-service | `daily_gift_service.py` embeds BesitoService | TriviaDiscountService can embed GameService |
| Atomic code generation | `store_service.py` create_product (SELECT FOR UPDATE) | Code pool concurrency |
| Singleton config | `trivia-timeout/worktrees/trivia_config_service.py` | TriviaConfig for daily limits |
| QuestionSet loading | `game_service.py` load_trivia_questions() | Load questions from JSON |

**Installation:**
```bash
# No new packages needed - all existing
```

## Architecture Patterns

### Recommended Project Structure
```
services/
├── trivia_discount_service.py      # NEW - promotion config, tiers, codes
├── question_set_service.py         # NEW - themed question groups (from worktree)
├── trivia_config_service.py        # NEW - singleton config for limits (from worktree)
models/
├── models.py                       # MODIFY - add TriviaPromotionConfig, Tier, DiscountCode, UserStreak, QuestionSet, Question, TriviaConfig
handlers/
├── trivia_discount_admin_handlers.py  # NEW - admin wizard (from worktree)
├── trivia_discount_user_handlers.py   # NEW - player FSM
keyboards/
├── inline_keyboards.py              # MODIFY - add trivia discount keyboards
```

### Pattern 1: TriviaDiscountService (from trivia-timeout worktree)
```python
# services/trivia_discount_service.py - manages promotions, tiers, codes
class TriviaDiscountService:
    def create_trivia_promotion_config(self, name, discount_tiers, ...) -> Optional[TriviaPromotionConfig]
    def generate_code(self, tier_id, user_id) -> Optional[DiscountCode]  # atomic with lock
    def claim_code(self, code_id) -> bool
    def invalidate_streak(self, user_id) -> None  # called by APScheduler job
```

**When to use:** Managing discount code pools per tier, concurrency-safe code generation.

### Pattern 2: Player FSM (TriviaStreakStates)
```python
# From trivia-timeout worktree handlers/game_user_handlers.py
class TriviaStreakStates(StatesGroup):
    waiting_answer = State()
    streak_choice = State()  # reached threshold, player chooses
    streak_continue = State()  # player chose to continue
    waiting_retire = State()

# Flow: idle → waiting_answer → (streak_choice | game_over)
#                             ↓
#                     waiting_retire → idle
```

**When to use:** Player completes streak threshold, shown discount offer with Continue/Retire/Salir buttons.

### Pattern 3: Admin Wizard (TriviaDiscountStates from worktree)
```python
# 17-step wizard matching SPEC.md section 5.2
class TriviaDiscountStates(StatesGroup):
    waiting_promotion_type = State()      # Fixed / Relative
    waiting_dates_or_duration = State()
    waiting_name = State()
    waiting_description = State()
    waiting_discount_tiers = State()      # NEW: multi-tier support
    waiting_question_set = State()
    waiting_confirmation = State()
```

**When to use:** Admin creates promotion with tiers, each tier having streak_threshold + discount_percentage + max_codes.

### Pattern 4: Atomic Code Generation (from StoreService)
```python
# Pattern: SELECT FOR UPDATE for atomic code reservation
def generate_code(self, tier_id: int, user_id: int) -> Optional[DiscountCode]:
    with self._get_db() as session:
        # Lock the tier row to prevent concurrent generation
        tier = session.query(Tier).filter(Tier.id == tier_id).with_for_update().first()
        if not tier or tier.available_count <= 0:
            return None
        # Generate code, decrement count, commit
```

**When to use:** Ensuring two players don't get the same code when they hit the threshold simultaneously.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Streak persistence | In-memory tracking | UserStreak model in DB | Survives bot restart, tracks across sessions |
| Code generation | Random without lock | SELECT FOR UPDATE | Concurrency safety, no duplicate codes |
| Streak timeout | Polling/sleep | APScheduler job | Non-blocking, survives restart, precision |
| Admin wizard | Callback spaghetti | FSM StatesGroup | Clean state management, back navigation |
| Config management | Hardcoded constants | TriviaConfig singleton | Runtime changes, no deploy needed |

**Key insight:** The trivia-timeout worktree has already solved most of these problems. Adapt its patterns rather than inventing new solutions.

## Common Pitfalls

### Pitfall 1: Confusion Between Existing Trivia and New Trivia Discount System
**What goes wrong:** Developers try to merge the two systems instead of treating them as separate
**Why it happens:** Both use "trivia" in the name and share some question-loading code
**How to avoid:** Clear separation: `game_service.py` = simple trivia, `trivia_discount_service.py` = gambling-style with codes
**Warning signs:** Trying to add tiers to GameService, adding code pools to existing trivia

### Pitfall 2: Tier Pool Not Truly Independent
**What goes wrong:** All tiers share a single code pool instead of independent pools
**Why it happens:** Coding codes as a single pool on PromotionConfig instead of per Tier
**How to avoid:** Each Tier has its own `max_codes` and `available_codes` count
**Warning signs:** "Admin sees all codes under one pool instead of per tier"

### Pitfall 3: Streak Timeout Not Atomic
**What goes wrong:** Timeout check in handler allows race condition where player answers right at 2-minute mark
**Why it happens:** Checking last_answered_at in handler without lock before processing answer
**How to avoid:** APScheduler job calls invalidate_streak() atomically, handler checks is_active flag
**Warning signs:** "Player's code not invalidated even after 2 minutes passed"

### Pitfall 4: Admin Wizard Too Long Without Save Point
**What goes wrong:** Admin makes mistake on step 12, must restart entire wizard
**Why it happens:** No intermediate save/resume capability
**How to avoid:** Store FSM state to DB on each step, allow resuming from last step
**Warning signs:** "I accidentally closed the wizard and lost all progress"

## Code Examples

### Existing Trivia Flow (game_service.py - simple trivia, NO tiers/codes)
```python
# Current trivia is "play for besitos" - streak tracked but no discount codes
def play_trivia(self, user_id, question_idx, answer_idx):
    is_correct = self.check_trivia_answer(question, answer_idx)
    if is_correct:
        new_streak = previous_streak + 1
        besitos = 1  # Fixed reward, no choice
    else:
        new_streak = 0  # Streak reset, no code invalidation
```

### New Trivia Discount Flow (from SPEC.md)
```python
# TriviaDiscountService handles the new flow
def process_answer(self, user_id, answer):
    is_correct = self.check_answer(question, answer)
    if is_correct:
        new_streak += 1
        if new_streak == tier.streak_threshold:  # Exact match
            code = self.generate_code(tier_id, user_id)  # Atomic
            return {'tier_reached': True, 'code': code}
    else:
        self.invalidate_streak(user_id)  # Code invalidated
```

### Tier Pool Independence (SPEC.md section 3.2)
```
Tier 1: Racha 5 → 10% descuento → 5 códigos (pool independently managed)
Tier 2: Racha 10 → 20% descuento → 6 códigos
Tier 3: Racha 15 → 30% descuento → 2 códigos
```

### Code Status Flow (SPEC.md section 3.3)
```
AVAILABLE → (generate_code) → CLAIMED → (use_code) → USED
           → (fail/wrong answer) → CANCELLED
           → (timeout) → EXPIRED
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Simple trivia (besitos only) | Trivia discount with tiered codes | This phase | New player experience, admin management |
| Questions in static JSON | QuestionSet with file_path reference | trivia-timeout worktree | Runtime question set switching |
| Hardcoded trivia limits | TriviaConfig singleton in DB | trivia-timeout worktree | Runtime configurable limits |
| Single promo type | Fixed vs Relative promotions | SPEC.md section 5.2 | Admin chooses date-based or duration-based |

**Deprecated/outdated:**
- None relevant to this phase

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | TriviaConfig singleton pattern from worktree is compatible with main branch | Standard Stack | May need import path adjustments |
| A2 | APScheduler job pattern from SchedulerService works for streak timeout | Architecture | Same pattern, should work |
| A3 | FSM storage (MemoryStorage vs RedisStorage) works for TriviaStreakStates | Player FSM | Existing pattern should work |

## Open Questions

1. **Should existing trivia (game_service.py) be extended or replaced?**
   - What we know: SPEC.md defines a separate "gambling-style trivia" distinct from existing simple trivia
   - What's unclear: Whether to keep game_service.py trivia separate or merge them under one menu
   - Recommendation: Keep separate entries in game menu — existing "Trivia" for besitos, new "Trivia Descuentos" for discounts

2. **Should questions be stored in DB or JSON files?**
   - What we know: QuestionSet model stores `file_path` reference, loads from JSON at runtime
   - What's unclear: Whether to migrate all questions to TriviaQuestion rows in DB
   - Recommendation: Use QuestionSet pattern (JSON files) initially, as done in trivia-timeout worktree

3. **How to handle VIP-exclusive trivia discount?**
   - What we know: SPEC.md excludes VIP trivia from this phase
   - What's unclear: Whether VIP players get separate limits or use same pool
   - Recommendation: TriviaConfig has separate limits for free, VIP, and VIP-exclusive; this phase implements free tier

## Environment Availability

Step 2.6: SKIPPED (no external dependencies - all project code/config)

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | pytest.ini |
| Quick run command | `pytest tests/unit/ -x` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REQ-16-01 | Player builds streak, gets tier discount at threshold | unit | `pytest tests/unit/test_trivia_discount_service.py::test_streak_tier_reached -x` | NO |
| REQ-16-02 | Each tier has independent code pool | unit | `pytest tests/unit/test_trivia_discount_service.py::test_tier_pool_independent -x` | NO |
| REQ-16-03 | Player can retire and claim code | unit | `pytest tests/unit/test_trivia_discount_service.py::test_player_retire -x` | NO |
| REQ-16-04 | Wrong answer invalidates code | unit | `pytest tests/unit/test_trivia_discount_service.py::test_wrong_answer_invalidates -x` | NO |
| REQ-16-05 | Admin wizard creates promotion with 3 tiers | integration | `pytest tests/integration/test_trivia_discount_admin.py -x` | NO |
| REQ-16-06 | Daily limits respected per user type | unit | `pytest tests/unit/test_trivia_config_service.py::test_daily_limits -x` | NO |
| REQ-16-07 | Atomic code generation prevents duplicates | unit | `pytest tests/unit/test_trivia_discount_service.py::test_code_generation_atomic -x` | NO |

### Wave 0 Gaps
- [ ] `tests/unit/test_trivia_discount_service.py` - covers REQ-16-01 through 04, 07
- [ ] `tests/unit/test_trivia_config_service.py` - covers REQ-16-06
- [ ] `tests/integration/test_trivia_discount_admin.py` - covers REQ-16-05
- [ ] Framework install: pytest - already in requirements.txt

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V4 Access Control | yes | is_admin() check in trivia_discount_admin_handlers.py |
| V5 Input Validation | yes | Validate tier thresholds, code counts, dates in service layer |
| V6 Cryptography | yes | Discount codes use secrets.token_hex / secrets.choice for uniqueness |

### Known Threat Patterns for Trivia Discount System

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| User tries to claim code twice (double-spend) | Spoofing | Code status check in claim_code(), atomic transaction |
| Admin creates invalid promotion (negative codes) | Tampering | Validation in create_trivia_promotion_config() |
| Concurrent code generation race | Repudiation | SELECT FOR UPDATE lock on tier row |
| Player spoofs answer (modify Telegram callback) | Spoofing | Validate question_idx + answer_idx match, server-side check |

## Sources

### Primary (HIGH confidence)
- `SPEC.md` - Full PRD for trivia discount system with model definitions, FSM states, 17-step wizard
- `services/game_service.py` - Existing trivia implementation (baseline for player flow)
- `.claude/worktrees/trivia-timeout/models/models.py` - TriviaPromotionConfig, QuestionSet, TriviaConfig models
- `.claude/worktrees/trivia-timeout/services/trivia_discount_service.py` - Service implementation patterns
- `.claude/worktrees/trivia-timeout/handlers/trivia_discount_admin_handlers.py` - Admin FSM wizard pattern
- `handlers/promotion_admin_handlers.py` - PromotionWizardStates (reference for admin wizard)
- `models/models.py` - Existing models, GameRecord already exists

### Secondary (MEDIUM confidence)
- `services/store_service.py` - Atomic code generation pattern (SELECT FOR UPDATE)
- `services/scheduler_service.py` - APScheduler job pattern for timeout
- `.planning/phases/16-expansi-n-de-trivias/16-CONTEXT.md` - Phase context and locked decisions

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - using existing aiogram/SQLAlchemy, adopting proven worktree patterns
- Architecture: HIGH - follows existing patterns (wizard FSM, service-with-service, singleton config)
- Pitfalls: HIGH - clear what to avoid (merging with simple trivia, race conditions)

**Research date:** 2026-05-08
**Valid until:** 30 days (stable tech stack, active development on trivia system)