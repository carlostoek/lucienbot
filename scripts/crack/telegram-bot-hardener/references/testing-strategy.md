# Testing Strategy — aiogram 3 Bot

Templates y estrategias de tests para bots de Telegram con pytest + pytest-asyncio.

---

## Setup

```bash
pip install pytest pytest-asyncio pytest-mock aiosqlite
```

```ini
# pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

---

## conftest.py completo

```python
# tests/conftest.py
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import User, Chat

# ─── Bot y Dispatcher ───────────────────────────────────────────

@pytest.fixture
def bot():
    mock_bot = AsyncMock(spec=Bot)
    mock_bot.id = 123456789
    mock_bot.token = "fake:token"
    mock_bot.send_message = AsyncMock(return_value=MagicMock())
    mock_bot.ban_chat_member = AsyncMock(return_value=True)
    mock_bot.unban_chat_member = AsyncMock(return_value=True)
    mock_bot.invite_chat_member = AsyncMock(return_value=MagicMock())
    return mock_bot

@pytest.fixture
def storage():
    return MemoryStorage()

@pytest.fixture
def dp(storage):
    return Dispatcher(storage=storage)

# ─── Factories de objetos Telegram ──────────────────────────────

@pytest.fixture
def make_user():
    def _factory(
        user_id: int = 1001,
        username: str = "testuser",
        first_name: str = "Test",
        is_bot: bool = False,
        is_premium: bool = False,
    ):
        user = MagicMock(spec=User)
        user.id = user_id
        user.username = username
        user.first_name = first_name
        user.is_bot = is_bot
        user.is_premium = is_premium
        user.full_name = first_name
        return user
    return _factory

@pytest.fixture
def make_message(bot, make_user):
    def _factory(text: str = "/start", user=None, chat_id: int = -1001):
        msg = AsyncMock()
        msg.bot = bot
        msg.from_user = user or make_user()
        msg.chat = MagicMock()
        msg.chat.id = chat_id
        msg.text = text
        msg.message_id = 42
        msg.answer = AsyncMock()
        msg.reply = AsyncMock()
        msg.delete = AsyncMock()
        return msg
    return _factory

@pytest.fixture
def make_callback(bot, make_user):
    def _factory(data: str = "action:test", user=None):
        cb = AsyncMock()
        cb.id = f"callback_{data}"
        cb.bot = bot
        cb.from_user = user or make_user()
        cb.data = data
        cb.message = AsyncMock()
        cb.message.answer = AsyncMock()
        cb.message.edit_text = AsyncMock()
        cb.answer = AsyncMock()
        return cb
    return _factory

@pytest.fixture
def make_fsm_context():
    """FSMContext mockeado con storage en memoria."""
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.fsm.storage.base import StorageKey
    
    storage = MemoryStorage()
    
    async def _factory(user_id: int = 1001, chat_id: int = 1001):
        key = StorageKey(bot_id=123, chat_id=chat_id, user_id=user_id)
        return FSMContext(storage=storage, key=key)
    
    return _factory

# ─── DB en memoria para tests de integración ────────────────────

@pytest_asyncio.fixture
async def test_db(tmp_path):
    """SQLite en memoria para tests, se destruye al terminar."""
    import aiosqlite
    db_path = str(tmp_path / "test.db")
    
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE users (
                user_id INTEGER PRIMARY KEY,
                points INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                archetype TEXT,
                narrative_node TEXT DEFAULT 'start'
            )
        """)
        await db.execute("""
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                action TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
    
    return db_path

@pytest_asyncio.fixture
async def seeded_db(test_db):
    """DB con usuarios de prueba ya insertados."""
    import aiosqlite
    async with aiosqlite.connect(test_db) as db:
        await db.executemany(
            "INSERT INTO users (user_id, points, level) VALUES (?, ?, ?)",
            [(1001, 100, 1), (1002, 5000, 5), (1003, 9999, 10)]
        )
        await db.commit()
    return test_db
```

---

## Tests unitarios — Gamificación

```python
# tests/unit/test_gamification_service.py
import pytest
from unittest.mock import AsyncMock
from services.gamification_service import GamificationService
from models.user import UserPoints

