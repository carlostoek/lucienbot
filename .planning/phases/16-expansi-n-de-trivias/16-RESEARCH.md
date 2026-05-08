# Phase 16: Expansión de Trivias - Research

**Researched:** 2026-05-08
**Domain:** Trivia Discount System (gambling-style trivia with progressive discount tiers)
**Confidence:** HIGH (verified against SPEC.md, existing codebase patterns, and service architecture)

## CRITICAL DISTINCTION: Two Completely Separate Promotion Systems

This research makes explicit the **complete separation** between two distinct systems:

| Aspect | Commercial PromotionService | NEW TriviaDiscountService |
|--------|---------------------------|---------------------------|
| **Purpose** | Sell products for MXN peso | Reward players with discount codes |
| **Model** | `Promotion` (commercial) | `TriviaPromotionConfig` (NEW) |
| **User action** | "Me Interesa" button | Streak-building trivia gameplay |
| **Admin creates** | Package + price in MXN | Tiers with streak_threshold + discount_percentage + max_codes |
| **Delivery** | Manual (admin sends files) | Automatic code generation |
| **Location** | `services/promotion_service.py` | `services/trivia_discount_service.py` (NEW) |

**This is NOT an extension of the existing Promotion system.** They share no code, no models, and no flows.

---

## User Constraints (from Input Clarification)

### Locked Decisions
- TriviaDiscountService, GameService (expanded), TriviaAdminService architecture
- TriviaPromotionConfig as NEW model (NOT reusing Promotion)
- Streak-based tier system with independent code pools per tier
- 2-minute streak timeout with APScheduler
- Admin wizard with direct `discount_percentage` input (no price in MXN)
- FSM player flow: idle → waiting_answer → (streak_choice | game_over) → waiting_retire → idle

### Claude's Discretion
- File structure (follow existing patterns)
- FSM storage (MemoryStorage or RedisStorage)
- Specific implementation patterns for models, services, handlers

### Deferred Ideas
- Trivia VIP (separate spec later)
- Besitos/rewards system (already exists)
- Narrative/stories (already exists)
- Commercial promotions (already exists, completely separate)

---

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REQ-16-01 | Gambling-style trivia with streak thresholds | game_service.py trivia pattern + SPEC.md section 2.1 |
| REQ-16-02 | TriviaPromotionConfig (NEW model, NOT Promotion) | SPEC.md section 3.1 |
| REQ-16-03 | Discount tiers with independent code pools (Tier model) | SPEC.md section 3.2 |
| REQ-16-04 | Player choice: retire with code or continue gambling | SPEC.md section 2.1 flow diagram |
| REQ-16-05 | 2-minute streak timeout invalidates code | SPEC.md section 4.5, APScheduler pattern |
| REQ-16-06 | Admin 17-step promotion creation wizard | PromotionWizardStates pattern in promotion_admin_handlers.py |
| REQ-16-07 | Daily limits by user type (free/VIP/exclusive) | TriviaConfig singleton pattern, SPEC.md section 3.8 |
| REQ-16-08 | Atomic code generation with SELECT FOR UPDATE | StoreService pattern |

---

## Summary

Phase 16 implements a **gambling-style trivia** where players build streaks of correct answers to unlock progressively higher discount tiers. **Each tier has its own independent pool of codes** — when a tier is exhausted, it's no longer offered. Players can retire and claim their discount or continue gambling for higher tiers. Wrong answer = streak reset + code invalidated. 2-minute timeout = code expired.

**Key distinction from existing trivia:** The current `game_service.py` trivia is simple "play for besitos" with streak counting but no discount codes, no tiers, no player choice, and no timeout. Phase 16 is a **separate system** with its own models, services, FSM states, and player flows.

**Key distinction from commercial PromotionService:** The commercial `PromotionService` manages "Me Interesa" for purchasing content for MXN pesos. TriviaDiscountService manages a completely different system for awarding discount codes based on trivia performance. They are architecturally independent with separate models, services, and handlers.

