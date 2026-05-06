# Leaderboard Service - Implementation

## Created Files

### `services/leaderboard_service.py`

**Class:** `LeaderboardService`

**Methods:**

- `get_top_users(limit=10, scope="global")` - Returns a list of dicts with `rank`, `user_id`, `username`, `first_name`, `balance`, `total_earned`. Queries `BesitoBalance` joined with `User`, ordered by balance descending.

- `get_user_rank(user_id)` - Returns `{"rank", "user_id", "balance", "total_earned", "total_active_users"}` or `None` if the user has no balance. Rank is computed by counting users with higher balance.

- `update_score(user_id, delta, reason=None)` - Wrapper that calls `BesitoService.credit_besitos` or `debit_besitos` with `TransactionSource.ADMIN`. Returns `bool`.

- `get_user_position_around(user_id, radius=2)` - Returns `{"user": {...}, "surrounding": [...]}` showing the user and N nearby entries. Uses offset-based pagination on the leaderboard query.

**Architecture notes:**
- Follows the existing service pattern: `_owns_session` + `_get_db()` + `close()` lifecycle
- Uses existing `BesitoBalance` and `User` models — no new tables needed
- Logs every action with `logger.info`
- Functions stay under 50 lines

---

### `handlers/leaderboard_handlers.py`

**Callbacks:**

- `leaderboard` - Shows the global top 10 with medals for ranks 1-3. Includes the user's own rank at the bottom if available.

- `my_rank` - Shows the user's exact rank and the 2 entries above and below them, with an arrow marker on the current user's line.

**Pattern used:**
- Single service call per handler
- `try/finally` for service lifecycle management
- `callback.message.edit_text` with `parse_mode="HTML"`
- `back_keyboard` for navigation
- Follows existing `gamification_user_handlers.py` conventions

---

## Integration Points

1. **Register router in `bot.py` or `handlers/__init__.py`:**
   ```python
   from handlers.leaderboard_handlers import router as leaderboard_router
   dp.include_router(leaderboard_router)
   ```

2. **Add menu buttons** (e.g., in `main_menu_keyboard`):
   - `["🏆 Ver Ranking", "my_rank"]`
   - `["🏅 Mi Posicion", "leaderboard"]`

3. **Optional: Admin handler** for `update_score` to manually adjust scores, following the pattern in `gamification_admin_handlers.py`.

---

## No New Models Required

The service reuses `BesitoBalance` for the ranking data. If weekly/monthly scopes are needed in the future, a new model (e.g., `LeaderboardSnapshot`) would be required with a migration.