@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    repo.get.return_value = UserPoints(user_id=1001, points=100, level=1)
    repo.add_points.return_value = UserPoints(user_id=1001, points=150, level=1)
    return repo

@pytest.fixture
def service(mock_repo):
    return GamificationService(repo=mock_repo)


class TestAwardPoints:
    async def test_daily_check_awards_correct_points(self, service, mock_repo):
        result = await service.award_points(1001, "daily_check")
        assert result["success"] is True
        assert result["awarded"] == 10
        mock_repo.add_points.assert_called_once_with(1001, 10)

    async def test_unknown_action_returns_failure(self, service):
        result = await service.award_points(1001, "accion_inexistente")
        assert result["success"] is False
        assert result["reason"] == "unknown_action"

    async def test_points_capped_at_maximum(self, service, mock_repo):
        # Usuario cerca del límite
        mock_repo.get.return_value = UserPoints(user_id=1001, points=9990, level=10)
        mock_repo.add_points.return_value = UserPoints(user_id=1001, points=10000, level=10)
        
        result = await service.award_points(1001, "minigame_win")  # +50 normalmente
        
        assert result["success"] is True
        assert result["awarded"] == 10  # Solo 10 hasta el límite
        mock_repo.add_points.assert_called_once_with(1001, 10)

    async def test_user_not_found_returns_failure(self, service, mock_repo):
        mock_repo.get.return_value = None
        result = await service.award_points(9999, "daily_check")
        assert result["success"] is False
        assert result["reason"] == "user_not_found"


class TestRedeemReward:
    async def test_redeem_deducts_points(self, service, mock_repo):
        mock_repo.get.return_value = UserPoints(user_id=1001, points=500, level=3)
        result = await service.redeem_reward(1001, reward_cost=200)
        assert result["success"] is True
        mock_repo.add_points.assert_called_once_with(1001, -200)

    async def test_insufficient_points_rejected(self, service, mock_repo):
        mock_repo.get.return_value = UserPoints(user_id=1001, points=50, level=1)
        result = await service.redeem_reward(1001, reward_cost=200)
        assert result["success"] is False
        assert result["reason"] == "insufficient_points"
        mock_repo.add_points.assert_not_called()
```

---

## Tests unitarios — Narrativa

```python
# tests/unit/test_narrative_service.py
import pytest
from services.narrative_service import NarrativeService
from narrative.states import NarrativeNode

@pytest.fixture
def mock_repo():
    from unittest.mock import AsyncMock
    return AsyncMock()

@pytest.fixture
def service(mock_repo):
    return NarrativeService(repo=mock_repo)


class TestNarrativeAdvance:
    async def test_valid_transition_succeeds(self, service):
        result = await service.advance(
            user_id=1001,
            current=NarrativeNode.INTRO,
            next_node=NarrativeNode.ARCHETYPE_QUIZ,
        )
        assert result["success"] is True
        assert result["node"] == NarrativeNode.ARCHETYPE_QUIZ

    async def test_invalid_transition_rejected(self, service, mock_repo):
        result = await service.advance(
            user_id=1001,
            current=NarrativeNode.START,
            next_node=NarrativeNode.ENDING_A,  # No se puede saltar al final
        )
        assert result["success"] is False
        assert result["reason"] == "invalid_transition"
        mock_repo.save_node.assert_not_called()

    async def test_archetype_assigned_only_once(self, service, mock_repo):
        mock_repo.get_archetype.return_value = "warrior"  # Ya tiene arquetipo
        
        result = await service.assign_archetype(user_id=1001, archetype="sage")
        assert result["success"] is False
        assert result["reason"] == "archetype_already_assigned"


class TestNarrativeState:
    async def test_state_persists_after_advance(self, service, mock_repo):
        await service.advance(1001, NarrativeNode.INTRO, NarrativeNode.ARCHETYPE_QUIZ)
        mock_repo.save_node.assert_called_once_with(1001, NarrativeNode.ARCHETYPE_QUIZ)

    async def test_unknown_node_raises_value_error(self, service):
        with pytest.raises(ValueError, match="unknown node"):
            await service.advance(1001, NarrativeNode.INTRO, "nodo_inventado")