**Primary recommendation:** Create a new `TriviaPromotionConfig` model (NOT extending `Promotion`), implement `TriviaDiscountService` as a standalone service, and follow SPEC.md section 5.2 for the 17-step admin wizard.

---

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

---

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
| Atomic code generation | `store_service.py` create_product (SELECT FOR UPDATE) | Code pool concurrency |
| Singleton config | `services/` pattern (e.g., config services) | TriviaConfig for daily limits |
| QuestionSet loading | `game_service.py` load_trivia_questions() | Load questions from JSON |

**Installation:**
```bash
# No new packages needed - all existing
```

---

## Architecture Patterns

### Recommended Project Structure
```
services/
├── trivia_discount_service.py      # NEW - promotion config, tiers, codes (NOT promotion_service.py)
├── question_set_service.py         # NEW - themed question groups
├── trivia_config_service.py        # NEW - singleton config for limits
├── game_service.py                 # EXPAND - existing trivia (keep separate)

models/
├── models.py                       # MODIFY - add TriviaPromotionConfig, Tier, DiscountCode, UserStreak, QuestionSet, Question, TriviaConfig

handlers/
├── trivia_discount_admin_handlers.py  # NEW - admin wizard
├── trivia_discount_user_handlers.py   # NEW - player FSM
├── game_user_handlers.py               # KEEP AS IS - existing "play for besitos" trivia

keyboards/
├── inline_keyboards.py              # MODIFY - add trivia discount keyboards
```

### Pattern 1: TriviaPromotionConfig Model (NEW, NOT Promotion)
```python
# models/models.py - NEW model, completely separate from Promotion
class TriviaPromotionConfig(Base):
    """Configuración de promoción de trivia con descuentos (NO es Promotion)"""
    __tablename__ = "trivia_promotion_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    duration_days = Column(Integer, nullable=True)  # For relative promotions
    auto_reset = Column(Boolean, default=False)
    question_set_id = Column(Integer, ForeignKey("question_sets.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tiers = relationship("Tier", back_populates="promotion_config", cascade="all, delete-orphan")
    question_set = relationship("QuestionSet")

class Tier(Base):
    """Nivel de descuento con pool independiente de códigos"""
    __tablename__ = "tiers"

    id = Column(Integer, primary_key=True, index=True)
    promotion_config_id = Column(Integer, ForeignKey("trivia_promotion_configs.id"), nullable=False)
    tier_number = Column(Integer, nullable=False)
    streak_threshold = Column(Integer, nullable=False)
    discount_percentage = Column(Integer, nullable=False)  # e.g., 10 = 10%
    max_codes = Column(Integer, nullable=False)
    codes_generated = Column(Integer, default=0)

    # Relationships
    promotion_config = relationship("TriviaPromotionConfig", back_populates="tiers")
    discount_codes = relationship("DiscountCode", back_populates="tier")

class DiscountCodeStatus(str, enum.Enum):
    """Estados de un código de descuento"""
    AVAILABLE = "available"
    CLAIMED = "claimed"
    USED = "used"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class DiscountCode(Base):
    """Código de descuento (INDEPENDIENTE del modelo Promotion)"""
    __tablename__ = "discount_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False)
    tier_id = Column(Integer, ForeignKey("tiers.id"), nullable=False)
    user_id = Column(BigInteger, nullable=True)  # Null = available
    status = Column(Enum(DiscountCodeStatus), default=DiscountCodeStatus.AVAILABLE)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    claimed_at = Column(DateTime(timezone=True), nullable=True)
    used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    tier = relationship("Tier", back_populates="discount_codes")
```

**Key point:** `DiscountCode` is NOT related to `Promotion`. It has its own status enum and belongs to a `Tier`.

