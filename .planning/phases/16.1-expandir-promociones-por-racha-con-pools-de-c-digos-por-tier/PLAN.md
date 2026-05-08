---
phase: "16.1"
plan: "01"
type: execute
wave: 1
depends_on: []
files_modified:
  - services/trivia_discount_service.py
  - services/game_service.py
  - handlers/trivia_discount_admin_handlers.py
  - handlers/game_user_handlers.py
autonomous: true
requirements:
  - REQ-16.1-01
  - REQ-16.1-02
  - REQ-16.1-03
  - REQ-16.1-04
  - REQ-16.1-05
must_haves:
  truths:
    - "Usuario que alcanza tier recibe codigo SOLO si el pool de ese tier tiene disponibilidad"
    - "Solo el tier mas alto alcanzado genera codigo (no stack)"
    - "Pool agotado = silent skip en generacion, handler muestra notificacion"
    - "Agotamiento del pool NO termina la promocion (otros tiers siguen disponibles)"
  artifacts:
    - path: services/trivia_discount_service.py
      provides: validate_discount_tiers con max_codes, get_tier_pool_status, generate_tiered_discount_code con pool check
      min_lines: 50
    - path: handlers/trivia_discount_admin_handlers.py
      provides: Admin wizard con max_codes por tier en JSON
      min_lines: 30
    - path: handlers/game_user_handlers.py
      provides: Notificacion cuando pool agotado al reclamar
      min_lines: 20
  key_links:
    - from: services/trivia_discount_service.py
      to: models/models.py:DiscountCode
      via: count query por config_id + discount_percentage
      pattern: session.query(DiscountCode).filter.*discount_percentage
    - from: services/game_service.py
      to: services/trivia_discount_service.py
      via: _generate_tier_discount_code llama generate_tiered_discount_code
      pattern: generate_tiered_discount_code
    - from: handlers/game_user_handlers.py
      to: services/game_service.py
      via: _generate_tier_discount_code retorna None si pool agotado
      pattern: _generate_tier_discount_code
---

# Phase 16.1: Expandir Promociones por Racha con Pools de Codigos por Tier

## Objective

Extender el sistema de promociones por racha de trivia para tener pools de codigos independientes por cada tier de descuento. Cada tier en discount_tiers JSON tendra su propio max_codes que controlara combienos codigos pueden generarse para ese tier especificamente.

Purpose:** Permitir que cada tier de descuento tenga un limite independiente de codigos generables, con pool que se agota al issuance (no al redemption).

Output:** Sistema funcional de pools por tier con validacion, conteo, y notificacion de agotamiento.

## Context

Locked decisions (from CONTEXT.md):

| ID | Decision |
|----|----------|
| D-01 | JSON estructura: [{"streak": 5, "discount": 50, "max_codes": 10}, ...] |
| D-02 | Solo el tier mas alto alcanzado genera codigo |
| D-03 | Silent skip cuando pool agotado - retorna None |
| D-04 | Pool depletion NO termina la promocion |

Correction (from RESEARCH.md):**
- Pool se agota cuando se ISSUE/GENERA el codigo (no cuando admin marca USED)
- codes_claimed existente es para tracking de redenciones, NO para pool depletion
- Pool depletion = codes_issued >= max_codes donde codes_issued se cuenta via query de DiscountCode

Key files and interfaces:**

From services/trivia_discount_service.py:
- validate_discount_tiers(tiers: List[dict]) -> tuple[bool, str]
- parse_discount_tiers(config: TriviaPromotionConfig) -> List[dict]
- get_tier_for_streak(config, streak) -> Optional[dict]
- generate_tiered_discount_code(user_id, config_id, discount_percentage, ...) -> Optional[dict]

From services/game_service.py:
- _get_streak_tier_info(user_id, new_streak) -> Optional[dict]
- _generate_tier_discount_code(user_id, config_id, discount_percentage) -> Optional[dict]

## Tasks

### Task 1: Extend validate_discount_tiers() to accept max_codes

Files:** services/trivia_discount_service.py

Action:** Extend validate_discount_tiers() to validate the optional max_codes field in each tier.

Add validation after existing streak/discount checks (around line 530):
```python
max_codes = tier.get('max_codes')
if max_codes is not None:
    if not isinstance(max_codes, int) or max_codes < 0:
        return False, f"Tier {i+1}: max_codes debe ser entero >= 0"
```

