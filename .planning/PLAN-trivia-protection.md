# Plan de Implementación: Sistema de Trivia con Protección por Besitos

**Fase:** 1 de 1 (MVP)
**Fecha:** 2026-05-06
**Estado:** LISTO PARA EJECUTAR

---

## 1. Contexto y Objetivo

Sistema ampliado de trivia con dos modos operativos:

- **Trivia Libre (sin promoción):** Acumular besitos sin presión, con bonus VR cada 3-6 preguntas
- **Trivia con Promo:** Participar por descuentos con protección comprable con besitos al momento de fallar

**Economic闭环:** Usuarios sin besitos → juega libre para acumular → regresa a promo con protección.

---

## 2. Arquitectura Propuesta

### 2.1 Game Types (nuevos valores en `game_type`)

| game_type | Descripción | Besitos | Límite diario |
|-----------|-------------|---------|---------------|
| `trivia_free` | Trivia sin promo (free) | 1 por acierto | 7 |
| `trivia_free_vip` | Trivia sin promo (vip) | 5 por acierto | 15 |
| `trivia_promo` | Trivia con promo (free) | NO otorga besitos | 20 |
| `trivia_promo_vip` | Trivia con promo (vip) | NO otorga besitos | 30 |

> **Decisión:** No se otorgan besitos en modo promo. Si esto es complejo de implementar inicialmente, se mantienen besitos como actualmente (fuente `TRIVIA`) y se separa después.

### 2.2 Modelo de Protección Configurable

Se reutiliza el campo `discount_tiers` existente en `TriviaPromotionConfig` para almacenar costos de protección:

```json
[
  {"streak": 5, "discount": 10, "protection_cost": 5},
  {"streak": 10, "discount": 20, "protection_cost": 10},
  {"streak": 15, "discount": 30, "protection_cost": 15}
]
```

**Fórmula fallback** (si no hay configuración): `5 + (streak // 3) * 5`

### 2.3 FSM States

```python
class TriviaStreakStates(StatesGroup):
    waiting_streak_choice = State()     # existente
    streak_continue = State()           # existente
    promo_wrong_answer = State()        # NUEVO: falló, ofrece protección
    free_bonus = State()                # NUEVO: pregunta bonus activa
```

### 2.4 Límites Diarios

Se agregan campos a `TriviaConfig`:

- `daily_trivia_limit_promo_free` = 20 (default)
- `daily_trivia_limit_promo_vip` = 30 (default)

Límites separados: `can_play(user_id, 'trivia_promo')` vs `can_play(user_id, 'trivia_free')`.

---

## 3. Flujo de Usuario Detallado

### 3.1 Menú de Entrada

```
MINIJUEGOS
├─ 🎲 Lanzar los dados
├─ ❓ Trivia Libre              ← siempre visible
└─ 🎫 Trivia con Promo         ← solo si hay promo activa
```

**Implementación:** Modificar `game_menu_keyboard` para agregar botón condicional.

### 3.2 Flujo Trivia Libre

```
play_trivia_free(user_id)
        ↓
Verificar límite diario (trivia_free o trivia_free_vip)
        ↓
Cargar pregunta (set general)
        ↓
is_bonus = _is_bonus_question()  # cada 3-6 preguntas (VR)
        ↓
Usuario responde
        ├→ Correcta + is_bonus → +10 besitos (reemplaza base)
        ├→ Correcta + !is_bonus → +1 (free) o +5 (vip)
        └→ Incorrecta → streak=0, sin protección
        ↓
¿Streak milestone? (3→+2, 5→+5, 7→+10 extra besitos)
        ↓
¿Alcanzó límite diario? → fin
```

### 3.3 Flujo Trivia Promo

```
play_trivia_promo(user_id)
        ↓
Verificar límite diario (trivia_promo o trivia_promo_vip)
        ↓
Cargar pregunta (question_set de promo o general)
        ↓
Usuario responde
        ├→ Correcta → streak+1 → ¿tier? → genera código / continúa
        │
        └→ Incorrecta → protection_offer()
                               ↓
                    ¿Tiene besitos >= costo?
                        ├→ SÍ → teclado: [Proteger (-X)] [Continuar sin]
                        │       ├→ Elige proteger → debitar besitos, streak se mantiene
                        │       └→ Elige no proteger → streak=0, CANCELLED
                        │
                        └→ NO → teclado: [Continuar sin] → streak=0, CANCELLED
```