### Pattern 2: UserStreak and GameRecord (for trivia)
```python
class UserStreak(Base):
    """Racha activa del usuario en trivia de descuentos"""
    __tablename__ = "user_streaks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    promotion_config_id = Column(Integer, ForeignKey("trivia_promotion_configs.id"), nullable=True)
    current_streak = Column(Integer, default=0)
    active_tier_id = Column(Integer, ForeignKey("tiers.id"), nullable=True)
    active_code_id = Column(Integer, ForeignKey("discount_codes.id"), nullable=True)
    streak_started_at = Column(DateTime(timezone=True), nullable=True)
    last_answered_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=False)

class GameResult(str, enum.Enum):
    """Resultado de partida de trivia"""
    WON = "won"
    LOST = "lost"
    ABANDONED = "abandoned"
    EXPIRED = "expired"

class GameRecord(Base):
    """Registro de partida (EXPAND existing model)"""
    __tablename__ = "game_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    promotion_config_id = Column(Integer, ForeignKey("trivia_promotion_configs.id"), nullable=True)
    discount_code_id = Column(Integer, ForeignKey("discount_codes.id"), nullable=True)
    game_type = Column(String(20), nullable=False)  # 'trivia_discount' | 'trivia_vip'
    questions_answered = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    final_streak = Column(Integer, default=0)
    result = Column(String(20), nullable=False)  # WON/LOST/ABANDONED/EXPIRED
    played_at = Column(DateTime(timezone=True), server_default=func.now())
```

### Pattern 3: QuestionSet and Question (NEW models)
```python
class Difficulty(str, enum.Enum):
    """Dificultad de pregunta"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class QuestionSet(Base):
    """Set de preguntas temáticas (NO es pregunta individual)"""
    __tablename__ = "question_sets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=False)  # Path to JSON file
    is_override = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    questions = relationship("Question", back_populates="question_set", cascade="all, delete-orphan")

class Question(Base):
    """Pregunta individual de trivia"""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    question_set_id = Column(Integer, ForeignKey("question_sets.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    option_a = Column(String(500), nullable=False)
    option_b = Column(String(500), nullable=False)
    option_c = Column(String(500), nullable=False)
    option_d = Column(String(500), nullable=False)
    correct_option = Column(String(1), nullable=False)  # 'A', 'B', 'C', 'D'
    difficulty = Column(Enum(Difficulty), default=Difficulty.MEDIUM)
    category = Column(String(100), nullable=True)

    # Relationships
    question_set = relationship("QuestionSet", back_populates="questions")
```

### Pattern 4: TriviaConfig (singleton for limits)
```python
class TriviaConfig(Base):
    """Configuración global de trivia (singleton - solo una fila)"""
    __tablename__ = "trivia_configs"

    id = Column(Integer, primary_key=True, index=True)
    free_daily_limit = Column(Integer, default=7)
    vip_daily_limit = Column(Integer, default=15)
    vip_exclusive_daily_limit = Column(Integer, default=5)
    streak_timeout_minutes = Column(Integer, default=2)
```

---

## Service Architecture

### TriviaDiscountService (NEW - separate from PromotionService)
```python
class TriviaDiscountService:
    """Servicio para gestionar promociones de trivia con descuentos"""

    # ==================== PROMOTION CONFIG ====================
    def create_promotion_config(self, data: dict) -> Optional[TriviaPromotionConfig]
    def get_promotion_config(self, config_id: int) -> Optional[TriviaPromotionConfig]
    def get_active_promotions(self) -> List[TriviaPromotionConfig]
    def update_promotion_config(self, config_id: int, data: dict) -> bool
    def delete_promotion_config(self, config_id: int) -> bool
    def pause_promotion(self, config_id: int) -> bool
    def resume_promotion(self, config_id: int) -> bool

    # ==================== TIERS ====================
    def get_tier(self, tier_id: int) -> Optional[Tier]
    def get_tiers_by_promotion(self, promotion_id: int) -> List[Tier]
    def get_available_codes_count(self, tier_id: int) -> int  # max_codes - codes_generated
    def add_codes_to_tier(self, tier_id: int, count: int) -> bool

    # ==================== CODE GENERATION (ATOMIC) ====================
    def generate_code(self, tier_id: int, user_id: int) -> Optional[DiscountCode]
    """Generate code atomically with SELECT FOR UPDATE"""
    def claim_code(self, code_id: int) -> bool
    def use_code(self, code_id: int) -> bool
    def cancel_code(self, code_id: int) -> bool
    def expire_code(self, code_id: int) -> bool
    def get_user_active_code(self, user_id: int) -> Optional[DiscountCode]
    def get_codes_by_tier(self, tier_id: int, filters: dict) -> List[DiscountCode]

    # ==================== STREAK ====================
    def get_user_streak(self, user_id: int) -> Optional[UserStreak]
    def create_streak(self, user_id: int, promotion_id: int) -> UserStreak
    def increment_streak(self, user_id: int) -> Tuple[UserStreak, Optional[Tier]]
    def invalidate_streak(self, user_id: int) -> None  # Called by APScheduler timeout
    def reset_streak(self, user_id: int) -> None
```

