# Testing Patterns

**Analysis Date:** 2026-05-07

## Test Framework

**Runner:**
- `pytest==8.1.1` with `pytest-asyncio==0.23.5` and `pytest-cov==5.0.0`
- Configured in `pyproject.toml`

**Assertion Library:**
- pytest built-in assertions with `unittest.mock.MagicMock` and `unittest.mock.AsyncMock`

**Run Commands:**
```bash
pytest                     # Run all tests
pytest -m unit            # Unit tests only
pytest -m integration     # Integration tests only
pytest -m e2e             # E2E tests only
pytest --cov=services --cov=models --cov=handlers  # Coverage for specific packages
pytest --cov-report=html:.coverage_html  # HTML coverage report
pytest --cov-fail-under=70  # Fail if coverage below 70%
```

## Test File Organization

**Location:**
- `tests/` - Root test directory
- `tests/unit/` - Unit tests
- `tests/integration/` - Integration tests
- `tests/e2e/` - End-to-end tests

**Naming:**
- Pattern: `test_{service_name}.py` or `test_{feature}.py`
- Examples: `test_besito_service.py`, `test_vip_flow.py`, `test_trivia_messages.py`

**Structure:**
```
tests/
├── conftest.py           # Shared fixtures
├── unit/
│   ├── test_alembic_heads.py
│   └── test_cross_service_atomicity.py
├── integration/
│   ├── test_besito_service.py
│   ├── test_vip_service.py
│   ├── test_store_service.py
│   └── ... (20+ service tests)
└── e2e/
    ├── test_trivia_messages.py
    └── test_lucien_voice.py
```

## Test Configuration

**pytest.ini_options in pyproject.toml:**
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--verbose",
    "--cov=services",
    "--cov=models",
    "--cov=handlers",
    "--cov-report=term-missing",
    "--cov-report=html:.coverage_html",
    "--cov-fail-under=70"
]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "slow: Slow tests",
    "e2e: E2E tests"
]
```

## Fixtures (conftest.py)

**Database Fixtures:**
```python
@pytest.fixture
def engine():
    """Creates SQLite in-memory engine for tests (function scope for isolation)."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture
def db_session(engine):
    """Creates clean DB session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()
