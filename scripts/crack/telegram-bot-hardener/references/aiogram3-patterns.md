# aiogram 3 — Patrones avanzados

Referencia rápida de patrones específicos de aiogram 3 para bots robustos.

---

## Router modular con inyección de dependencias

```python
# bot/main.py
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage  # o MemoryStorage para dev

from repositories.points_repository import PointsRepository
from services.gamification_service import GamificationService
from services.narrative_service import NarrativeService
from services.channel_admin_service import ChannelAdminService
from handlers.gamification import create_gamification_router
from handlers.narrative import create_narrative_router
from handlers.channel_admin import create_channel_admin_router
from middlewares.error_handler import ErrorHandlerMiddleware
from middlewares.rate_limiter import RateLimiterMiddleware
from core.event_bus import event_bus

async def main():
    bot = Bot(token=TOKEN)
    storage = RedisStorage.from_url("redis://localhost") if PROD else MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Repositorios
    points_repo = PointsRepository(db_path=DB_PATH)

    # Servicios (lógica de negocio)
    gamification_svc = GamificationService(repo=points_repo, event_bus=event_bus)
    narrative_svc = NarrativeService(repo=points_repo, event_bus=event_bus)
    channel_admin_svc = ChannelAdminService(bot=bot, vip_id=VIP_CHANNEL_ID, free_id=FREE_CHANNEL_ID)

    # Registrar suscriptores de eventos
    event_bus.on("points_earned")(narrative_svc.check_narrative_unlock)
    event_bus.on("vip_expired")(channel_admin_svc.revoke_vip_access)

    # Middlewares globales
    dp.update.middleware(ErrorHandlerMiddleware())
    dp.message.middleware(RateLimiterMiddleware(limit_seconds=1.0))

    # Routers con dependencias inyectadas
    dp.include_router(create_gamification_router(gamification_svc))
    dp.include_router(create_narrative_router(narrative_svc))
    dp.include_router(create_channel_admin_router(channel_admin_svc))

    await dp.start_polling(bot)
```

---

## FSM Storage en Redis para producción

En producción, el estado FSM DEBE persistirse en Redis, no en memoria.
Si el bot se reinicia, los usuarios no pierden su progreso en la narrativa.

```python
# Para desarrollo
from aiogram.fsm.storage.memory import MemoryStorage
storage = MemoryStorage()

# Para producción
from aiogram.fsm.storage.redis import RedisStorage
storage = RedisStorage.from_url(
    "redis://localhost:6379",
    key_builder=DefaultKeyBuilder(with_bot_id=True)
)
```

---

## Throttling con aiogram-throttle (alternativa a middleware manual)

```bash
pip install aiogram-throttle
```

```python
from aiogram_throttle import ThrottlingMiddleware
dp.message.middleware(ThrottlingMiddleware(throttling_rate_limit=1, silence_cooldown=30))
```

---

## Protección de callbacks con TTL

Para callbacks en mensajes viejos (botones que ya no deberían funcionar):

```python
import time

@router.callback_query(F.data.startswith("game_"))
async def handle_game_callback(callback: CallbackQuery):
    # Verificar que el mensaje no es muy viejo (ej: botones de >24h)
    message_age = time.time() - callback.message.date.timestamp()
    if message_age > 86400:  # 24 horas
        await callback.answer("⏰ Este botón ya expiró.", show_alert=True)
        return
    # ... lógica normal ...
```

---

## Logging estructurado con contexto de usuario

```python
# core/logging.py
import logging
import json
from typing import Any

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def _log(self, level: str, message: str, **context):
        extra = json.dumps(context, default=str) if context else ""
        getattr(self.logger, level)(f"{message} | {extra}" if extra else message)

    def info(self, msg: str, **ctx): self._log("info", msg, **ctx)
    def warning(self, msg: str, **ctx): self._log("warning", msg, **ctx)
    def error(self, msg: str, **ctx): self._log("error", msg, **ctx)

# Uso
logger = StructuredLogger(__name__)
logger.info("Puntos otorgados", user_id=1001, amount=50, action="minigame_win")
# Output: Puntos otorgados | {"user_id": 1001, "amount": 50, "action": "minigame_win"}
```

---

## Health check endpoint (para monitoreo)

```python
# health.py — endpoint simple con aiohttp
from aiohttp import web

async def health_handler(request):
    try:
        # Verificar bot
        bot_info = await bot.get_me()
        # Verificar DB
        user_count = await repo.count_users()
        return web.json_response({
            "status": "ok",
            "bot": bot_info.username,
            "users": user_count,
        })
    except Exception as e:
        return web.json_response({"status": "error", "detail": str(e)}, status=500)

app = web.Application()
app.router.add_get("/health", health_handler)
```

---

## Patrón para minijuegos aislados

Cada minijuego debe ser completamente independiente del sistema de narrativa y gamificación.
Solo se comunica vía Event Bus al terminar.

```python
# minigames/word_game.py
from aiogram import Router
from aiogram.fsm.state import State, StatesGroup
from core.event_bus import EventBus

class WordGameStates(StatesGroup):
    waiting_for_answer = State()
    game_over = State()

def create_word_game_router(event_bus: EventBus) -> Router:
    router = Router()

    @router.callback_query(F.data == "start_word_game")
    async def start_game(callback: CallbackQuery, state: FSMContext):
        await state.set_state(WordGameStates.waiting_for_answer)
        await state.update_data(question="¿Capital de Francia?", answer="Paris", attempts=3)
        await callback.message.answer("🎮 ¿Cuál es la capital de Francia?")
        await callback.answer()

    @router.message(WordGameStates.waiting_for_answer)
    async def check_answer(message: Message, state: FSMContext):
        data = await state.get_data()
        if message.text.strip().lower() == data["answer"].lower():
            await state.set_state(WordGameStates.game_over)
            await message.answer("✅ ¡Correcto!")
            # Notificar resultado — gamificación decide cuántos puntos dar
            await event_bus.emit(
                "minigame_completed",
                user_id=message.from_user.id,
                game="word_game",
                result="win",
            )
        else:
            attempts_left = data["attempts"] - 1
            if attempts_left <= 0:
                await state.clear()
                await message.answer("❌ Sin intentos. Juego terminado.")
                await event_bus.emit(
                    "minigame_completed",
                    user_id=message.from_user.id,
                    game="word_game",
                    result="lose",
                )
            else:
                await state.update_data(attempts=attempts_left)
                await message.answer(f"❌ Incorrecto. {attempts_left} intentos restantes.")

    return router
```