**Key distinction from PromotionService:**
- `PromotionService.create_promotion()` takes `price_mxn` parameter
- `TriviaDiscountService.create_promotion_config()` takes `discount_percentage` per tier
- They share no code paths

### GameService (expand existing, keep separate)
```python
class GameService:
    """EXPAND existing - add trivia discount support"""

    # ==================== TRIVIA DISCOUNT ENTRY ====================
    def get_trivia_discount_entry_data(self, user_id: int) -> dict
    def can_play_trivia_discount(self, user_id: int) -> Tuple[bool, int, int, str]
    def get_active_trivia_promotion(self) -> Optional[TriviaPromotionConfig]

    # ==================== TRIVIA DISCOUNT GAMEPLAY ====================
    def load_questions_for_promotion(self, promotion_id: int) -> List[Question]
    def get_random_trivia_question(self) -> Tuple[Optional[Question], int]
    def check_trivia_discount_answer(self, question: Question, answer: str) -> bool
    def process_trivia_answer(self, user_id: int, question_id: int, answer: str) -> dict
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Discount code generation | Random without lock | SELECT FOR UPDATE | Concurrency safety, no duplicate codes |
| Streak persistence | In-memory tracking | UserStreak model in DB | Survives bot restart, tracks across sessions |
| Streak timeout | Polling/sleep | APScheduler job | Non-blocking, survives restart, precision |
| Admin wizard | Callback spaghetti | FSM StatesGroup | Clean state management, back navigation |
| Config management | Hardcoded constants | TriviaConfig singleton | Runtime changes, no deploy needed |
| Discount codes | Reuse Promotion model | New TriviaPromotionConfig + DiscountCode | Complete independence from commercial system |

---

## Common Pitfalls

### Pitfall 1: Confusion Between Promotion and TriviaPromotionConfig
**What goes wrong:** Developers try to merge or reuse `Promotion` for trivia discounts
**Why it happens:** Both have "promotion" in the name
**How to avoid:** Clear separation — `Promotion` is for commercial "Me Interesa", `TriviaPromotionConfig` is for trivia discount codes
**Warning signs:** Trying to pass `price_mxn` to trivia discount creation, reusing `PromotionInterest`

### Pitfall 2: Tier Pool Not Truly Independent
**What goes wrong:** All tiers share a single code pool instead of independent pools
**Why it happens:** Coding codes as a single pool on promotion instead of per Tier
**How to avoid:** Each Tier has its own `max_codes` and `codes_generated` count. Code generation is per-tier with atomic lock.
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

### Pitfall 5: Using Commercial PromotionService for Trivia
**What goes wrong:** Calling PromotionService methods for trivia discount flow
**Why it happens:** Both deal with "promotions"
**How to avoid:** Use TriviaDiscountService exclusively for trivia. PromotionService is only for commercial "Me Interesa" system.
**Warning signs:** "price_mxn" parameter appearing in trivia flow, "InterestStatus" used for trivia codes

---

## Code Examples

### Code Status Flow (SPEC.md section 3.3)
```
AVAILABLE → (generate_code) → CLAIMED → (use_code) → USED
           → (fail/wrong answer) → CANCELLED
           → (timeout) → EXPIRED