Verify:**
```bash
grep -A 5 "max_codes.*not isinstance" services/trivia_discount_service.py
```

Done:** validate_discount_tiers([{"streak": 5, "discount": 50, "max_codes": 10}]) returns (True, "")

---

### Task 2: Add get_tier_pool_status() method

Files:** services/trivia_discount_service.py

Action:** Add new method after parse_discount_tiers() (around line 555):

```python
def get_tier_pool_status(self, config_id: int, streak: int) -> dict:
    """
    Obtiene estado del pool de codigos para un tier especifico.
    Retorna: {codes_issued, max_codes, available, unlimited}
    """
    config = self.get_trivia_promotion_config(config_id)
    if not config:
        return {'codes_issued': 0, 'max_codes': None, 'available': True}

    tier = self.get_tier_for_streak(config, streak)
    if not tier:
        return {'codes_issued': 0, 'max_codes': None, 'available': True}

    max_codes = tier.get('max_codes')
    if max_codes is None:
        return {'codes_issued': 0, 'max_codes': None, 'available': True, 'unlimited': True}

    # Count codes issued for this tier via discount_percentage match
    with SessionLocal() as session:
        codes_issued = session.query(DiscountCode).filter(
            DiscountCode.config_id == config_id,
            DiscountCode.discount_percentage == tier['discount']
        ).count()

    available = codes_issued < max_codes
    return {
        'codes_issued': codes_issued,
        'max_codes': max_codes,
        'available': available
    }
```

Verify:**
```bash
grep -n "def get_tier_pool_status" services/trivia_discount_service.py
```

Done:** get_tier_pool_status(config_id, 5) returns correct counts for tier with streak=5

---

### Task 3: Modify generate_tiered_discount_code() for pool check

Files:** services/trivia_discount_service.py

Action:** Modify generate_tiered_discount_code() to:
1. Accept streak_tier parameter (the streak threshold of the tier)
2. Check pool availability via get_tier_pool_status() BEFORE generating
3. Return None silently if pool exhausted (no exception, no message)
4. Do NOT use codes_claimed for pool check - pool is tracked via count query

Modify the method signature to add streak_tier:
```python
def generate_tiered_discount_code(
    self,
    user_id: int,
    config_id: int,
    discount_percentage: int,
    streak_tier: int,  # NEW: needed for pool check
    username: Optional[str] = None,
    first_name: Optional[str] = None
) -> Optional[dict]:
```

Add pool check before generating code (around line 600):
```python
    # NEW: Check tier pool availability BEFORE generating
    tier_pool = self.get_tier_pool_status(config_id, streak_tier)
    if not tier_pool['available']:
        logger.info(f"Pool exhausted for tier {streak_tier}")
        return None  # Silent skip
```

Verify:**
```bash
grep -B 2 -A 3 "tier_pool\['available'\]" services/trivia_discount_service.py
```

Done:** When pool is exhausted, returns None without exception; promotion continues

---

### Task 4: Update _generate_tier_discount_code() to pass streak_tier

Files:** services/game_service.py

Action:** Modify _generate_tier_discount_code() to pass the streak_tier to generate_tiered_discount_code().

Current call (around line 1157):
```python
self._trivia_discount_service.generate_tiered_discount_code(
    user_id=user_id,
    config_id=config_id,
    discount_percentage=discount_percentage,
    ...
)
```

Update to include streak_tier:
```python
# Get tier info for the streak
tier_info = self._trivia_discount_service.get_tier_for_streak(
    self._trivia_discount_service.get_trivia_promotion_config(config_id),
    current_streak
)
self._trivia_discount_service.generate_tiered_discount_code(
    user_id=user_id,
    config_id=config_id,
    discount_percentage=discount_percentage,
    streak_tier=tier_info['streak'] if tier_info else 0,  # NEW
    ...
)
```

Also update _get_streak_tier_info() to include streak_tier in returned dict so handlers can access it.

Verify:**
```bash
grep -n "streak_tier" services/game_service.py
```

Done:** _generate_tier_discount_code passes correct streak_tier to service

---

### Task 5: Extend admin wizard for max_codes per tier

Files:** handlers/trivia_discount_admin_handlers.py

