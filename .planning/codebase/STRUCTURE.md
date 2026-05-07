# Codebase Structure

**Analysis Date:** 2026-05-07

## Directory Layout

```
/home/ubuntu/repos/lucienbot/
├── bot.py                      # Entry point (python bot.py)
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Project metadata
├── alembic.ini                 # Alembic migration config
├── architecture.md             # System architecture rules
├── rules.md                    # Coding rules (50-line limit, naming)
├── decisions.md                # Technical decisions
├── CLAUDE.md                   # Project instructions (this file)
├── AGENTS.md                   # Agent documentation
│
├── handlers/                   # Router files (25 total) - EVENT ROUTING ONLY
│   ├── __init__.py             # Router exports
│   ├── admin_handlers.py       # Admin panel
│   ├── channel_handlers.py     # Channel management
│   ├── vip_handlers.py         # VIP subscriptions
│   ├── vip_user_handlers.py    # VIP user flows
│   ├── free_channel_handlers.py
│   ├── gamification_user_handlers.py
│   ├── gamification_admin_handlers.py
│   ├── broadcast_handlers.py
│   ├── package_handlers.py
│   ├── mission_user_handlers.py
│   ├── mission_admin_handlers.py
│   ├── reward_user_handlers.py
│   ├── reward_admin_handlers.py
│   ├── store_user_handlers.py
│   ├── store_admin_handlers.py
│   ├── promotion_user_handlers.py
│   ├── promotion_admin_handlers.py
│   ├── story_user_handlers.py
│   ├── story_admin_handlers.py
│   ├── analytics_handlers.py
│   ├── anonymous_message_admin_handlers.py
│   ├── category_admin_handlers.py
│   ├── game_user_handlers.py       # Minijuegos (trivia/dice)
│   ├── trivia_admin_handlers.py    # Trivia config
│   ├── trivia_discount_admin_handlers.py
│   ├── question_set_admin_handlers.py
│   ├── trivia_stats_admin_handlers.py
│   ├── backpack_handler.py         # Mochila (Phase 15)
│   ├── leaderboard_handlers.py     # Leaderboard (Phase 16)
│   ├── common_handlers.py          # Start, help, etc.
│   ├── rate_limit_middleware.py    # ThrottlingMiddleware
│   ├── chat_action_middleware.py   # "typing..." indicator
│   └── CLAUDE.md
│
├── services/                   # Business logic (19 services)
│   ├── __init__.py             # Service exports + get_service context manager
│   ├── vip_service.py          # VIP subscriptions, tokens, tariffs
│   ├── channel_service.py      # Channel CRUD
│   ├── user_service.py         # User management
│   ├── besito_service.py        # Besitos (points) transactions
│   ├── broadcast_service.py     # Broadcast messages + reactions
│   ├── daily_gift_service.py   # Daily gift
│   ├── game_service.py          # Trivia + Dice minijuegos (66KB)
│   ├── leaderboard_service.py   # Leaderboards
│   ├── backpack_service.py      # User inventory (Phase 15)
│   ├── package_service.py       # Content packages
│   ├── store_service.py         # Store products
│   ├── mission_service.py       # Missions
│   ├── reward_service.py        # Rewards
│   ├── promotion_service.py      # Promotions
│   ├── story_service.py         # Narrative/archetypes
│   ├── scheduler_service.py     # APScheduler jobs (23KB)
│   ├── backup_service.py        # Database backups
│   ├── analytics_service.py     # Dashboard stats
│   ├── anonymous_message_service.py
│   ├── trivia_stats_service.py
│   ├── trivia_discount_service.py (34KB)
│   ├── trivia_config_service.py
│   ├── question_set_service.py
│   └── CLAUDE.md
│
├── models/                     # SQLAlchemy entities
│   ├── __init__.py             # Model exports
│   ├── models.py               # All entity definitions
│   ├── database.py             # Base, engine, SessionLocal, init_db
│   └── CLAUDE.md               # Model rules + migration guide
│
├── keyboards/                  # Telegram UI
│   ├── inline_keyboards.py     # All keyboard builders (18KB)
│   └── CLAUDE.md
│
├── utils/                      # Utilities
│   ├── helpers.py              # Generic helpers
│   ├── lucien_voice.py         # Lucien's persona (31KB)
│   └── CLAUDE.md
│
├── config/                     # Configuration
│   ├── settings.py             # bot_config from env vars
│   └── CLAUDE.md
│
├── alembic/                    # Database migrations
│   ├── versions/               # Migration scripts
│   └── alembic.ini
│
├── tests/                      # Test suite
│
├── docs/                       # Documentation + question sets
│   ├── preguntas.json          # Trivia questions (default)
│   └── ...
│
├── scripts/                    # Utility scripts
│
└── .planning/                  # GSD planning docs
    ├── codebase/               # Codebase maps (STACK.md, etc.)
    ├── phases/                 # Phase plans
    ├── notes/                  # Meeting notes
    └── quick/                  # Quick fix plans
```

