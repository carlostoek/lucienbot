# Phase 16: Expansión de Trivias - Context

**Gathered:** 2026-05-07
**Status:** Ready for planning
**Source:** PRD Express Path (.planning/PLAN-trivia-protection.md)

<domain>
## Phase Boundary

Sistema ampliado de trivia con dos modos operativos:

- **Trivia Libre (sin promo):** Acumular besitos sin presión, con bonus VR cada 3-6 preguntas
- **Trivia con Promo:** Participar por descuentos con protección comprable con besitos al momento de fallar

**Economic闭环:** Usuarios sin besitos → juega libre para acumular → regresa a promo con protección.

</domain>

<decisions>
## Implementation Decisions

### Game Types
- `trivia_free` — Trivia sin promo (free), 1 besito por acierto, límite 7 diario
- `trivia_free_vip` — Trivia sin promo (vip), 5 besitos por acierto, límite 15 diario
- `trivia_promo` — Trivia con promo (free), NO otorga besitos, límite 20 diario
- `trivia_promo_vip` — Trivia con promo (vip), NO otorga besitos, límite 30 diario

### Protection Cost
- Campo `protection_tiers` en `TriviaPromotionConfig` (JSON)
- Fórmula fallback: `5 + (streak // 3) * 5`
- Protección debit besitos y mantiene streak cuando se acepta

### FSM States
```python
class TriviaStreakStates(StatesGroup):
    waiting_streak_choice = State()     # existente
    streak_continue = State()           # existente
    promo_wrong_answer = State()        # NUEVO: falló, ofrece protección
    free_bonus = State()                # NUEVO: pregunta bonus activa
```

### VR Bonus (libre)
- Cada 3-6 preguntas (random.randint(3,6))
- Reemplaza base: +10 besitos en lugar de +1/+5

### Daily Limits (separados por modo)
- `daily_trivia_limit_promo_free` = 20 (default)
- `daily_trivia_limit_promo_vip` = 30 (default)
- `can_play_promo()` separada de `can_play()`

### Besitos en Promo
- NO se otorgan besitos en modo promo
- Fuente: `TransactionSource.TRIVIA_PROMO` (para trazabilidad)

### Claude's Discretion
- Diseño de UI del menú trivia (keyboards)
- Gestión de errores y edge cases
- Tests de integración para flujos completos

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Game Service (Phase 14)
- `services/game_service.py` — GameService existente, métodos `play_trivia()`, `can_play()`
- `models/models.py` — TriviaConfig, TriviaPromotionConfig, GameRecord, TransactionSource
- `handlers/game_user_handlers.py` — trivia handlers existentes

### Gamification
- `services/besito_service.py` — BesitoService, métodos de balance y transacciones
- `services/mission_service.py` — RewardService para entrega de recompensas

### Migration Patterns
- `migrations/` — Migraciones Alembic existentes para referencia de patrones

</canonical_refs>

<specifics>
## Specific Ideas

### Flujo Trivia Libre
```
play_trivia_free(user_id)
  → Verificar límite diario
  → Cargar pregunta (set general)
  → is_bonus = _is_bonus_question()  # cada 3-6 preguntas
  → Usuario responde
    ├→ Correcta + is_bonus → +10 besitos (reemplaza base)
    ├→ Correcta + !is_bonus → +1 (free) o +5 (vip)
    └→ Incorrecta → streak=0, sin protección
  → ¿Streak milestone? (3→+2, 5→+5, 7→+10 extra)
  → ¿Alcanzó límite diario? → fin
```

### Flujo Trivia Promo
```
play_trivia_promo(user_id)
  → Verificar límite diario
  → Cargar pregunta
  → Usuario responde
    ├→ Correcta → streak+1 → ¿tier? → genera código / continúa
    └→ Incorrecta → protection_offer()
```

### Flujo Protección
```
protection_offer(user_id, streak)
  → cost = get_protection_cost(promo_config, streak)
  → balance = besito_service.get_balance(user_id)
  → ¿balance >= cost?
    ├→ SÍ → teclado: [🛡️ Proteger (-X)] [❌ Continuar sin]
    └→ NO → teclado: [❌ Continuar sin]
```

### Límites Separados
- `can_play(user_id, 'trivia_free')` vs `can_play(user_id, 'trivia_promo')`
- Contadores separados en DailyUsage

</specifics>

<deferred>
## Deferred Ideas

Ninguna — PRD cubre scope completo de Phase 16.

</deferred>

---

*Phase: 16-expansion-de-trivias*
*Context gathered: 2026-05-07 via PRD Express Path*