```

### Atomic Code Generation Pattern
```python
def generate_code(self, tier_id: int, user_id: int) -> Optional[DiscountCode]:
    """Generate code atomically with SELECT FOR UPDATE"""
    db = self._get_db()
    try:
        # Lock the tier row to prevent concurrent generation
        tier = db.query(Tier).filter(Tier.id == tier_id).with_for_update().first()
        if not tier:
            return None

        available = tier.max_codes - tier.codes_generated
        if available <= 0:
            return None  # No codes available

        # Generate unique code
        code = f"TRI-{secrets.token_hex(3).upper()}"

        # Create discount code
        discount_code = DiscountCode(
            code=code,
            tier_id=tier_id,
            user_id=user_id,
            status=DiscountCodeStatus.AVAILABLE,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30)
        )
        db.add(discount_code)

        # Update tier count
        tier.codes_generated += 1

        db.commit()
        db.refresh(discount_code)
        return discount_code

    except Exception as e:
        db.rollback()
        logger.error(f"Error generating code for tier {tier_id}: {e}")
        return None
```

### Tier Pool Independence (SPEC.md section 3.2)
```
Tier 1: Racha 5 → 10% descuento → 5 códigos (pool independently managed)
Tier 2: Racha 10 → 20% descuento → 6 códigos
Tier 3: Racha 15 → 30% descuento → 2 códigos
```

### Admin Wizard States (17-step from SPEC.md section 5.2)
```python
class TriviaDiscountStates(StatesGroup):
    waiting_promotion_type = State()      # Fixed / Relative
    waiting_dates_or_duration = State()   # Step 2a or 2b
    waiting_name = State()                 # Step 3
    waiting_description = State()          # Step 3
    waiting_tiers = State()               # Step 4 - multiple tiers
    waiting_question_set = State()        # Step 5
    waiting_confirmation = State()        # Step 6
```

### Player FSM States
```python
class TriviaStreakStates(StatesGroup):
    waiting_answer = State()
    streak_choice = State()    # Reached threshold, player chooses
    waiting_retire = State()   # Player chose to retire, processing code claim
    # Flow: idle → waiting_answer → (streak_choice | game_over)
    #                              ↓
    #                      waiting_retire → idle
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single code pool | Independent pools per tier | This phase | Admin sees per-tier availability |
| Hardcoded trivia limits | TriviaConfig singleton in DB | This phase | Runtime configurable limits |
| Simple trivia (besitos only) | Trivia discount with tiered codes | This phase | New player experience, admin management |
| No player choice | Player can retire or continue | This phase | Gambling-style risk/reward |
| No streak timeout | 2-minute timeout with APScheduler | This phase | Prevents abandoned streaks |

**Deprecated/outdated:**
- None relevant to this phase

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | TriviaPromotionConfig is a new model (not extending Promotion) | Models | Code will need refactoring if this assumption is wrong |
| A2 | APScheduler job pattern from SchedulerService works for streak timeout | Architecture | Same pattern, should work |
| A3 | FSM storage (MemoryStorage vs RedisStorage) works for TriviaStreakStates | Player FSM | Existing pattern should work |
| A4 | QuestionSet uses JSON file loading pattern from existing trivia | Question Loading | Same pattern as game_service.py |

---

## Open Questions

1. **Should existing trivia (game_service.py) be extended or replaced?**
   - What we know: SPEC.md defines a separate "gambling-style trivia" distinct from existing simple trivia
   - What's unclear: Whether to keep game_service.py trivia separate or merge them under one menu
   - Recommendation: Keep separate entries in game menu — existing "Trivia" for besitos, new "Trivia Descuentos" for discounts

2. **Should questions be stored in DB or JSON files?**
   - What we know: SPEC.md section 3.6 shows QuestionSet model with `file_path` reference
   - What's unclear: Whether to migrate all questions to TriviaQuestion rows in DB
   - Recommendation: Use QuestionSet pattern (JSON files) initially, as done in game_service.py

