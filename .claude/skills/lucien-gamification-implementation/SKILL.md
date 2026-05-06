---
name: lucien-gamification-implementation
description: >
  Implementación técnica de sistemas gamificados en LucienBot. Úsala cuando el usuario
  quiera implementar rachas, daily rewards, quests, leaderboards, escribir flujos FSM,
  crear services de gamificación o diseñar UI con inline keyboards.
  Conoce los servicios existentes y patrones de arquitectura del bot.
  Consulta lucien-gamification-design para entender el propósito de cada feature
  antes de implementar.
---

# Gamification Implementation Skill

Esta skill traduce diseños gamificados en código funcional. El foco está en **cómo** implementar: FSM, servicios, handlers, UI.

**Antes de implementar, consultar `lucien-gamification-design` para entender el propósito y qué impulso Octalysis cubre.**

---

## Arquitectura: Handlers → Services → Models

```
handlers/ → services/ → models/ → database
```

**Reglas críticas (non-negotiable)**:
- Handlers: Solo enrutan eventos. SIN lógica de negocio. SIN acceso a DB.
- Services: Toda la lógica de negocio. Acceden a DB vía models.
- Un handler = una service (no mezclr lógica de múltiples servicios en un handler)

---

## FSM (Finite State Machine)

### Estructura Base

```python
from aiogram.fsm.state import State, StatesGroup

class GameFlow(StatesGroup):
    menu = State()
    quest_active = State()
    quest_completed = State()
    reward_claim = State()
```

### Transiciones

```python
# Establecer estado
await state.set_state(GameFlow.quest_active)

# Guardar datos intermedios
await state.update_data(quest_id=42, progress=3)

# Obtener datos
data = await state.get_data()
quest_id = data['quest_id']

# Limpiar estado
await state.clear()
```

### Patrones de Cancelación

```python
# Cancelación global desde cualquier estado
@router.message(F.text == "Cancelar")
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Operación cancelada.")
```

### TTL en Estados

Para evitar estados huérfanos (usuario abandona a mitad):

```python
# Configurar TTL al set_state
from aiogram.fsm.context import FSMContext

async def set_state_with_ttl(state: FSMContext, state_obj: State, ttl_seconds: int = 3600):
    await state.set_state(state_obj)
    # El estado expira automáticamente (RedisStorage TTL o cleaner job)
```

---

## Service Patterns para Gamificación

### Estructura Base

```python
class GamificationService:
    def __init__(self):
        self.session = Session()

    def close(self):
        self.session.close()

    # Context manager para cleanup automático
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        self.close()
```

### Usar context manager

```python
from services import get_service

with get_service(GamificationService) as service:
    result = service.process_streak(user_id)
```

### Método con Transacción (para crédito/débito)

```python
async def credit_besitos(self, user_id: int, amount: int, source: str, description: str):
    with self.session.begin():
        balance = self.session.query(BesitoBalance).filter_by(user_id=user_id).with_for_update().first()
        balance.balance += amount
        # Log transaction
        tx = BesitoTransaction(user_id=user_id, amount=amount, source=source, description=description)
        self.session.add(tx)
    return balance.balance
```

---

## Handler Patterns

### Thin Handler (correcto)

```python
@router.callback_query(F.data == "game:play")
async def play_game(callback: CallbackQuery, service: GameService = Depends(get_game_service)):
    user_id = callback.from_user.id
    result = service.play_game(user_id)
    await callback.message.edit_text(f"Resultado: {result}")
    await callback.answer()
```

**PROHIBIDO en handlers**:
- No hacer queries a DB directamente
- No crear lógica de negocio
- No calcular balances o probabilidades

### Callback Data (64-byte limit)

**Convención obligatoria**: `accion:entidad:id:modificador`

```
quest:accept:42        → Aceptar quest 42
game:roll:dice         → Lanzar dado
streak:claim:daily     → Reclamar racha diaria
nav:back:menu_main    → Volver al menú principal
```

**PROHIBIDO**: `callback_data` > 64 bytes. Telegram rechaza silenciosamente.

### Always call query.answer()

```python
@router.callback_query(F.data == "game:play")
async def play_game(callback: CallbackQuery):
    # Procesar...
    await callback.answer("🎲 ¡Dado lanzado!", show_alert=True)
```

Sin `callback.answer()`, el usuario ve un spinner de 30 segundos.

---

## UI Patterns: Inline Keyboards

### Barra de Progreso

```python
def level_progress_bar(current_xp: int, xp_to_next: int, length: int = 10) -> str:
    filled = int((current_xp / xp_to_next) * length)
    return "█" * filled + "░" * (length - filled)
```

### Menú Gamificado

```python
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🎮 Jugar Dados", callback_data="game:roll:dice")],
    [InlineKeyboardButton(text="🧩 Trivia", callback_data="game:trivia:start")],
    [InlineKeyboardButton(text="🔥 Mi Racha", callback_data="streak:status")],
    [InlineKeyboardButton(text="📊 Leaderboard", callback_data="nav:leaderboard")],
    [InlineKeyboardButton(text="🎁 Regalo Diario", callback_data="daily:claim")],
])
```

### Reglas de UX

- Emoji al inicio del label: "📊 Stats" > "View Statistics"
- Máximo 3-4 botones por fila en móviles
- Acciones destructivas en fila propia, al final
- Usar `editMessageReplyMarkup` para actualizar estado visual (no enviar nuevo mensaje)

---

## VR (Variable Ratio) Implementation

**Patrón para recompensas sorpresa** (referencia: `lucien-gamification-design/REFERENCES/reinforcement.md`):

```python
import random
from aiogram.fsm.context import FSMContext

async def handle_interaction(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    interactions_since_reward = data.get("interactions_since_reward", 0)

    # Probabilidad acumulativa
    base_chance = 0.05
    accumulated_chance = min(base_chance + (interactions_since_reward * 0.03), 0.35)

    if random.random() < accumulated_chance:
        reward = generate_surprise_reward(tier=1)  # +5 a +20 besitos
        await callback.message.answer(f"🎉 ¡Sorpresa! +{reward} besitos")
        await state.update_data(interactions_since_reward=0)
        await log_reward(callback.from_user.id, reward)
    else:
        await state.update_data(interactions_since_reward=interactions_since_reward + 1)
    await callback.answer()
```

**Límites éticos VR**:
- Máximo 3 VR rewards por día por usuario
- Probabilidad máxima 35%
- Nunca VR para transacciones monetarias reales

---

## Cross-Reference: Para Qué Sirve Lo Que Implementas

| Lo que implementas | Qué impulso Octalysis cubre | Véase |
|-------------------|---------------------------|-------|
| Barra de progreso nivel | #2 Desarrollo y Logro | `lucien-gamification-design` |
| Sistema de besitos | #4 Posesión y Propiedad | `lucien-gamification-design` |
| Racha diaria | #8 Pérdida y Evitación | `lucien-gamification-design` |
| VR surprise rewards | #7 Impredictibilidad | `lucien-gamification-design` |
| Leaderboards | #5 Influencia Social | `lucien-gamification-design` |

---

## Recursos de Referencia

| Archivo | Contenido |
|---------|-----------|
| `REFERENCES/fsm_patterns.md` | Patrones FSM completos con ejemplos del codebase |
| `REFERENCES/service_patterns.md` | Cómo crear/modificar servicios de gamificación |
| `REFERENCES/ui_patterns.md` | Templates de inline keyboards, progress bars |
| `REFERENCES/existing_services.md` | Servicios gamificación existentes y sus métodos |
