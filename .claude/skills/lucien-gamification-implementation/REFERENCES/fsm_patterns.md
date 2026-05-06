# FSM Patterns para Aiogram 3.x

## Concepto

FSM (Finite State Machine) en Aiogram 3 gestiona flujos multi-step: el usuario avanza por estados como "elegir opción" → "confirmar" → "completado".

---

## StatesGroup y State

```python
from aiogram.fsm.state import State, StatesGroup

class TriviaStates(StatesGroup):
    selecting_difficulty = State()
    answering = State()
    showing_result = State()
    claiming_reward = State()
```

Cada `State()` puede tener un estado único o ser parte de un `StatesGroup`.

---

## Establecer Estado

```python
from aiogram.fsm.context import FSMContext

# Estado simple
await state.set_state(TriviaStates.answering)

# Con datos iniciales
await state.update_data(
    question_id=42,
    difficulty="hard",
    start_time=datetime.utcnow()
)
```

---

## Obtener y Limpiar Datos

```python
# Obtener todos los datos
data = await state.get_data()
question_id = data.get("question_id")

# Obtener estado actual
current_state = await state.get_state()
# Retorna: "TriviaStates:answering"

# Limpiar todo
await state.clear()

# Actualizar datos parciales
await state.update_data(progress=5)  # Merge con datos existentes
```

---

## Transiciones Típicas

### Flujo Lineal (forward only)

```python
@router.callback_query(F.data == "trivia:start", TriviaStates.selecting_difficulty)
async def start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TriviaStates.answering)
    await callback.message.edit_text("Elige dificultad:", reply_markup=...)

@router.callback_query(F.data.startswith("trivia:answer:"), TriviaStates.answering)
async def answer(callback: CallbackQuery, state: FSMContext):
    # Procesar respuesta
    await state.set_state(TriviaStates.showing_result)
    await show_result(callback, state)
```

### Con Volver Atrás

```python
# Guardar estado previo
async def navigate_to(state: FSMContext, new_state: State, prev_state: State = None):
    current = await state.get_state()
    data = await state.get_data()
    if prev_state is None:
        prev_state = current
    await state.update_data(previous_state=prev_state)
    await state.set_state(new_state)

@router.callback_query(F.data == "back", lambda cb: True)
async def go_back(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    prev = data.get("previous_state")
    if prev:
        await state.set_state(prev)
        # Re-render previous view
```

### Cancelación Global

```python
@router.message(F.text.in_(["Cancelar", "/cancel"]))
async def cancel(message: Message, state: FSMContext):
    current = await state.get_state()
    if current:
        await state.clear()
        await message.answer("Operación cancelada. Volviendo al menú principal.")
    else:
        await message.answer("No hay operación activa.")
```

---

## Filtrar por Estado + Callback Data

```python
# Solo responde si está en TriviaStates.answering Y el callback empieza con "trivia:answer:"
@router.callback_query(
    TriviaStates.answering,
    F.data.startswith("trivia:answer:")
)
async def process_answer(callback: CallbackQuery, state: FSMContext):
    answer_idx = int(callback.data.split(":")[-1])
    # Procesar...
```

---

## TTL (Time To Live) para Estados

Para evitar estados huérfanos (usuario abre un wizard y lo abandona):

### Opción 1: Redis TTL

RedisStorage expira keys automáticamente si está configurado:

```python
# En bot.py
from aiogram.fsm.storage.redis import RedisStorage

redis = RedisStorage.from_url(REDIS_URL, state_ttl=3600)  # 1 hora TTL
```

### Opción 2: Cleaner Job con APScheduler

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

async def clean_stale_states():
    """Periodic job para limpiar estados > 2 horas"""
    # Implementar limpieza de estados huérfanos en Redis
    pass

scheduler = AsyncIOScheduler()
scheduler.add_job(clean_stale_states, "interval", hours=2)
```

---

## Anti-Patrones FSM

| Anti-Patrón | Problema | Alternativa |
|------------|---------|-------------|
| Estado sin timeout | Estados huérfanos si usuario abandona | TTL + cleaner job |
| Demasiados estados | Código spaghetti | Simplificar, usar callbacks sin estado |
| No limpiar al completar | Memoria leaks en Redis | `await state.clear()` siempre al terminar |
| Saltos de estado sin guarda | Lógica inconsistente | Validar precondiciones antes de set_state |