```

**Model Fixtures:**
```python
@pytest.fixture
def sample_user(db_session: Session):
    user = User(
        telegram_id=123456789,
        username="testuser",
        first_name="Test",
        last_name="User",
        role=UserRole.USER
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def sample_admin(db_session: Session):
    user = User(
        telegram_id=987654321,
        username="adminuser",
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

# Fixtures for: sample_vip_channel, sample_free_channel, sample_tariff,
# sample_token, sample_used_token, sample_expired_token, sample_subscription,
# sample_expired_subscription, sample_balance, sample_mission, sample_mission_progress,
# sample_pending_request, sample_package, sample_store_product, sample_promotion,
# sample_reaction_emoji, sample_broadcast_message, sample_story_node, sample_story_choice,
# sample_archetype, sample_daily_gift_config, sample_cart_item, sample_order, sample_reward_besitos
```

**Mock Fixtures:**
```python
@pytest.fixture
def mock_bot():
    """Creates a mock of the Telegram bot."""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    bot.send_photo = AsyncMock()
    bot.send_video = AsyncMock()
    bot.send_animation = AsyncMock()
    bot.send_document = AsyncMock()
    bot.send_media_group = AsyncMock()
    bot.ban_chat_member = AsyncMock()
    bot.unban_chat_member = AsyncMock()
    bot.create_chat_invite_link = AsyncMock(
        return_value=MagicMock(invite_link="https://t.me/+NewInviteLink")
    )
    return bot

@pytest.fixture
def mock_dispatcher():
    """Creates a mock of the dispatcher."""
    dp = MagicMock()
    return dp
```

## Test Structure

**Integration Test Pattern (service tests):**
```python
# tests/integration/test_besito_service.py
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from models.models import User, UserRole, BesitoBalance, BesitoTransaction, TransactionSource
from services.besito_service import BesitoService


class TestBesitoService:
    """Tests for BesitoService."""

    @pytest.fixture
    def service(self, db_session: Session):
        """Create service with test DB session."""
        return BesitoService(db=db_session)

    def test_get_or_create_balance_creates_new(self, service, sample_user):
        """Test that new balance is created for user without balance."""
        balance = service.get_or_create_balance(sample_user.telegram_id)
        assert balance.user_id == sample_user.id
        assert balance.balance == 0

    def test_credit_besitos_increases_balance(self, service, sample_user, sample_balance):
        """Test that crediting increases user balance."""
        initial = sample_balance.balance
        result = service.credit_besitos(
            sample_user.telegram_id,
            100,
            TransactionSource.ADMIN,
            "Test credit"
        )
        assert result is True
        # Verify by getting balance again
        new_balance = service.get_balance(sample_user.telegram_id)
        assert new_balance == initial + 100

    def test_debit_besitos_fails_with_insufficient_balance(self, service, sample_user, sample_balance):
        """Test that debiting fails when balance is insufficient."""
        result = service.debit_besitos(
            sample_user.telegram_id,
            sample_balance.balance + 1,
            "Test debit"
        )
        assert result is False
```

**Unit Test Pattern:**
```python
# tests/unit/test_alembic_heads.py
import pytest

def test_alembic_heads_are_sequential():
    """Test that alembic migration chain is intact."""
    # Implementation checks migration chain
    ...

def test_no_duplicate_migrations():
    """Test that no duplicate migrations exist."""
    ...
```

**E2E Test Pattern:**
```python
# tests/e2e/test_trivia_messages.py
import pytest
from services.game_service import GameService


class TestStreakTemplates:
    """Test that STREAK_TEMPLATES and helper methods are properly implemented."""

    @pytest.fixture
    def service(self):
        return GameService()

    def test_streak_templates_exist(self, service):
        """Verify all STREAK_TEMPLATES keys exist"""
        required_keys = [
            'entry_header', 'entry_promotion_bar', 'entry_promotion_progress',
            ...
        ]
        for key in required_keys:
            assert key in service.STREAK_TEMPLATES, f"Missing template: {key}"

    def test_templates_have_variations(self, service):
        """Verify each template has at least 2 variations"""
        for key, template_list in service.STREAK_TEMPLATES.items():
            assert isinstance(template_list, list)
            assert len(template_list) >= 2, f"{key} should have at least 2 variations"
```

## Mocking

**Framework:** `unittest.mock` (MagicMock, AsyncMock, patch)

**Patterns:**

1. **AsyncMock for async methods:**
```python
mock_bot = AsyncMock()
mock_bot.send_message = AsyncMock(return_value=None)
```

2. **MagicMock for sync methods:**
```python
mock_dispatcher = MagicMock()
```

3. **Mock return values:**
```python
mock_bot.create_chat_invite_link = AsyncMock(
    return_value=MagicMock(invite_link="https://t.me/+NewInviteLink")
)
```

4. **Patching services:**
```python
with patch('services.besito_service.BesitoService') as mock:
    mock.get_balance.return_value = 100
    ...
```

## What to Mock

**Do mock:**
- External services (Telegram API)
- Database sessions (via fixtures)
- Time-dependent logic (freeze with freezegun if needed)
- Randomness (patch random)

**Do NOT mock:**
- The service under test
- Model classes directly (use real models with in-memory DB)
- Database in integration tests (use `db_session` fixture)

## Test Data

**Factory pattern via fixtures:**
- `sample_user`, `sample_admin` - User creation
- `sample_vip_channel`, `sample_free_channel` - Channel creation
- `sample_tariff`, `sample_token`, `sample_subscription` - VIP domain
- `sample_balance`, `sample_mission`, `sample_mission_progress` - Gamification
- `sample_store_product`, `sample_package`, `sample_promotion` - Store domain
- `sample_reaction_emoji`, `sample_broadcast_message` - Broadcast domain

**Fixture reuse:** Fixtures can depend on other fixtures:
```python
@pytest.fixture
def sample_token(db_session: Session, sample_tariff):
    """Creates test token using sample_tariff fixture."""
    token = Token(
        token_code="TEST123456",
        tariff_id=sample_tariff.id,
        status=TokenStatus.ACTIVE
    )
    ...
    return token

@pytest.fixture
def sample_subscription(db_session: Session, sample_user, sample_vip_channel, sample_token):
    """Creates test subscription using multiple fixtures."""
    subscription = Subscription(
        user_id=sample_user.id,
        channel_id=sample_vip_channel.id,
        token_id=sample_token.id,
        ...
    )
    ...
    return subscription
```

## Coverage

**Requirements:** `--cov-fail-under=70` enforced in CI

**Coverage targets:**
- `services/` - Primary coverage target
- `models/` - ORM model coverage
- `handlers/` - Handler routing coverage

**Omits:**
```
"*/tests/*",
"*/test_*",
"*/__pycache__/*",
"*/venv/*",
"*/.venv/*"
```

**Report lines excluded:**
- `pragma: no cover`
- `def __repr__`
- `raise AssertionError`
- `raise NotImplementedError`
- `if __name__ == .__main__.:`
- `if TYPE_CHECKING:`

## Test Types

**Unit Tests:**
- Tests isolated components in `tests/unit/`
- Fast, no I/O
- Used for utilities, pure functions

**Integration Tests:**
- Tests service with real DB (SQLite in-memory)
- File pattern: `test_{service_name}.py`
- 20+ tests covering: besito_service, broadcast_service, channel_service, daily_gift_service, mission_service, package_service, promotion_service, reward_service, store_service, story_service, vip_service, scheduler, rate_limit_middleware, etc.

**E2E Tests:**
- High-level smoke tests
- Test complete flows and templates
- Files: `test_lucien_voice.py`, `test_trivia_messages.py`

## Common Patterns

**Async Testing:**
```python
# tests/integration/test_trivia_stats_service.py
class TestTriviaStatsService:
    @pytest.fixture
    def service(self, db_session: Session):
        return TriviaStatsService(db=db_session)

    @pytest.mark.asyncio
    async def test_async_trivia_stats(self, service, sample_user):
        # For true async tests
        ...
```

**Error Testing:**
```python
def test_service_raises_on_invalid_input(self, service, sample_user):
    """Test that service raises ValueError for invalid input."""
    with pytest.raises(ValueError, match="Tarifa no encontrada"):
        service.generate_token(invalid_tariff_id)
```

**Fixture isolation:**
- Each test gets fresh `db_session` via transaction rollback
- No test affects another
- `engine` fixture uses function scope

---

*Testing analysis: 2026-05-07*