## Directory Purposes

**Root Directory:**
- Purpose: Project root, entry point
- Contains: `bot.py`, `requirements.txt`, config files, `CLAUDE.md`

**handlers/:**
- Purpose: Route Telegram events to services
- Contains: 25 router files, 2 middleware files
- Key files: `game_user_handlers.py`, `backpack_handler.py`, `leaderboard_handlers.py`

**services/:**
- Purpose: Business logic per domain
- Contains: 19 service files + `__init__.py` with `get_service` context manager
- Key files: `game_service.py` (66KB, trivia+dice), `trivia_discount_service.py` (34KB)

**models/:**
- Purpose: SQLAlchemy ORM entities
- Contains: `models.py` (all entities), `database.py` (session management)

**keyboards/:**
- Purpose: Telegram inline keyboard definitions
- Contains: `inline_keyboards.py` (all keyboard builders)

**utils/:**
- Purpose: Shared utilities
- Contains: `helpers.py`, `lucien_voice.py` (personality module)

**config/:**
- Purpose: Environment-based settings
- Contains: `settings.py` with `bot_config` singleton

## Key File Locations

**Entry Points:**
- `bot.py`: Main entry point, dispatcher setup, polling

**Configuration:**
- `config/settings.py`: bot_config with TOKEN, ADMIN_IDS, REDIS_URL, etc.

**Core Logic:**
- `services/game_service.py`: Trivia and dice minigames
- `services/trivia_discount_service.py`: Trivia discount system
- `services/leaderboard_service.py`: Leaderboard rankings
- `services/backpack_service.py`: User inventory system

**Testing:**
- `tests/`: Test directory

## Naming Conventions

**Files:**
- Handlers: `{domain}_{scope}_handlers.py` (e.g., `game_user_handlers.py`)
- Services: `{domain}_service.py` (e.g., `game_service.py`, `backpack_service.py`)
- Middleware: `{name}_middleware.py`
- Models: `models.py` (singular file, not `model.py`)

**Functions:**
- Handlers: `async def handle_{action}(callback/message):`
- Services: `{verb}_{noun}_{result}` (e.g., `get_user_rank`, `play_dice_game`)
- Routers: `lambda c: c.data == "{callback_data}"`

**Routers:**
- Exported as: `router as {domain}_{scope}_router`
- Naming: `{domain}_{scope}_router` (e.g., `game_user_router`, `backpack_router`)

**FSM States:**
- Class: `{Feature}States` (e.g., `TriviaStreakStates`)
- States: `waiting_{step}`, `confirming`, `selecting_{item}`

## Where to Add New Code

**New Handler (User-facing):**
1. Create new `handlers/{domain}_{scope}_handlers.py` with router
2. Export router in `handlers/__init__.py`
3. Import and register in `bot.py:247-290`: `dp.include_router({domain}_{scope}_router)`
4. Add to `__all__` in `handlers/__init__.py`

**New Handler (Admin):**
1. Same as above but in admin handler file
2. Ensure admin permission check at start of handler

**New Service:**
1. Create `services/{domain}_service.py` with class
2. Export in `services/__init__.py`
3. Use `get_service({Domain}Service) as service:` pattern in handlers

**New Model:**
1. Add to `models/models.py`
2. Export in `models/__init__.py`
3. Create Alembic migration: `alembic revision -m "description"`
4. Run: `alembic upgrade head`

**New Keyboard:**
1. Add function to `keyboards/inline_keyboards.py`
2. Return `InlineKeyboardMarkup`
3. Import in handler as needed

**New Command/Callback:**
1. Determine domain
2. Add handler function to appropriate handler file
3. Use appropriate decorator: `@router.callback_query()` or `@router.message()`
4. Include logging: `logger.info(f"{file} - {func_name} - {user_id} - {result}")`

## Special Directories

**.planning/:**
- Purpose: GSD workflow documentation
- Generated: No
- Committed: Yes (version-controlled planning docs)

**alembic/versions/:**
- Purpose: Database migrations
- Generated: Partially (scaffold via alembic CLI, content is manual)
- Committed: Yes

**docs/:**
- Purpose: Static content (trivia questions, etc.)
- Generated: No
- Committed: Yes

---

*Structure analysis: 2026-05-07*