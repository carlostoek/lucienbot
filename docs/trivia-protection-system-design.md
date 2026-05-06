# Sistema de Trivia con Protección por Besitos - Diseño

Fecha: 2026-05-06
Estado: DISEÑO COMPLETO → listo para implementación

---

## Resumen Ejecutivo

Rediseño del sistema de trivia para crear un **economic闭环** donde los besitos tengan utilidad real:
- **Modo Promo**: Streak-based, ganar descuentos, protección comprable con besitos
- **Modo Libre**: Acumular besitos sin presión, VR bonuses, preguntas especiales

---

## Modos de Trivia

### Modo Promo (Trivia con Descuento)

**Objetivo:** Completar tiers de descuento para promociones activas.

**Límites:**
- Free: 20 preguntas/día (eran 7, aumentadas por promoción activa)
- VIP: 30 preguntas/día (eran 15, aumentadas por promoción activa)

**Sistema de tiers:**
- Configurable por promoción (ej: 5→10%, 10→20%, 15→30%)
- Streak se rompe con 1 respuesta incorrecta (sin protección)
- Al completar tier → código de descuento generado

**Protección con Besitos:**
Cuando el usuario falla una pregunta, tiene la opción de comprar protección:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 🎩 Lucien observa su tropiezo con calma...  ┃
┃ El velo de protección le susurra:            ┃
┃ "Puedo salvar lo que ha construido.          ┃
┃  Pero el precio debe pagarse."               ┃
┃                                              ┃
┃ ┌─────────────────────────────────────────┐  ┃
┃ │ 🛡️ PROTEGER (-{cost} besitos)          │  ┃
┃ │    Mantiene su streak de {streak}       │  ┃
┃ └─────────────────────────────────────────┘  ┃
┃ ┌─────────────────────────────────────────┐  ┃
┃ │ ❌ CONTINUAR SIN PROTECCIÓN             │  ┃
┃ │    Su descuento {current_discount}%     │  ┃
┃ │    y racha se perderán                  │  ┃
┃ └─────────────────────────────────────────┘  ┃
┃                                              ┃
┃ Besitos disponibles: {balance}              ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

**Costo de protección (fórmula):**
```
protection_cost = 5 + (current_streak // 3) * 5
```

| Streak | Costo | Besitos necesarios para proteger |
|--------|-------|--------------------------------|
| 1-2 | 5 besitos | "Early protection" - barato |
| 3-5 | 10 besitos | Streak 3 = 10, Streak 5 = 10 |
| 6-8 | 15 besitos | Streak 8 = 15 |
| 9-11 | 20 besitos | - |
| 12-14 | 25 besitos | Tier 2 |
| 15+ | 30 besitos | Tier 3+ |

**Reglas de la protección:**
1. **Duración:** 1 sola pregunta — si fallas después de comprar protección, pierdes todo
2. **No acumulable entre sesiones** — solo existe durante la sesión actual
3. **Solo besitos** — no se puede comprar con dinero real
4. **Si no tiene besitos suficientes** → solo ve opción "Continuar sin protección"
5. **Si tiene besitos suficientes** → ve ambas opciones

**Comportamiento del sistema:**

```
ESCENARIO 1: Usuario con streak 7, 20 besitos
→ Falla pregunta
→ Ve: "Proteger por 15 besitos"
→ Tiene 20 besitos → PUEDE proteger
→ Elige proteger → gasta 15 besitos
→ Streak se mantiene en 7
→ Sigue jugando

ESCENARIO 2: Usuario con streak 7, solo 5 besitos
→ Falla pregunta
→ Ve: "Proteger por 15 besitos"
→ Tiene 5 besitos → NO PUEDE permitirselo
→ Solo ve: "Continuar sin protección"
→ Pierde streak y descuento

ESCENARIO 3: Usuario con streak 12, 30 besitos
→ Falla pregunta
→ Ve: "Proteger por 25 besitos" (tier 2)
→ Tiene 30 besitos → PUEDE
→ Protege → mantiene streak 12
→ Sigue jugando para llegar a tier 3
```

