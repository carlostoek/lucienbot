# Architecture Patterns — aiogram 3 Bot

Implementaciones listas para usar en bots de Telegram con Python + aiogram 3.

---

## 1. Service Layer

El patrón más impactante. Separa el "qué hace el bot" del "cómo responde Telegram".

### Estructura de archivos

```
bot/
├── handlers/
│   └── gamification.py      # Solo recibe update → valida → llama servicio → responde
├── services/
│   └── gamification_service.py  # Lógica pura, sin aiogram, 100% testeable
├── repositories/
│   └── points_repository.py     # Solo SQL/queries, sin lógica
└── models/
    └── user.py                  # Dataclasses o Pydantic models
```

### Implementación

```python
# models/user.py
from dataclasses import dataclass

@dataclass
class UserPoints:
    user_id: int
    points: int
    level: int

# repositories/points_repository.py
from typing import Optional
import aiosqlite  # o el driver que uses

class PointsRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def get(self, user_id: int) -> Optional[UserPoints]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT user_id, points, level FROM users WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return UserPoints(*row)
        return None

    async def add_points(self, user_id: int, amount: int) -> UserPoints:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET points = points + ? WHERE user_id = ?",
                (amount, user_id)
            )
            await db.commit()
        return await self.get(user_id)

# services/gamification_service.py
from repositories.points_repository import PointsRepository
from models.user import UserPoints

MAX_POINTS = 10_000
POINTS_PER_ACTION = {"minigame_win": 50, "daily_check": 10, "narrative_choice": 20}

class GamificationService:
    def __init__(self, repo: PointsRepository):
        self.repo = repo

    async def award_points(self, user_id: int, action: str) -> dict:
        """
        Retorna dict con resultado listo para responder al usuario.
        Sin aiogram, sin bot, 100% testeable.
        """
        amount = POINTS_PER_ACTION.get(action, 0)
        if amount == 0:
            return {"success": False, "reason": "unknown_action"}

        user = await self.repo.get(user_id)
        if not user:
            return {"success": False, "reason": "user_not_found"}

        if user.points + amount > MAX_POINTS:
            amount = MAX_POINTS - user.points  # cap en máximo

        updated = await self.repo.add_points(user_id, amount)
        return {
            "success": True,
            "awarded": amount,
            "total": updated.points,
            "level": updated.level,
        }

# handlers/gamification.py
from aiogram import Router
from aiogram.types import Message
from services.gamification_service import GamificationService

router = Router()

# La dependencia se inyecta al crear el router, no se importa globalmente
def create_gamification_router(service: GamificationService) -> Router:
    
    @router.message(Command("puntos"))
    async def show_points(message: Message):
        result = await service.award_points(message.from_user.id, "daily_check")
        if result["success"]:
            await message.answer(
                f"✅ +{result['awarded']} puntos\n"
                f"Total: {result['total']} | Nivel {result['level']}"
            )
        else:
            await message.answer("No se pudieron registrar los puntos.")
    
    return router
```

---

## 2. Event Bus interno

Desacopla módulos que necesitan comunicarse sin importarse mutuamente.
Especialmente útil para: gamificación → narrativa, narrativa → channel_admin.

```python
# core/event_bus.py
from collections import defaultdict
from typing import Callable, Awaitable, Any
import asyncio

class EventBus:
    def __init__(self):
        self._listeners: dict[str, list[Callable]] = defaultdict(list)

    def on(self, event: str):
        """Decorador para suscribirse a un evento."""
        def decorator(func: Callable[..., Awaitable]):
            self._listeners[event].append(func)
            return func
        return decorator

    async def emit(self, event: str, **kwargs):
        """Emite un evento a todos los suscriptores. Errores no bloquean."""
        tasks = [listener(**kwargs) for listener in self._listeners[event]]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, Exception):
                # Loggear pero no propagar — un fallo en narrativa no debe romper gamificación
                import logging
                logging.error(f"EventBus error on '{event}': {r}", exc_info=r)

# Instancia global (o inyectada vía DI)
event_bus = EventBus()

# En gamification_service.py
from core.event_bus import event_bus

async def award_points(self, user_id: int, action: str) -> dict:
    # ... lógica de puntos ...
    await event_bus.emit("points_earned", user_id=user_id, points=amount, action=action)
    return result

# En narrative_service.py
from core.event_bus import event_bus

@event_bus.on("points_earned")
async def check_narrative_unlock(user_id: int, points: int, **kwargs):
    """Se ejecuta automáticamente cuando alguien gana puntos."""
    # Verificar si desbloquea nuevo capítulo
    ...
```

---

## 3. Middleware de Error Global

Captura cualquier excepción no manejada, responde al usuario, loggea con contexto.

