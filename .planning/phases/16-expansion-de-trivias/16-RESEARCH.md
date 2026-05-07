# Phase 16: Expansión de Trivias - Research

**Researched:** 2026-05-07
**Domain:** Trivia game expansion with protection system
**Confidence:** HIGH

## Summary

Phase 16 expands the existing trivia system into two distinct modes: **Trivia Libre** (free play, earns besitos) and **Trivia Promo** (competes for discount codes with purchasable protection). The existing GameService (`game_service.py`) already has the foundation: `play_trivia()`, `play_trivia_vip()`, `can_play()`, streak tracking, and tier-based discount code generation. The expansion requires:

1. **New game_type values**: `trivia_free`, `trivia_free_vip`, `trivia_promo`, `trivia_promo_vip` (current is just `trivia`/`trivia_vip`)
2. **Separate daily limit counters**: independent counters for free vs promo modes
3. **Protection system**: offered on wrong answers in promo mode, costs besitos, maintains streak when accepted
4. **VR bonus**: every 3-6 questions in free mode grants +10 besitos instead of base reward
5. **FSM state additions**: `promo_wrong_answer` (offer protection), `free_bonus` (bonus question active)
6. **Model changes**: `TriviaPromotionConfig.protection_tiers` JSON column
7. **TransactionSource additions**: `TRIVIA_PROMO`, `TRIVIA_PROTECTION`

The existing TriviaDiscountService already handles tier parsing and code generation - protection is a new feature layered on top.

**Primary recommendation:** Extend `GameService` with new methods `play_trivia_free()`, `play_trivia_promo()` and variants, reuse existing streak/tier logic for promo mode, implement VR bonus via random check in free mode.

---

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Game types: `trivia_free`, `trivia_free_vip`, `trivia_promo`, `trivia_promo_vip`
- Protection cost formula fallback: `5 + (streak // 3) * 5`
- Protection debits besitos and maintains streak when accepted
- FSM states: `waiting_streak_choice`, `streak_continue` (existing), `promo_wrong_answer` (new), `free_bonus` (new)
- VR bonus every 3-6 questions in free mode (+10 besitos)
- Separate daily limits: `daily_trivia_limit_promo_free`=20, `daily_trivia_limit_promo_vip`=30
- No besitos awarded in promo mode (source: `TransactionSource.TRIVIA_PROMO` for traceability)

### Claude's Discretion
- UI design of trivia menu (keyboards)
- Error handling and edge cases
- Integration tests for complete flows

### Deferred Ideas (OUT OF SCOPE)
Ninguna — PRD covers complete scope of Phase 16.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Trivia question flow | API/Backend | — | GameService handles all game logic |
| Besitos transactions | API/Backend | — | BesitoService owns balance operations |
| FSM state management | API/Backend | — | Handlers set/get state, service validates |
| Daily limit tracking | Database | — | GameRecord query by game_type and date |
| Protection offer UI | Frontend (Telegram) | — | Handlers build keyboard, send message |
| Discount code generation | API/Backend | — | TriviaDiscountService owns tier logic |
| Admin config (protection tiers) | API/Backend | — | TriviaDiscountAdminHandlers wizard |

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| aiogram | 3.4.1 | Telegram bot framework | Project standard |
| SQLAlchemy | 2.0 | ORM for database operations | Project standard |
| APScheduler | async compatible | Scheduler for time-based triggers | Project standard |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `services/besito_service.py` | — | Balance checks, credit/debit | Protection purchase flow |
| `services/trivia_discount_service.py` | — | Tier parsing, code generation | Promo mode discount logic |
| `services/trivia_config_service.py` | — | TriviaConfig singleton | Daily limit config |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| JSON column for protection_tiers | Separate `protection_tiers` table | Simpler queries vs normalized storage — JSON is fine for tier configs |

---

## Architecture Patterns

### System Architecture Diagram

```
User presses "game_trivia" or "game_trivia_promo"
         │
         ▼
┌─────────────────────────────────────────────────┐
│  GameService.get_menu_data()                     │
│  - Checks active promo via TriviaDiscountService │
│  - Shows free always, promo only if active      │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│  game_trivia callback (FREE mode)                │
│  game_trivia_promo callback (PROMO mode)         │
└─────────────────────────────────────────────────┘
         │
    ┌────┴────┐
    ▼         ▼
FREE MODE   PROMO MODE
    │         │
    ▼         ▼
┌───────────────────┐   ┌────────────────────────────┐
│ play_trivia_free()│   │ play_trivia_promo()         │
│ - check daily    │   │ - check daily limit (NEW)   │
│ - load question  │   │ - load question             │
│ - is_bonus = _   │   │ - user answers              │
│   _is_bonus_q()  │   │   ├─ CORRECT → streak++     │
│ - credit +1/5    │   │   │  → tier check → code gen │
│   or +10 if bonus│   │   └─ WRONG → offer_protection│
└───────────────────┘   └────────────────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────────────────────────────────────┐
│  Protection Flow (promo mode only)               │
│  1. protection_offer()                          │
│  2. get_protection_cost(config, streak)         │
│  3. check balance via BesitoService             │
│  4. if accept: debit_besitos() + maintain streak│
│  5. if decline: streak=0                        │
└─────────────────────────────────────────────────┘
```

