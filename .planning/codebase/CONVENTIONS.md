# Coding Conventions

**Analysis Date:** 2026-05-07

## Naming Patterns

**Files:**
- Handlers: `{domain}_handlers.py` (e.g., `vip_handlers.py`, `backpack_handler.py`)
- Services: `{domain}_service.py` (e.g., `vip_service.py`, `backpack_service.py`)
- Models: `models.py` (single file for all SQLAlchemy models)
- Keyboards: `inline_keyboards.py`
- Utils: `helpers.py`, `lucien_voice.py`

**Functions:**
- Pattern: `verbo + contexto + resultado`
- Examples: `get_balance`, `credit_besitos`, `create_tariff`, `get_user_rewards`
- Private methods: `_helper_method` (single underscore prefix)

**Variables:**
- camelCase for local variables: `user_id`, `session`, `result`
- snake_case for DB columns and module-level constants: `total_earned`, `DAILY_DICE_LIMIT`
- UPPER_SNAKE_CASE for class-level constants: `STREAK_TIMEOUT_SECONDS`, `DAILY_DICE_LIMIT_FREE`

**Types:**
- Python enums for domain values: `UserRole`, `ChannelType`, `TokenStatus`
- Enums defined in `models/models.py`

## Code Style

**Formatting:**
- Tool: `ruff` (configured in `pyproject.toml`)
- Line length: 100 characters
- Indent: 4 spaces
- Quote style: double quotes

**Linting:**
- `ruff` with rules: E, W, F, I (isort), N (naming), UP (upgrade), B (bugbear), C4 (comprehensions), SIM (simplify)
- Ignore: E501 (line too long - handled by formatter), B008 (function calls in argument defaults)

**Docstrings:**
- Convention: Google style
- Use `"""docstring"""` for all public methods and classes

## Architecture Rules (MANDATORY)

### Layer Separation

```
handlers/ → services/ → models/ → database
```

**handlers/** (`/home/ubuntu/repos/lucienbot/handlers/`):
- ONLY route events from Telegram
- NO business logic, NO DB access
- Call exactly ONE service per handler
- Example: `handlers/vip_handlers.py`, `handlers/backpack_handler.py`

**services/** (`/home/ubuntu/repos/lucienbot/services/`):
- Business logic per domain
- NO direct DB access (use models)
- One service = one domain (do not fragment)
- Example: `services/vip_service.py`, `services/game_service.py`

**models/** (`/home/ubuntu/repos/lucienbot/models/`):
- SQLAlchemy entities ONLY
- DB access ONLY
- Example: `models/models.py`, `models/database.py`

**utils/** (`/home/ubuntu/repos/lucienbot/utils/`):
- Pure helper functions (no side effects)
- Voice/message templates in `lucien_voice.py`
- Example: `utils/helpers.py`

## Import Organization

**Order:**
1. Standard library: `logging`, `datetime`, `typing`
2. Third-party: `aiogram`, `sqlalchemy`, `pytest`
3. Internal modules: `models`, `services`, `handlers`, `keyboards`, `utils`, `config`
4. Relative imports within package

**Path aliases:**
- No path aliases configured; use relative imports

**Example:**
```python
# handlers/vip_handlers.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from services.vip_service import VIPService
from keyboards.inline_keyboards import tariffs_keyboard
from utils.lucien_voice import LucienVoice
```

## Service Pattern

**Context manager pattern for DB sessions:**
```python
# services/__init__.py
def get_service(service_class, db=None):
    """Creates a service with automatic session management."""
    return _ServiceContext(service_class, db)

class _ServiceContext:
    """Context manager for services with automatic session handling."""
    def __enter__(self):
        self._service = self._service_class(self._db)
        return self._service
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._service and hasattr(self._service, 'close'):
            self._service.close()
        return False

# Usage:
with get_service(VIPService) as vip_service:
    tariffs = vip_service.get_all_tariffs()
```

**Service initialization:**
```python
class VIPService:
    def __init__(self, db: Session = None):
        self.db = db
        self._owns_session = db is None  # Track if we created the session

    def _get_db(self) -> Session:
        if self.db is None:
            self.db = SessionLocal()
        return self.db

    def close(self):
        if self._owns_session and self.db:
            self.db.close()
            self.db = None
```

## Error Handling

**Strategy:**
- Use context managers for transaction rollback
- Services do NOT catch exceptions (let them propagate)
- Log all actions with: module, action, user_id, result

**Transaction pattern:**
```python
# models/database.py
@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
```

**Admin validation:**
```python
# utils/helpers.py
def is_admin(user_id: int) -> bool:
    """Verifica si un usuario es administrador"""
    return user_id in bot_config.ADMIN_IDS

# Usage in handlers:
@router.callback_query(F.data == "admin_action", lambda cb: is_admin(cb.from_user.id))
async def admin_action(callback: CallbackQuery):
    ...
```

## Logging

**Pattern:**
```python
logger = logging.getLogger(__name__)

# Every important action:
logger.info(f"{module} | {action} | user_id={user_id} | result={result}")
```

**When to log:**
- Every handler entry
- Every service method that modifies data
- Every admin action
- Every error with stack trace

## FSM (Finite State Machine)

**Handlers define StatesGroup:**
```python
# handlers/game_user_handlers.py
class TriviaStreakStates(StatesGroup):
    waiting_streak_choice = State()
    streak_continue = State()
```

**State transitions:**
```python
await state.set_state(TriviaStreakStates.waiting_promotion_type)
```

## Comments

**When to comment:**
- Complex business logic
- Non-obvious decisions
- FSM state purposes

**JSDoc/TSDoc:**
- Not used (Python project)
- Use Google-style docstrings

## Function Design

**Size limit:** Maximum 50 lines (enforced by rules.md)

**Single responsibility:**
- One function = one action
- No generic functions like `process_data` or `handle_logic`

**Parameters:**
- Type hints required for public API
- Use `Optional` for nullable parameters

## Module Design

**Exports:**
- Use `__all__` in `services/__init__.py` and similar
- Explicit public API only

**Context manager pattern:**
```python
# services/game_service.py
class GameService:
    # Class constants at top
    DAILY_DICE_LIMIT_FREE = 10
    DAILY_DICE_LIMIT_VIP = 20

    # Templates as class attributes
    MENU_TEMPLATES = {...}

    # Public methods
    def get_menu_data(self, user_id: int) -> Dict[str, Any]:
        """Get game menu data for user."""
        ...
```

## Anti-Patterns (PROHIBITED)

1. **Business logic in handlers** - Handlers must call exactly one service
2. **Direct DB access in services** - Use models, never raw SQL
3. **Duplicated logic between services** - Centralize in one service per domain
4. **Generic function names** - Use descriptive `verbo_contexto_resultado` pattern
5. **Creating sessions directly in handlers** - Use `get_service()` context manager

---

*Convention analysis: 2026-05-07*