---

### Modo Libre (Trivia Libre)

**Objetivo:** Acumular besitos sin presión, para usar en modo promo.

**Límites (separados del modo promo):**
- Free: 7 preguntas/día
- VIP: 15 preguntas/día

**Recompensas base:**
- Free: 1 besito por respuesta correcta
- VIP: 5 besitos por respuesta correcta

**Bonus VR (Razón Variable):**
Cada 3-6 preguntas (aleatorio), aparece una PREGUNTA BONO:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 🎰 PREGUNTA BONO 🎰                          ┃
┃ +5 besitos asegurados                         ┃
┃ Si aciertas, el DOBLE (+10)                  ┃
┃ El riesgo: 0 besitos si fallas                ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

- **Frecuencia:** 3-6 preguntas aleatorio (VR puro)
- **Premio asegurable:** +5 besitos siempre (sin importar acierto)
- **Premio bonus:** Si acierta → +5 adicionales (+10 total)
- **Si falla:** 0 besitos extra (pero no pierde besitos base)
- **El bono REEMPLAZA la base** (no suma) — el VIP no obtiene 5+5, solo 5+5 del bonus si acierta

**Rachas en modo libre (besitos extra):**
- Streak 3: +2 besitos extra
- Streak 5: +5 besitos extra
- Streak 7: +10 besitos extra

Esto hace que el modo libre tenga objetivo pero alcanzable.

---

## Flujo de Usuario

```
┌─────────────────────────────────────────────────────────────┐
│                     MENÚ DE TRIVIA                          │
│                                                             │
│   [Trivia con Descuento]     [Trivia Libre]                 │
│        🎫                      🎁                           │
│   Con promoción activa        Sin promoción                  │
│   Gana descuentos            Gana besitos                    │
└─────────────────────────────────────────────────────────────┘
```

###闭环 Económico

```
USUARIO NUEVO (0 besitos)
│
├→ Entra a TRIVIA LIBRE
│   └→ Juega sin presión, acumula besitos
│       └→ Cada 3-6 preguntas: PREGUNTA BONO (+3-5 besitos)
│           └→ Acumula 30-50 besitos
│
├→ [Ya tiene besitos] → Entra a TRIVIA CON DESCUENTO
│   └→ Llega a streak 8, falla pregunta
│       └→ Ve: "Proteger por 15 besitos"
│           └→Tiene 20 besitos → Protege
│               └→ Sigue buscando el 20% descuento
│
└→ [Sin besitos] → Entra a TRIVIA CON DESCUENTO
    └→ Llega a streak 5, falla
        └→ Ve: "Proteger por 15 besitos"
            └→ Solo tiene 5 besitos → NO PUEDE
                └→ Pierde streak
                    └→ Se va a TRIVIA LIBRE a ganar besitos
```

---

## Cambios Técnicos Requeridos

### 1. Separación de Game Types

Actual: `game_type` = 'trivia', 'trivia_vip'
Nuevo: `game_type` = 'trivia_promo', 'trivia_promo_vip', 'trivia_free', 'trivia_free_vip'

### 2. Nuevos Métodos en GameService

| Método | Descripción |
|--------|-------------|
| `get_trivia_modes()` | Devuelve info de ambos modos (límites, promo activa, etc.) |
| `play_trivia_free()` | Lógica de modo libre con VR bonuses |
| `play_trivia_promo()` | Lógica de modo promo con protección |
| `calculate_protection_cost()` | Fórmula de costo de protección |
| `check_protection_offer()` | Determina si usuario puede ver opción de protección |
| `_is_bonus_question()` | Determina si la pregunta actual es bonus VR |

### 3. Nuevos Handlers

| Handler | Función |
|---------|---------|
| `trivia_menu()` | Muestra selección de modo |
| `trivia_promo_callback` | Inicia modo promo con promo_id |
| `trivia_free_callback` | Inicia modo libre |
| `trivia_protection_offer()` | Muestra UI de protección al fallar en promo |
| `trivia_protection_accept()` | Procesa compra de protección |
| `trivia_protection_decline()` | Continúa sin protección |