### Recommended Project Structure
```
services/
├── game_service.py          # Extended with free/promo methods
├── trivia_discount_service.py # Extended with protection_tiers
├── besito_service.py         # No changes needed (existing debit_besitos)

handlers/
├── game_user_handlers.py     # Extended with promo_wrong_answer state
├── trivia_discount_admin_handlers.py # Extended with protection tiers wizard

models/
├── models.py                # TriviaPromotionConfig: add protection_tiers

migrations/
├── alembic/versions/         # New migration for protection_tiers column
```

### Pattern 1: Dual-Mode Game Type Routing
**What:** Route to different play methods based on whether a promo is active
**When to use:** User presses trivia button — check `_get_active_trivia_promotion()` to determine mode
**Example:**
```python
def get_trivia_mode(self, user_id: int) -> str:
    """Returns 'free' or 'promo' based on active promotion"""
    config = self._get_active_trivia_promotion()
    return 'promo' if config and config.is_active else 'free'
```

### Pattern 2: Protection Cost Calculation
**What:** Calculate protection cost from tiers JSON or fallback formula
**When to use:** When user fails in promo mode, before offering protection
**Example:**
```python
def get_protection_cost(self, config: TriviaPromotionConfig, streak: int) -> int:
    """Calculate protection cost: tier-based or fallback formula"""
    if config.protection_tiers:
        tiers = json.loads(config.protection_tiers)
        for tier in reversed(tiers):
            if streak >= tier['streak']:
                return tier['cost']
    # Fallback: 5 + (streak // 3) * 5
    return 5 + (streak // 3) * 5
```
**Source:** Phase 16 PRD specification

### Pattern 3: VR Bonus (Free Mode)
**What:** Every 3-6 questions, grant +10 besitos instead of base reward
**When to use:** After correct answer in free mode trivia
**Example:**
```python
def _is_bonus_question(self, question_count: int) -> bool:
    """VR bonus every 3-6 questions"""
    return question_count % random.randint(3, 6) == 0
```

### Anti-Patterns to Avoid
- **Hand-rolling protection cost**: Use `get_protection_cost()` with tier fallback, don't hardcode
- **Single game_type for all trivia**: Separate counters needed — use `trivia_free`/`trivia_promo` variants
- **Blocking on insufficient balance**: Show decline keyboard (no protection option) when balance < cost

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|------------|-------------|-----|
| Protection cost formula | Custom pricing logic | `get_protection_cost()` with tier lookup + fallback | Consistency, admin-configurable tiers |
| Besitos debit | Direct SQL UPDATE | `BesitoService.debit_besitos()` | Race condition protection via SELECT FOR UPDATE |
| Daily limit tracking | Custom counter tables | `GameRecord` with separate `game_type` per mode | Already normalized, query by date+type |
| Streak timeout | Custom expiration | `STREAK_TIMEOUT_SECONDS` check in handlers | Already implemented in Phase 14 |

**Key insight:** The existing `BesitoService.debit_besitos()` already uses `SELECT FOR UPDATE` for race condition protection. Protection purchase just needs to call this method with appropriate `TransactionSource`.

---

## Runtime State Inventory

> N/A for this phase — no rename/refactor/migration. This is a feature expansion.

---

## Common Pitfalls

### Pitfall 1: Single Counter for All Trivia Modes
**What goes wrong:** Users could play 20 promo + 20 free trivias (should be independent limits)
**Why it happens:** `get_today_play_count()` queries by single `game_type` value
**How to avoid:** Use separate `game_type` values: `trivia_promo`, `trivia_free`, etc.
**Warning signs:** `get_today_play_count(user_id, 'trivia')` — too generic

### Pitfall 2: Protection Offered When Balance Insufficient
**What goes wrong:** User accepts protection, transaction fails, streak is lost anyway
**Why it happens:** Not checking balance before offering protection keyboard
**How to avoid:** `protection_offer()` must check `besito_service.has_sufficient_balance(user_id, cost)` first
**Warning signs:** Missing balance check in protection offer flow

