<!-- refreshed: 2026-05-07 -->
# Architecture

**Analysis Date:** 2026-05-07

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      bot.py (Entry Point)                   │
│              aiogram Dispatcher + Router Registration        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    handlers/ (25 routers)                   │
│         Event routing ONLY — no business logic, no DB        │
│   admin_handlers, vip_handlers, game_user_handlers, etc.    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      services/ (19 services)                │
│              Business logic per domain                       │
│  vip_service.py, game_service.py, leaderboard_service.py    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                       models/                                │
│              SQLAlchemy entities + database.py              │
│        models.py (all entities), database.py (session)        │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      PostgreSQL/SQLite                       │
│              SQLAlchemyJobStore (scheduler)                  │
└─────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| bot.py | Entry point, dispatcher setup, middleware, router registration | `bot.py` |
| handlers/* | Route Telegram events to ONE service only | `handlers/*.py` |
| services/* | Business logic per domain | `services/*.py` |
| models/* | SQLAlchemy entities and DB session management | `models/models.py`, `models/database.py` |
| keyboards/* | Telegram inline keyboard UI definitions | `keyboards/inline_keyboards.py` |
| config/* | Global configuration (env-based) | `config/settings.py` |
| utils/* | Helpers and Lucien's voice module | `utils/helpers.py`, `utils/lucien_voice.py` |

## Pattern Overview

**Overall:** Layered Architecture with Router-per-Domain pattern

**Key Characteristics:**
- Handlers are thin wrappers that call exactly ONE service
- Services contain all business logic
- Models handle all DB access via SQLAlchemy ORM
- No handler accesses DB directly; no service contains routing logic
- Context manager pattern for service session management: `get_service(ServiceClass)`

## Layers

**Handlers (Input Layer):**
- Purpose: Receive Telegram events (messages, callbacks, queries), route to appropriate service
- Location: `handlers/`
- Contains: 25 router files, each with aiogram `@router.callback_query()` and `@router.message()` handlers
- Depends on: services (for business logic)
- Used by: Dispatcher (via `dp.include_router()`)
- FSM States: Defined per-domain (e.g., `TriviaStreakStates`, `PackageWizardStates`)

**Services (Business Logic Layer):**
- Purpose: All business logic per domain, orchestrates models and cross-service calls
- Location: `services/`
- Contains: VIPService, GameService, LeaderboardService, BackpackService, BesitoService, etc.
- Depends on: models (for DB operations)
- Used by: handlers

**Models (Data Layer):**
- Purpose: SQLAlchemy entity definitions and database session management
- Location: `models/models.py`, `models/database.py`
- Contains: User, Channel, Subscription, Token, BesitoBalance, GameRecord, etc.
- Depends on: database driver (SQLAlchemy)
- Used by: services

**Keyboards (UI Layer):**
- Purpose: Telegram inline keyboard definitions
- Location: `keyboards/inline_keyboards.py`
- Contains: All `*_keyboard()` functions returning `InlineKeyboardMarkup`

**Config (Settings Layer):**
- Purpose: Environment-based configuration
- Location: `config/settings.py`
- Contains: bot_config with TOKEN, ADMIN_IDS, etc.

## Data Flow

### Primary Request Path (Callback Query)

1. **Telegram sends callback query** - User presses inline button
2. **Dispatcher routes to handler** (`handlers/game_user_handlers.py:38`) - `@router.callback_query(lambda c: c.data == "game_menu")`
3. **Handler calls service** (`handlers/game_user_handlers.py:42`) - `with get_service(GameService) as service: data = service.get_menu_data(user_id)`
4. **Service executes business logic** (`services/game_service.py`) - queries models, calculates results
5. **Service returns data dict** - Handler formats response
6. **Handler sends reply** - `await callback.message.edit_text(text, reply_markup=...)`
7. **Logger logs completion** - `logger.info(f"game_user_handlers - game_menu - {user_id} - shown")`

### Secondary Flow: FSM State Machine

1. **Handler receives first callback** - Triggers initial state entry
2. **FSM context stores state** - `await state.set_state(TriviaStreakStates.waiting_streak_choice)`
3. **Subsequent callbacks** - Routed based on current state
4. **Handler updates FSM** - `await state.set_state(...)` or `await state.clear()`
5. **State transitions validated** - Only valid transitions allowed

### Trivia Streak Flow

1. `game_trivia` callback → `GameService.start_trivia()` → returns question data
2. `trivia_answer` callback → `GameService.check_trivia_answer()` → returns result + streak choice
3. If streak continues → `TriviaStreakStates.streak_continue` → next question
4. If streak ends → `GameService.end_streak()` → awards besitos

### Leaderboard Query Flow

1. `leaderboard_menu` callback → `LeaderboardService.get_top_users()` → returns ranked list
2. User can view specific rank → `LeaderboardService.get_user_rank()` → returns position
3. View surrounding users → `LeaderboardService.get_user_position_around()` → returns context

### Backpack Inventory Flow

1. `backpack_menu` callback → `BackpackService.get_backpack_summary()` → returns counts
2. View rewards tab → `BackpackService.get_user_rewards()` → returns reward history
3. View purchases tab → `BackpackService.get_user_purchases()` → returns order history
4. View VIP tab → `BackpackService.get_user_vip_subscriptions()` → returns active subs
5. Claim package → `BackpackService.deliver_package_content()` → sends files via bot

**State Management:**
- **FSM**: aiogram Finite State Machine with RedisStorage (prod) or MemoryStorage (dev)
- **Session**: `get_service(ServiceClass)` context manager handles DB session lifecycle
- **Scheduler**: APScheduler with SQLAlchemyJobStore (jobs persist in DB across restarts)

## Key Abstractions

**get_service Context Manager:**
- Purpose: Automatic session creation/cleanup for services
- Examples: `services/__init__.py:37-69`
- Pattern: `with get_service(VIPService) as service: ...`
- Session is created on enter, closed on exit

**Service Context Manager:**
- Purpose: Per-service session management when service is instantiated directly
- Examples: `services/vip_service.py`, `services/game_service.py`
- Pattern: `_ServiceContext(service_class, db)` with `__enter__`/`__exit__`

**Router Pattern:**
- Purpose: Group handlers by domain
- Examples: `game_user_router`, `backpack_router`, `leaderboard_handlers`
- Pattern: Each handler file exports a `router` instance

**FSM States Group:**
- Purpose: Multi-step conversation flows
- Examples: `TriviaStreakStates`, `PackageWizardStates`
- Pattern: Class inheriting from `StatesGroup` with `State()` members

## Entry Points

**Main Entry:**
- Location: `bot.py:227-312`
- Triggers: `python bot.py` or `if __name__ == "__main__": asyncio.run(main())`
- Responsibilities: Validate config, create bot, setup storage, register routers, register startup/shutdown hooks, start polling

**Startup Sequence:**
1. `init_db()` - Initialize SQLAlchemy
2. `check_expired_subscriptions_on_startup()` - Process offline expirations
3. `scheduler.start()` - Start APScheduler
4. `_sync_question_sets()` - Sync trivia questions
5. Notify admins via Telegram

**Shutdown Sequence:**
1. `scheduler.stop()` - Stop APScheduler gracefully
2. Notify admins via Telegram

## Architectural Constraints

- **Threading:** Single-threaded event loop (aiogram asyncio). Scheduler uses thread pool for job execution.
- **Global state:** Module-level `_active_question_set_path` in GameService. Module-level Redis client in RedisStorage.
- **Circular imports:** Services import models, handlers import services. No circular handler↔service or service↔model.
- **FSM persistence:** RedisStorage when `REDIS_URL` set, MemoryStorage otherwise. FSM state survives restarts only with Redis.
- **Scheduler persistence:** SQLAlchemyJobStore persists jobs across restarts regardless of FSM storage choice.

## Anti-Patterns

### Logic in Handlers

**What happens:** Business logic directly in handler callbacks
**Why it's wrong:** Violates separation of concerns; makes testing and reuse difficult
**Do this instead:** Create a service method and call it: `services/game_service.py:42`

### Direct DB Access in Handlers

**What happens:** Handler imports models and queries database
**Why it's wrong:** Handlers should only route events; DB access belongs in services
**Do this instead:** `with get_service(GameService) as service: service.play_dice_game(user_id)`

### Service Duplication

**What happens:** Similar logic scattered across multiple services
**Why it's wrong:** Breaks domain ownership; leads to inconsistencies
**Do this instead:** Each domain has ONE authoritative service (e.g., BackpackService owns backpack/inventory logic)

## Error Handling

**Strategy:** Layered error handling with logging at each boundary

**Patterns:**
- Handler-level: try/except around service calls, `callback.answer()` for errors
- Service-level: Logging with structured format, return error tuples or raise domain exceptions
- Model-level: SQLAlchemy transaction rollback on exceptions

## Cross-Cutting Concerns

**Logging:** Structured logging with `logging.getLogger(__name__)` per module
- Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- Every handler action logs: `logger.info(f"handler_file - function_name - {user_id} - result")`

**Validation:**
- Telegram callback data always validated before processing
- FSM state transitions validated by aiogram
- Admin actions verified with `is_admin()` checks

**Authentication:**
- Admin ID check via `bot_config.ADMIN_IDS`
- FSM prevents unauthorized state transitions

**Rate Limiting:**
- `ThrottlingMiddleware` with `aiolimiter`
- Admin bypass available

---

*Architecture analysis: 2026-05-07*