### 3.4 Flujo de Protección

```
protection_offer(user_id, streak)
        ↓
cost = get_protection_cost(promo_config, streak)
balance = besito_service.get_balance(user_id)
        ↓
¿balance >= cost?
        ├→ SÍ → teclado con ambas opciones
        └→ NO → teclado solo "Continuar sin protección"
        ↓
user selects:
        ├→ "Proteger" → debitar besitos, return {protected: True}
        └→ "Continuar" → return {protected: False}
```

---

## 4. Pasos de Implementación

### Fase A: Preparación (modelos y servicios base)

**A.1** Agregar `protection_cost_tiers` a `TriviaPromotionConfig`
- Campo nuevo `protection_tiers` tipo `Text` (JSON), nullable
- Alternativa: reuse existing `discount_tiers` field

**A.2** Agregar campos de límites promo a `TriviaConfig`
```python
daily_trivia_limit_promo_free = Column(Integer, default=20)
daily_trivia_limit_promo_vip = Column(Integer, default=30)
```

**A.3** Crear migración Alembic para los campos nuevos

**A.4** Agregar `can_play_promo()` en `GameService`
- Copia de `can_play()` pero con contadores `trivia_promo` / `trivia_promo_vip`

---

### Fase B: Servicios

**B.1** Crear `calculate_protection_cost(streak, promo_config)` en `GameService`
```python
def calculate_protection_cost(self, streak: int, promo_config) -> int:
    if promo_config.protection_tiers:
        tiers = json.loads(promo_config.protection_tiers)
        for tier in tiers:
            if tier['streak'] <= streak:
                return tier['protection_cost']
    return 5 + (streak // 3) * 5  # fallback
```

**B.2** Crear `_is_bonus_question()` en `GameService`
- Mantiene contador interno por usuario (`interactions_since_bonus`)
- Retorna `True` si `random.randint(3, 6) == interactions_since_bonus`
- Resetea contador al activar bonus

**B.3** Modificar `play_trivia()` o crear `play_trivia_promo()` y `play_trivia_free()`
- `play_trivia_promo()`: no acredita besitos, incluye lógica de protección
- `play_trivia_free()`: acredita besitos según VIP/free, incluye VR bonus

**B.4** Crear `get_protection_offer(user_id, streak, cost)` en `GameService`
- Verifica balance de besitos
- Retorna `{can_protect: bool, cost: int, balance: int}`

**B.5** Crear `purchase_protection(user_id, cost)` en `BesitoService`
- Valida balance >= cost
- Debita besitos con `TransactionSource.PROTECTION`

---

### Fase C: Handlers

**C.1** Nuevo handler `trivia_menu(callback)`
- Detecta si hay promo activa
- Muestra `trivia_menu_keyboard` (libre + promo condicional)

**C.2** Modificar `game_menu(callback)`
- Cambiar callback de `game_trivia` → `trivia_menu`

**C.3** Nuevo handler `trivia_promo_callback(callback)`
- Verifica promo activa
- Inicia `play_trivia_promo()` con estado `TriviaStreakStates.promo_playing`

**C.4** Nuevo handler `trivia_free_callback(callback)`
- Inicia `play_trivia_free()` con estado `TriviaStreakStates.free_playing`

**C.5** Modificar `trivia_answer()` para routing
- Detectar si es modo promo o libre (del estado FSM)
- Dirigir a `handle_promo_answer()` o `handle_free_answer()`

**C.6** Nuevo handler `trivia_protection_accept(callback)`
- FSM: `TriviaStreakStates.promo_wrong_answer`
- Ejecuta `purchase_protection()`
- Continúa trivia promo

**C.7** Nuevo handler `trivia_protection_decline(callback)`
- FSM: `TriviaStreakStates.promo_wrong_answer`
- Resetea streak, CANCELLED de código activo
- Regresa al menú

---

### Fase D: Keyboards

**D.1** `trivia_menu_keyboard(has_promo: bool)` - menú de selección de modo

**D.2** `protection_offer_keyboard(can_protect: bool, cost: int, balance: int)`
- Si `can_protect`: [🛡️ Proteger (-{cost})] / [❌ Continuar sin protección]
- Si `!can_protect`: [❌ Continuar sin protección]

**D.3** `free_bonus_keyboard()` - teclado para pregunta bonus VR

---

### Fase E: Admin - Configurar Protección