### Pitfall 3: Protection Debit Without Streak Maintenance
**What goes wrong:** Protection accepted but streak still reset to 0
**Why it happens:** Forgetting to skip the streak reset when protection is accepted
**How to avoid:** In `play_trivia_promo()`, when protection accepted: do NOT set `new_streak = 0`
**Warning signs:** Streak lost after protection purchase

### Pitfall 4: VR Bonus Triggering Every Question
**What goes wrong:** Bonus triggers on every question instead of every 3-6
**Why it happens:** Off-by-one in modulo check: `count % rand == 0` rarely triggers
**How to avoid:** Use cumulative counter, not streak, for bonus triggering:
```python
# CORRECT: increment and check
self._bonus_counter += 1
if self._bonus_counter >= random.randint(3, 6):
    self._bonus_counter = 0  # reset
    return True  # bonus triggered
# INCORRECT: modulo on streak
if streak % random.randint(3, 6) == 0:  # wrong!
```

### Pitfall 5: Promo Mode Awarding Besitos
**What goes wrong:** Users earn besitos in promo mode, breaking economic loop
**Why it happens:** `play_trivia_promo()` calls `credit_besitos()` on correct answer
**How to avoid:** Promo mode should NOT call `credit_besitos()` — only update streak/tier
**Warning signs:** `source=TransactionSource.TRIVIA` in promo mode flow

---

## Code Examples

### Example 1: Protection Offer Flow (game_service.py addition)
```python
def protection_offer(self, user_id: int, streak: int, config: TriviaPromotionConfig) -> dict:
    """Build protection offer keyboard data"""
    cost = self.get_protection_cost(config, streak)
    balance = self.besito_service.get_balance(user_id)
    can_afford = balance >= cost

    return {
        'cost': cost,
        'balance': balance,
        'can_afford': can_afford,
        'keyboard': protection_keyboard(cost) if can_afford else decline_only_keyboard()
    }

def accept_protection(self, user_id: int, cost: int) -> bool:
    """Debit besitos and return True if successful"""
    return self.besito_service.debit_besitos(
        user_id=user_id,
        amount=cost,
        source=TransactionSource.TRIVIA_PROTECTION,
        description=f"Protection purchase at streak"
    )
```

### Example 2: Extended Daily Limit Check
```python
def can_play(self, user_id: int, game_type: str) -> Tuple[bool, int, int, str]:
    """
    Verifies daily limits for all trivia modes.
    game_type: 'dice', 'trivia_free', 'trivia_free_vip', 'trivia_promo', 'trivia_promo_vip'
    """
    limits = self.get_daily_limits(user_id)
    is_vip = self.is_user_vip(user_id)

    if game_type == 'dice':
        limit = limits['dice_limit']
    elif game_type == 'trivia_free':
        limit = limits['trivia_limit']  # from TriviaConfig
    elif game_type == 'trivia_free_vip':
        limit = limits['trivia_limit'] * 2  # VIP gets double free
    elif game_type == 'trivia_promo':
        limit = self._trivia_config_service.get_config().daily_trivia_limit_promo_free
    elif game_type == 'trivia_promo_vip':
        limit = self._trivia_config_service.get_config().daily_trivia_limit_promo_vip
    else:
        limit = 7  # fallback

    played = self.get_today_play_count(user_id, game_type)
    # ... rest of logic unchanged
```