```

---

## Tests de integración — Flujo completo

```python
# tests/integration/test_points_flow.py
import pytest
from repositories.points_repository import PointsRepository
from services.gamification_service import GamificationService


class TestPointsFlowIntegration:
    @pytest.fixture
    async def setup(self, seeded_db):
        repo = PointsRepository(db_path=seeded_db)
        service = GamificationService(repo=repo)
        return service, repo

    async def test_earn_and_redeem_full_flow(self, setup):
        service, repo = setup
        user_id = 1001  # Inicia con 100 puntos

        # Ganar puntos
        earn_result = await service.award_points(user_id, "minigame_win")
        assert earn_result["success"] is True
        assert earn_result["total"] == 150  # 100 + 50

        # Canjear recompensa
        redeem_result = await service.redeem_reward(user_id, reward_cost=50)
        assert redeem_result["success"] is True

        # Verificar en DB
        user = await repo.get(user_id)
        assert user.points == 100  # 150 - 50

    async def test_concurrent_points_no_duplication(self, setup):
        """Verifica que dos acciones simultáneas no dupliquen puntos."""
        import asyncio
        service, repo = setup
        user_id = 1001

        results = await asyncio.gather(
            service.award_points(user_id, "daily_check"),
            service.award_points(user_id, "daily_check"),
        )

        user = await repo.get(user_id)
        # Con SQLite serializado, debe ser 120 (100 + 10 + 10), no 130 por race condition
        assert user.points <= 120
```

---

## Tests de handlers

```python
# tests/handlers/test_gamification_handlers.py
import pytest
from unittest.mock import AsyncMock
from handlers.gamification import create_gamification_router


class TestGamificationHandlers:
    @pytest.fixture
    def mock_service(self):
        svc = AsyncMock()
        svc.award_points.return_value = {
            "success": True, "awarded": 10, "total": 110, "level": 1
        }
        return svc

    async def test_puntos_command_calls_service(self, make_message, mock_service):
        router = create_gamification_router(mock_service)
        msg = make_message("/puntos")

        # Llamar el handler directamente
        from handlers.gamification import show_points
        await show_points(msg)

        mock_service.award_points.assert_called_once_with(
            msg.from_user.id, "daily_check"
        )

    async def test_puntos_command_responds_to_user(self, make_message, mock_service):
        msg = make_message("/puntos")
        from handlers.gamification import show_points
        await show_points.__wrapped__(msg)  # Llama al handler sin decoradores
        msg.answer.assert_called_once()
        assert "110" in msg.answer.call_args[0][0]

    async def test_puntos_command_handles_service_failure(self, make_message, mock_service):
        mock_service.award_points.return_value = {"success": False, "reason": "user_not_found"}
        msg = make_message("/puntos")
        from handlers.gamification import show_points
        await show_points.__wrapped__(msg)
        msg.answer.assert_called_once()
        # No debe lanzar excepción aunque el servicio falle
```

---

## Tests de Channel Admin

```python
# tests/unit/test_channel_admin_service.py
import pytest
from unittest.mock import AsyncMock

class TestChannelAdminService:
    async def test_vip_user_gets_access(self, bot):
        from services.channel_admin_service import ChannelAdminService
        service = ChannelAdminService(
            bot=bot,
            vip_channel_id=-100123,
            free_channel_id=-100456,
        )
        result = await service.grant_vip_access(user_id=1001)
        assert result["success"] is True
        bot.unban_chat_member.assert_called_with(-100123, 1001)

    async def test_expired_user_removed_gracefully(self, bot):
        """Si el usuario ya salió del canal, no debe lanzar error."""
        from aiogram.exceptions import TelegramBadRequest
        bot.ban_chat_member.side_effect = TelegramBadRequest(
            method="banChatMember", message="user not found"
        )
        from services.channel_admin_service import ChannelAdminService
        service = ChannelAdminService(bot=bot, vip_channel_id=-100123, free_channel_id=-100456)
        
        result = await service.revoke_vip_access(user_id=9999)
        assert result["success"] is True  # Fallo silencioso esperado
        assert result["note"] == "user_not_in_channel"
```