```python
# middlewares/error_handler.py
import logging
import traceback
from typing import Callable, Awaitable, Any
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict], Awaitable[Any]],
        event: TelegramObject,
        data: dict,
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            # Log con contexto completo
            user_id = None
            if isinstance(event, (Message, CallbackQuery)):
                user_id = event.from_user.id if event.from_user else None

            logger.error(
                f"Unhandled exception | user_id={user_id} | "
                f"event_type={type(event).__name__} | error={e}\n"
                f"{traceback.format_exc()}"
            )

            # Responder al usuario sin revelar detalles
            try:
                if isinstance(event, Message):
                    await event.answer("⚠️ Ocurrió un error. Por favor intenta de nuevo.")
                elif isinstance(event, CallbackQuery):
                    await event.answer("⚠️ Error al procesar. Intenta de nuevo.", show_alert=True)
            except Exception:
                pass  # Si la respuesta también falla, al menos no se cuelga

# Registrar en el dispatcher principal
dp.update.middleware(ErrorHandlerMiddleware())
```

---

## 4. Middleware de Rate Limiting

Protege minijuegos y comandos de spam.

```python
# middlewares/rate_limiter.py
import time
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message

class RateLimiterMiddleware(BaseMiddleware):
    def __init__(self, limit_seconds: float = 1.0):
        self.limit = limit_seconds
        self._last_call: dict[int, float] = {}

    async def __call__(self, handler, event: TelegramObject, data: dict):
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
            now = time.monotonic()
            last = self._last_call.get(user_id, 0)
            
            if now - last < self.limit:
                await event.answer("⏳ Espera un momento antes de volver a usar este comando.")
                return
            
            self._last_call[user_id] = now

        return await handler(event, data)
```

---

## 5. FSM con transiciones explícitas (para Narrativa)

Documenta y valida el grafo de estados de la historia.

```python
# narrative/states.py
from aiogram.fsm.state import State, StatesGroup
from enum import Enum

class NarrativeNode(str, Enum):
    """Todos los nodos posibles de la historia. Fuente de verdad única."""
    START = "start"
    INTRO = "intro"
    ARCHETYPE_QUIZ = "archetype_quiz"
    BRANCH_WARRIOR = "branch_warrior"
    BRANCH_SAGE = "branch_sage"
    MINIGAME_1 = "minigame_1"
    ENDING_A = "ending_a"
    ENDING_B = "ending_b"

# Grafo de transiciones válidas — documentado explícitamente
VALID_TRANSITIONS: dict[NarrativeNode, list[NarrativeNode]] = {
    NarrativeNode.START: [NarrativeNode.INTRO],
    NarrativeNode.INTRO: [NarrativeNode.ARCHETYPE_QUIZ],
    NarrativeNode.ARCHETYPE_QUIZ: [NarrativeNode.BRANCH_WARRIOR, NarrativeNode.BRANCH_SAGE],
    NarrativeNode.BRANCH_WARRIOR: [NarrativeNode.MINIGAME_1, NarrativeNode.ENDING_A],
    NarrativeNode.BRANCH_SAGE: [NarrativeNode.ENDING_B],
    NarrativeNode.MINIGAME_1: [NarrativeNode.ENDING_A],
}

class NarrativeStates(StatesGroup):
    in_story = State()

# narrative/narrative_service.py
from narrative.states import NarrativeNode, VALID_TRANSITIONS

class NarrativeService:
    async def advance(self, user_id: int, current: NarrativeNode, next_node: NarrativeNode) -> dict:
        allowed = VALID_TRANSITIONS.get(current, [])
        if next_node not in allowed:
            return {
                "success": False,
                "reason": "invalid_transition",
                "current": current,
                "attempted": next_node,
            }
        # ... guardar y avanzar ...
        return {"success": True, "node": next_node}
```

---

## 6. Idempotencia en Callbacks

Evita que Telegram ejecute el mismo callback dos veces si hay reintento.

```python
# core/idempotency.py
import time

class IdempotencyCache:
    """Cache en memoria. Para producción, usar Redis con TTL."""
    def __init__(self, ttl_seconds: int = 60):
        self._seen: dict[str, float] = {}
        self.ttl = ttl_seconds

    def is_duplicate(self, callback_id: str) -> bool:
        now = time.monotonic()
        # Limpiar expirados
        self._seen = {k: v for k, v in self._seen.items() if now - v < self.ttl}
        
        if callback_id in self._seen:
            return True
        self._seen[callback_id] = now
        return False

idempotency = IdempotencyCache()

# En handlers/gamification.py
@router.callback_query(F.data.startswith("redeem_"))
async def redeem_reward(callback: CallbackQuery):
    if idempotency.is_duplicate(callback.id):
        await callback.answer()  # Silencioso, ya fue procesado
        return
    
    # ... lógica normal ...
    await callback.answer("✅ Recompensa canjeada")
```
