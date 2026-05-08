---
phase: "16.1"
plan: "01"
type: execute
wave: 1
depends_on: []
gap_closure: true
files_modified:
  - services/trivia_discount_service.py
  - services/game_service.py
  - handlers/trivia_discount_admin_handlers.py
  - handlers/game_user_handlers.py
autonomous: true
requirements: []
must_haves:
  truths:
    - "Usuario que alcanza tier recibe codigo SOLO si el pool de ese tier tiene disponibilidad"
    - "Solo el tier mas alto alcanzado genera codigo (no stack)"
    - "Pool agotado = silent skip en generacion, handler muestra notificacion"
    - "Agotamiento del pool NO termina la promocion (otros tiers siguen disponibles)"
    - "Admin wizard muestra max_codes por tier en confirmacion (fix gap UAT-01)"
    - "Trivia discount creation no crashea por metodo inexistente (fix gap UAT-02)"
    - "Error handler no crashea al hacer log de excepciones (fix gap UAT-03)"
  artifacts:
    - path: handlers/trivia_discount_admin_handlers.py:672
      provides: Fix get_active_promotions → get_all_promotions(active_only=True)
      min_lines: 1
    - path: handlers/error_handler_middleware.py:109
      provides: Fix handler.__name__ → handler.callback.__name__
      min_lines: 1
---

# Phase 16.1: Gap Closure — Corregir 3 Blocker Gaps del UAT

## Objective

El plan original 16.1-01-SUMMARY.md está incomplete debido a 3 gaps diagnosticados en el UAT. Este plan los corrige:

1. **Gap UAT-01 (major):** Admin wizard no muestra `max_codes` en la confirmación — el usuario no ve los límites de pool
2. **Gap UAT-02 (blocker):** Crasha al crear trivia discount — línea 672 llama `promo_service.get_active_promotions()` que no existe
3. **Gap UAT-03 (blocker):** Error handler crashea al intentar loguear excepciones por usar `handler.__name__` en un `HandlerObject` dataclass

## Context

El plan original (PLAN.md) fue escrito con las tareas correctas, pero la implementación original falló en estos puntos específicos. Las tareas 1-6 del plan original ya fueron ejecutadas parcialmente (SUMMARY existe), pero los gaps persisten porque los bugs de código impiden el flujo completo.

## Tasks

### Task 1: Fix Gap UAT-02 — Line 672 get_active_promotions → get_all_promotions(active_only=True)

Files: handlers/trivia_discount_admin_handlers.py

Root cause: Línea 672 llama `promo_service.get_active_promotions()` pero este método no existe en PromotionService. El método correcto es `get_all_promotions(active_only=True)`.

Action: En la línea 672 (o la región donde se llama get_active_promotions), cambiar:

```python
# WRONG:
active_promos = promo_service.get_active_promotions()

# CORRECT:
active_promos = promo_service.get_all_promotions(active_only=True)
```

Read first:
- handlers/trivia_discount_admin_handlers.py (buscar todas las llamadas a get_active_promotions)

Verify:
```bash
grep -n "get_active_promotions" handlers/trivia_discount_admin_handlers.py
# Should return nothing (no occurrences after fix)
grep -n "get_all_promotions" handlers/trivia_discount_admin_handlers.py
# Should show the corrected call with active_only=True
```

Done: Trivia discount creation no longer crashes on this call.

---

### Task 2: Fix Gap UAT-03 — Line 109 handler.__name__ → handler.callback.__name__

Files: handlers/error_handler_middleware.py

Root cause: Línea 109 accede `handler.__name__` directamente, pero `HandlerObject` es un dataclass wrapper. El handler real está en `handler.callback`. Hay que usar `handler.callback.__name__`.

Action: En handlers/error_handler_middleware.py, alrededor de línea 109, cambiar:

```python
# WRONG:
f"{handler.__module__}.{handler.__name__}"

# CORRECT:
f"{handler.callback.__module__}.{handler.callback.__name__}"
```

Read first:
- handlers/error_handler_middleware.py (buscar todos los usos de handler.__name__)

Verify:
```bash
grep -n "handler.__name__" handlers/error_handler_middleware.py
# Should return nothing (no bare handler.__name__ after fix)
grep -n "handler.callback.__name__" handlers/error_handler_middleware.py
# Should show the corrected usage
```

Done: Error handler middleware no longer crashes when logging exceptions from HandlerObject-wrapped handlers.

---

### Task 3: Fix Gap UAT-01 — Mostrar max_codes por tier en admin wizard confirmation

Files: handlers/trivia_discount_admin_handlers.py

Root cause: El admin wizard valida max_codes en el JSON pero no lo despliega en el mensaje de confirmación. El usuario no ve qué límites tiene cada tier.

Action: En el paso de confirmación del wizard multi-tier, donde se muestra el resumen de tiers, agregar la línea de max_codes por cada tier:

Buscar la función/método que arma el mensaje de confirmación de discount_tiers y agregar:

```python
# Después de mostrar streak y discount, agregar:
max_codes = tier.get('max_codes')
if max_codes is not None:
    tier_summary += f"  → Pool: {codes_issued}/{max_codes} códigos disponibles\n"
else:
    tier_summary += f"  → Pool: ilimitado\n"
```

Read first:
- handlers/trivia_discount_admin_handlers.py (buscar donde se arma el mensaje de confirmación de tiers)
- services/trivia_discount_service.py (get_tier_pool_status para obtener codes_issued por tier)

Verify:
```bash
grep -n "max_codes" handlers/trivia_discount_admin_handlers.py | grep -E "tier_summary|confirmation|Pool"
# Should show max_codes being displayed in confirmation
```

Done: Admin ve "Pool: 3/10 códigos disponibles" por cada tier en la confirmación.

---

## Verification

```bash
# Gap UAT-02: trivia discount creation doesn't crash
python -c "
from handlers.trivia_discount_admin_handlers import AdminTriviaDiscountHandlers
print('Import OK - no get_active_promotions call at import time')
"

# Gap UAT-03: error handler doesn't crash on HandlerObject
python -c "
from handlers.error_handler_middleware import error_handler_middleware
print('error_handler_middleware imported OK')
"

# Gap UAT-01: max_codes shown in confirmation
grep -n "Pool:" handlers/trivia_discount_admin_handlers.py | head -5
```

## Success Criteria

1. ✅ get_active_promotions() reemplazado por get_all_promotions(active_only=True) — trivia creation no crashea
2. ✅ handler.__name__ reemplazado por handler.callback.__name__ — error handler no crashea en log
3. ✅ Admin wizard muestra max_codes por tier en confirmación — usuario ve límites de pool

---

## Output

After completion, update 16.1-01-SUMMARY.md with gap closure results.