### Example 3: FSM State Addition (game_user_handlers.py)
```python
class TriviaStreakStates(StatesGroup):
    waiting_streak_choice = State()     # existing
    streak_continue = State()           # existing
    promo_wrong_answer = State()        # NEW: falló en promo, ofrece protección
    free_bonus = State()                # NEW: pregunta bonus activa
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single `trivia` game_type | Multiple game_types: `trivia_free`, `trivia_promo`, etc. | Phase 16 | Independent daily limits per mode |
| No protection system | Protection offered on wrong answer in promo | Phase 16 | Users can protect streaks for besitos |
| Fixed besitos per correct answer | VR bonus +10 every 3-6 questions | Phase 16 | Increased engagement in free mode |

**Deprecated/outdated:**
- `game_type='trivia'` — replaced by `trivia_free`/`trivia_promo`
- `game_type='trivia_vip'` — replaced by `trivia_free_vip`/`trivia_promo_vip`

---

## Assumptions Log

> All claims verified via code inspection — no user confirmation needed.

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `TriviaPromotionConfig` table exists and has `discount_tiers` JSON column | Model Changes | Low — confirmed in models.py line 1172 |
| A2 | `BesitoService.debit_besitos()` uses SELECT FOR UPDATE | Protection Flow | Low — confirmed in besito_service.py line 156 |
| A3 | `TransactionSource` enum is extendable via migration | TransactionSource | Low — pattern confirmed via existing migrations |

---

## Open Questions

1. **VR Bonus cumulative counter storage**
   - What we know: `_is_bonus_question()` uses a counter, triggers every 3-6 questions
   - What's unclear: Where is the bonus counter stored? (FSM state? GameRecord? Memory?)
   - Recommendation: Store in FSM state data, reset after each bonus trigger

2. **Protection tiers admin UI**
   - What we know: Admin wizard in `TriviaDiscountStates` handles `waiting_discount_tiers`
   - What's unclear: Do we need a separate step for protection_tiers or combine with discount_tiers?
   - Recommendation: Combine into same wizard step — both are JSON tier arrays

3. **Free bonus question display**
   - What we know: VR bonus replaces base reward with +10 besitos
   - What's unclear: Does the bonus question look different? Same keyboard?
   - Recommendation: Use same keyboard but show special "BONUS!" header text

---

## Environment Availability

> Skip this section — no external dependencies beyond project code.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio |
| Config file | `tests/pytest.ini` |
| Quick run command | `pytest tests/unit/test_game_service.py -x -v` |
| Full suite command | `pytest tests/ -x -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| REQ-16-01 | Menu shows free trivia always, promo only with active promo | unit | `pytest tests/unit/test_game_service.py::test_trivia_menu_modes -x` | Wave 0 |
| REQ-16-02 | Independent daily limits between free and promo modes | unit | `pytest tests/unit/test_game_service.py::test_daily_limits_independent -x` | Wave 0 |
| REQ-16-03 | Protection offered on wrong answer in promo mode | unit | `pytest tests/unit/test_game_service.py::test_protection_offer -x` | Wave 0 |
| REQ-16-04 | Protection cost calculated from tiers or fallback formula | unit | `pytest tests/unit/test_game_service.py::test_protection_cost_calculation -x` | Wave 0 |
| REQ-16-05 | Protection debits besitos and maintains streak | unit | `pytest tests/unit/test_game_service.py::test_protection_accept -x` | Wave 0 |
| REQ-16-06 | VR bonus every 3-6 questions in free mode | unit | `pytest tests/unit/test_game_service.py::test_vr_bonus_frequency -x` | Wave 0 |
| REQ-16-07 | Admin can configure protection_tiers in promo wizard | integration | `pytest tests/integration/test_trivia_admin.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/unit/test_game_service.py -x -q`
- **Per wave merge:** `pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_game_service.py` — covers REQ-16-01 through REQ-16-06
- [ ] `tests/integration/test_trivia_admin.py` — covers REQ-16-07
- [ ] `tests/conftest.py` — shared fixtures (likely exists from Phase 14)
- [ ] Framework install: already present

*(If no gaps: "None — existing test infrastructure covers all phase requirements")*

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | yes | question_idx, answer_idx integer validation in play_trivia() |
| V4 Access Control | partial | VIP-only trivia checks via is_user_vip() |

### Known Threat Patterns for Trivia System

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| User manipulates question index to guess answers | Tampering | Question indices are ephemeral, answer checked server-side |
| User replays correct answer to farm besitos | Tampering | Daily limits per game_type — GameRecord INSERT per play |
| Race condition on protection purchase | Denial | SELECT FOR UPDATE via BesitoService.debit_besitos() |
| User exploits VR bonus calculation | Tampering | Bonus counter in FSM state, not user-controlled |

---

## Sources

### Primary (HIGH confidence)
- `services/game_service.py` — lines 1-1521, current trivia implementation
- `services/besito_service.py` — lines 1-226, debit_besitos() with SELECT FOR UPDATE
- `models/models.py` — lines 1143-1216, TriviaPromotionConfig model
- `.planning/phases/16-expansion-de-trivias/16-CONTEXT.md` — Phase 16 PRD decisions

### Secondary (MEDIUM confidence)
- `handlers/game_user_handlers.py` — FSM states, trivia flow handlers
- `services/trivia_discount_service.py` — tier parsing, code generation patterns

### Tertiary (LOW confidence)
- None — all critical patterns verified via code inspection

---

## Metadata

**Confidence breakdown:**
- Standard Stack: HIGH — aiogram/SQLAlchemy versions verified via requirements
- Architecture: HIGH — existing patterns confirmed in code
- Pitfalls: HIGH — all pitfalls derived from existing code analysis

**Research date:** 2026-05-07
**Valid until:** 2026-06-07 (30 days — trivia system is stable)