### 4. Estado FSM

```python
class TriviaStates:
    # Modo Promo
    promo_playing = State()      # Jugando modo promo
    promo_wrong_answer = State() # Falló, mostrando opciones de protección
    promo_protecting = State()   # Compró protección, 1 pregunta garantizada

    # Modo Libre
    free_playing = State()       # Jugando modo libre
    free_bonus = State()         # Pregunta bonus activa
```

### 5. Modelo de Datos

No se requieren nuevos modelos. Se usa:
- `GameRecord.game_type` existente (extendido con nuevos valores)
- `BesitoService` para verificación de balance y débito
- `TriviaPromotionConfig` existente para promo mode

---

## UI / Templates

### Menú de Selección de Modo

```python
TRIVIA_MENU_TEMPLATE = {
    'title': "❓ El Examen de Diana",
    'promo_button': "🎫 Trivia con Descuento",
    'promo_subtitle': "Completa rachas para ganar descuentos",
    'free_button': "🎁 Trivia Libre",
    'free_subtitle': "Acumula besitos para futuras defensas",
    'footer': "Elija su camino, visitante..."
}
```

### Pregunta Bonus (Modo Libre)

```python
FREE_BONUS_TEMPLATE = {
    'header': "🎰 PREGUNTA BONO 🎰",
    'body': "+5 besitos asegurados\nSi aciertas: DOBLE (+10 total)\nSi fallas: 0 extra",
    'correct': "🎰 ¡BONO DOBLADO! +10 besitos 💋💋",
    'incorrect': "Sin bonus esta vez... pero los 1 besito base son tuyos."
}
```

### Protección Ofrecida (Modo Promo)

```python
PROTECTION_OFFER_TEMPLATE = {
    'header': "🎩 Lucien observa su tropiezo con calma...",
    'body': "El velo de protección le susurra:\n'Puedo salvar lo que ha construido.\n Pero el precio debe pagarse.'",
    'protect_button': "🛡️ PROTEGER",
    'protect_cost': "-{cost} besitos",
    'decline_button': "❌ CONTINUAR SIN PROTECCIÓN",
    'decline_warning': "Perderá su descuento y racha",
    'balance_note': "Besitos disponibles: {balance}"
}
```

---

## Decisiones Confirmadas

| # | Decisión | Valor |
|---|----------|-------|
| 1 | Costo protección | `5 + (streak // 3) * 5` |
| 2 | Límites modo libre | Free: 7, VIP: 15 |
| 3 | Límites modo promo | Free: 20, VIP: 30 |
| 4 | Preguntas bonus | Visualmente diferentes, generan adrenalina |
| 5 | Bonus VR | Reemplaza la base (no suma) |
| 6 | Duración protección | 1 pregunta |
| 7 | Protección sesión | No persiste entre sesiones |
| 8 | Payment | Solo besitos |

---

## Próximos Pasos

1. Implementar `trivia_menu` handler
2. Separar `play_trivia()` en `play_trivia_promo()` y `play_trivia_free()`
3. Implementar lógica VR de preguntas bonus en modo libre
4. Implementar sistema de protección con besitos en modo promo
5. Crear templates de UI para protección y bonus
6. Testing E2E de ambos modos

---

## Archivos a Modificar

- `services/game_service.py` — nuevos métodos, lógica separada
- `handlers/game_user_handlers.py` — nuevo handler de menú y callbacks
- `keyboards/inline_keyboards.py` — nuevos keyboards para menú, protección, bonus
- `models/models.py` — extender `game_type` enum si necesario
- `tests/integration/test_trivia_*.py` — actualizar tests para ambos modos
- `services/besito_service.py` — método para verificar y debitar para protección

---

*Documento preparado para sesión de implementación con skill lucien-gamification-implementation*