3. **Should VIP-exclusive trivia discount use same TriviaPromotionConfig or separate?**
   - What we know: TriviaConfig has separate limits for free, VIP, and VIP-exclusive; SPEC.md excludes VIP trivia from this phase
   - What's unclear: Whether VIP players get separate promotions or use same pool with higher limits
   - Recommendation: TriviaConfig singleton supports separate limits per user type; this phase implements free tier

---

## Environment Availability

Step 2.6: SKIPPED (no external dependencies - all project code/config)

---

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
| REQ-16-02 | TriviaPromotionConfig is NEW model (not Promotion) | unit | `pytest tests/unit/test_trivia_models.py::test_trivia_promotion_config_is_new_model -x` | NO |
| REQ-16-03 | Each tier has independent code pool | unit | `pytest tests/unit/test_trivia_discount_service.py::test_tier_pool_independent -x` | NO |
| REQ-16-04 | Player can retire and claim code | unit | `pytest tests/unit/test_trivia_discount_service.py::test_player_retire -x` | NO |
| REQ-16-05 | Wrong answer invalidates code | unit | `pytest tests/unit/test_trivia_discount_service.py::test_wrong_answer_invalidates -x` | NO |
| REQ-16-06 | Admin wizard creates promotion with 3 tiers | integration | `pytest tests/integration/test_trivia_discount_admin.py -x` | NO |
| REQ-16-07 | Daily limits respected per user type | unit | `pytest tests/unit/test_trivia_config_service.py::test_daily_limits -x` | NO |
| REQ-16-08 | Atomic code generation prevents duplicates | unit | `pytest tests/unit/test_trivia_discount_service.py::test_code_generation_atomic -x` | NO |

### Wave 0 Gaps
- [ ] `tests/unit/test_trivia_models.py` - covers REQ-16-02
- [ ] `tests/unit/test_trivia_discount_service.py` - covers REQ-16-01, 03, 04, 05, 08
- [ ] `tests/unit/test_trivia_config_service.py` - covers REQ-16-07
- [ ] `tests/integration/test_trivia_discount_admin.py` - covers REQ-16-06
- [ ] Framework install: pytest - already in requirements.txt

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V4 Access Control | yes | is_admin() check in trivia_discount_admin_handlers.py |
| V5 Input Validation | yes | Validate tier thresholds, code counts, dates in service layer |
| V6 Cryptography | yes | Discount codes use secrets.token_hex for uniqueness |

### Known Threat Patterns for Trivia Discount System

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| User tries to claim code twice (double-spend) | Spoofing | Code status check in claim_code(), atomic transaction |
| Admin creates invalid promotion (negative codes) | Tampering | Validation in create_promotion_config() |
| Concurrent code generation race | Repudiation | SELECT FOR UPDATE lock on tier row |
| Player spoofs answer (modify Telegram callback) | Spoofing | Validate question_idx + answer match server-side |

---

## Sources

### Primary (HIGH confidence)
- `SPEC.md` - Full PRD for trivia discount system with model definitions, FSM states, 17-step wizard
- `services/game_service.py` - Existing trivia implementation (baseline for player flow)
- `services/promotion_service.py` - Commercial PromotionService (shows separation needed)
- `models/models.py` - Existing models, GameRecord already exists
- `handlers/promotion_admin_handlers.py` - PromotionWizardStates (reference for admin wizard)
- `services/store_service.py` - Atomic code generation pattern (SELECT FOR UPDATE)
- `services/scheduler_service.py` - APScheduler job pattern for timeout

### Secondary (MEDIUM confidence)
- `handlers/game_user_handlers.py` - Existing trivia handlers (reference for player flow)
- `.planning/phases/16-expansi-n-de-trivias/16-RESEARCH.md` - Previous research (baseline)

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - using existing aiogram/SQLAlchemy, proven patterns
- Architecture: HIGH - follows existing patterns (wizard FSM, atomic code gen, singleton config)
- Pitfalls: HIGH - clear what to avoid (merging with commercial promotion, race conditions)
- Model separation: HIGH - verified against SPEC.md and promotion_service.py

**Research date:** 2026-05-08
**Valid until:** 30 days (stable tech stack, active development on trivia system)