Action:** Extend the multi-tier wizard to accept max_codes per tier.

Approach:** Allow admin to include max_codes in the JSON directly:
```json
[{"streak": 5, "discount": 50, "max_codes": 10}, {"streak": 10, "discount": 75, "max_codes": 5}]
```

Extend process_discount_tiers() (around line 260) to:
1. Validate that if max_codes is present in any tier, it must be a valid integer >= 0
2. Store the JSON as-is (includes max_codes per tier) in state for confirmation

The validation is already handled by validate_discount_tiers() which will be extended in Task 1.

Verify:**
```bash
grep -n "max_codes" handlers/trivia_discount_admin_handlers.py | head -20
```

Done:** Admin can specify max_codes per tier in multi-tier JSON, validated by service

---

### Task 6: Handle pool exhaustion notification in handler

Files:** handlers/game_user_handlers.py

Action:** When _generate_tier_discount_code() returns None (pool exhausted), show notification.

In trivia_answer() around line 305-320 (after calling _generate_tier_discount_code):
```python
if discount and discount.get('code'):
    # ... show success message with code ...
else:
    # Pool exhausted - show notification but allow user to continue
    header = service._select_template(service.STREAK_TEMPLATES['pool_exhausted_header'])
    message = (
        f"{header}\n\n"
        f"<i>Este nivel de descuento esta agotado, pero su racha continua.</i>\n\n"
        f"Puede seguir jugando para alcanzar el siguiente nivel."
    )
    keyboard = streak_continue_keyboard()  # Allow them to continue
```

Similar handling needed in trivia_vip_answer() around line 554-571.

Also add pool exhaustion template strings to GameService.STREAK_TEMPLATES:
```python
'pool_exhausted_header': [
    "🎩 Lucien: El Gabinete de Oportunidades ha cerrado este nivel.",
    "🎩 Lucien: Esta puerta se ha cerrado, pero hay otras esperando."
],
```

Verify:**
```bash
grep -n "pool_exhausted" handlers/game_user_handlers.py
```

Done:** User sees notification when pool exhausted but can continue playing

---

## Threat Model

Trust Boundaries:** None new - all operations within existing trust boundaries.

STRIDE Threat Register:**

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-16.1-01 | Tampering | discount_tiers JSON | mitigate | validate_discount_tiers() rejects non-integer or negative max_codes |
| T-16.1-02 | Denial | Pool exhaustion race | accept | Eventual consistency acceptable for small pool sizes |

---

## Verification

Service-level tests:**
```bash
python -c "
from services.trivia_discount_service import TriviaDiscountService
svc = TriviaDiscountService()

# Test 1: validate accepts max_codes
valid, msg = svc.validate_discount_tiers([{'streak': 5, 'discount': 50, 'max_codes': 10}])
assert valid, f'Should validate: {msg}'
print('PASS: validate_discount_tiers accepts max_codes')

# Test 2: validate rejects invalid max_codes
valid, msg = svc.validate_discount_tiers([{'streak': 5, 'discount': 50, 'max_codes': -1}])
assert not valid, 'Should reject negative max_codes'
print('PASS: validate_discount_tiers rejects invalid max_codes')

# Test 3: get_tier_pool_status exists
pool = svc.get_tier_pool_status(999, 5)  # Non-existent config
assert 'codes_issued' in pool
print('PASS: get_tier_pool_status returns correct structure')
"
```

Manual integration test:**
1. Admin creates multi-tier promo with max_codes=2 for tier 15
2. User 1 completes streak 15, gets code (pool: 1/2)
3. User 2 completes streak 15, gets code (pool: 2/2)
4. User 3 completes streak 15, gets None notification, keeps streak

---

## Success Criteria

1. validate_discount_tiers() validates max_codes field (optional, integer >= 0)
2. get_tier_pool_status() returns correct codes_issued count per tier
3. generate_tiered_discount_code() returns None when pool exhausted for tier
4. Admin wizard accepts max_codes per tier in multi-tier JSON
5. Handler shows notification when pool exhausted but user keeps streak
6. Pool depletion does NOT end the promotion (other tiers remain available)

---

## Output

After completion, create .planning/phases/16.1-expandir-promociones-por-racha-con-pools-de-c-digos-por-tier/16.1-01-SUMMARY.md