**E.1** Modificar wizard de `TriviaDiscountStates` para incluir paso de `protection_tiers`
- Opción: usar fórmula por defecto o configurar tiers manualmente
- UI: lista de tiers con costos de protección

**E.2** Guardar `protection_tiers` JSON en `TriviaPromotionConfig.protection_tiers`

---

### Fase F: Testing y Verificación

**F.1** Tests unitarios para:
- `calculate_protection_cost()`
- `_is_bonus_question()`
- `get_protection_offer()`
- `play_trivia_promo()` y `play_trivia_free()`

**F.2** Tests de integración:
- Flujo completo promo: jugar → fallar → proteger → continuar
- Flujo completo libre: jugar → bonus → acierto → besitos
- Verificar límites separados

---

## 5. Archivos a Modificar

| Archivo | Cambios |
|---------|---------|
| `models/models.py` | Agregar campos `protection_tiers`, límites promo a `TriviaConfig` |
| `migrations/*.py` | Migración para campos nuevos |
| `services/game_service.py` | Métodos nuevos: `play_trivia_promo`, `play_trivia_free`, `calculate_protection_cost`, `_is_bonus_question`, `get_protection_offer` |
| `services/besito_service.py` | Método `purchase_protection` |
| `handlers/game_user_handlers.py` | Nuevos handlers: `trivia_menu`, `trivia_promo_callback`, `trivia_free_callback`, `trivia_protection_accept`, `trivia_protection_decline`. Modificar `trivia_answer` |
| `keyboards/inline_keyboards.py` | Nuevos keyboards: `trivia_menu_keyboard`, `protection_offer_keyboard`, `free_bonus_keyboard` |
| `handlers/trivia_discount_admin_handlers.py` | Agregar paso de configuración de protección |

---

## 6. Migración Requerida

```sql
-- Agregar protection_tiers a trivia_promotion_configs
ALTER TABLE trivia_promotion_configs
ADD COLUMN protection_tiers TEXT;

-- Agregar límites promo a trivia_config
ALTER TABLE trivia_config
ADD COLUMN daily_trivia_limit_promo_free INTEGER DEFAULT 20;

ALTER TABLE trivia_config
ADD COLUMN daily_trivia_limit_promo_vip INTEGER DEFAULT 30;
```

---

## 7. Criterios de Verificación

| # | Criterio | Método de verificación |
|---|----------|----------------------|
| 1 | Menú muestra trivia libre siempre y promo solo con promo activa | Botón promo visible solo con promo activa |
| 2 | Límites diarios son independientes entre modos | Jugar 5 promo + 5 libre = 5+5 usados, no 10+5 |
| 3 | Protección offered al fallar en promo | Simular respuesta incorrecta en promo |
| 4 | Protección costing depends on streak tier | Verificar costo con streak 3 vs streak 10 |
| 5 | Protection debita besitos y mantiene streak | Proteger y verificar balance y streak |
| 6 | Free bonus every 3-6 questions | Contar preguntas hasta bonus (promedio ~4.5) |
| 7 | Free bonus replaces base | VIP bonus = +10 no +1+5+5 |
| 8 | Admin puede configurar protection_tiers | Wizard de promo incluye paso de protección |
| 9 | Sin promo = no besitos en promo | Jugar modo promo y verificar que balance no cambia |

---

## 8. Decisiones Confirmadas

| # | Decisión | Valor |
|---|----------|-------|
| 1 | Campo `protection_tiers` | Campo NUEVO en `TriviaPromotionConfig` (no reutilizar `discount_tiers`) |
| 2 | Flujo "ir a libre y regresar" | Simplificado: si no puede/no quiere pagar, pierde todo |
| 3 | Besitos en promo | Separados con `TransactionSource.TRIVIA_PROMO` (no otorga besitos) |

---

## 9. Decisiones Técnicas Adicionales Confirmadas

| # | Decisión | Valor |
|---|----------|-------|
| 1 | Límites diarios | Separados por modo (libre vs promo) |
| 2 | Game types | `trivia_free`, `trivia_free_vip`, `trivia_promo`, `trivia_promo_vip` |
| 3 | Protección configurable | En `protection_tiers` JSON de promo activa |
| 4 | Fórmula fallback protección | `5 + (streak // 3) * 5` si no hay config |
| 5 | VR bonus en libre | Cada 3-6 preg, reemplaza base (+10 vs +1/+5) |

---

*Plan preparado para revisión y ejecución*