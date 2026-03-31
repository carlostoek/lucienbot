# Phase 10: Flujos de entrada - Research

**Researched:** 2026-03-31
**Domain:** aiogram 3.x handlers, APScheduler 3.11.2, SQLAlchemy 2.0 migrations
**Confidence:** HIGH

## Summary

Phase 10 redesigns the entry flows for both Free (Los Kinkys) and VIP (El Diván) channels, converting cold automatic processes into narrative rituals that increase perceived exclusivity and retention. The Free channel gets a 30-second delayed welcome message + social buttons, a repeated-request message, and a rewritten approval message. The VIP channel gets a 3-phase callback-based ritual after token redemption before delivering the invite link.

Key technical pivot points identified: (1) APScheduler `DateTrigger` is the correct tool for the 30s delay job, not `IntervalTrigger` or `asyncio.sleep`; (2) the VIP flow should use persistent DB fields on `User` (`vip_entry_status`, `vip_entry_stage`) per the locked decision, checked inside `cmd_start` to resume interrupted flows; (3) the existing `_process_pending_requests` cron job at 09:00 is a functional bug for real-time approvals and must switch to an `IntervalTrigger` of 30 seconds; (4) new inline keyboards follow the established `inline_keyboards.py` convention.

**Primary recommendation:** Implement Free delay with APScheduler `DateTrigger` (+30s), fix pending-request approval with `IntervalTrigger(seconds=30)`, implement VIP ritual via DB fields on `User`, and handle flow resumption inside `cmd_start` before any token logic.

---

## Findings

### Canal Free — Delayed welcome and scheduling mechanisms

**Current behavior:** `free_channel_handlers.py::handle_join_request()` immediately sends `LucienVoice.free_request_received(channel.wait_time_minutes)` upon `ChatJoinRequest`. It also creates a `PendingRequest` whose `scheduled_approval_at` is set to `now + wait_time_minutes` (default 3 minutes). The `_process_pending_requests` scheduler job currently runs once daily at 09:00 via `cron` trigger, which means automatic approvals do not happen in real time.

**Locked decisions from CONTEXT.md:**
- Do **not** send the message immediately. Wait **30 seconds exactly**.
- Use an **APScheduler job** for the delay, **not** `asyncio.sleep` in the handler.
- Message 1 (after 30s) must include inline buttons to Instagram, TikTok, and X.
- Message 2 (if re-requesting while pending) has no buttons.
- Message 3 (on approval) replaces `LucienVoice.free_access_approved()`.
- The scheduler `_process_pending_requests` must change from daily cron to a short interval (e.g., every 30s or 1min).

**APScheduler trigger choice:**
- For the **30-second delay** (send welcome message at a specific future time), use `DateTrigger(run_date=datetime.utcnow() + timedelta(seconds=30))`. This fires exactly once.
- For the **pending-request approval loop**, use `IntervalTrigger(seconds=30)` (or `minutes=1`). This replaces the current `trigger="cron", hour=9, minute=0`.
- `scheduler.add_job(..., replace_existing=True)` is already the project pattern and should be reused.

**Where to add the delay job:** The `SchedulerService` or `ChannelService` should expose a method like `schedule_free_welcome_message(user_id, channel_id, run_date)` that calls `self._scheduler.add_job(func, trigger=DateTrigger(run_date=run_date), id=unique_job_id, replace_existing=True)`. Because `_scheduler` lives in `SchedulerService`, the cleanest approach is to add a public method there. The job handler must be a module-level function (not a bound method) so APScheduler + `SQLAlchemyJobStore` can serialize it — this is the same pattern already used for `_process_pending_requests`, `_run_backup_job`, etc.

**Repeated-request flow:** In `handle_join_request()`, if `existing_request` is found and still `pending`, instead of silently returning, the bot should send Message 2 (the "impatience" message) with no keyboard.

### Canal VIP — 3-Phase ritualized entry flow

**Current behavior:** `common_handlers.py::cmd_start()` calls `vip_service.redeem_token(args, user.id)`. If successful, it immediately replies with `LucienVoice.vip_activated(...)` and generates a one-time invite link via `bot.create_chat_invite_link(chat_id=vip_channel.channel_id, member_limit=1)`.

**Locked decisions from CONTEXT.md:**
- Token redemption must still happen at `/start <token>`, but the link is **not** delivered immediately.
- The user enters `pending_entry` state.
- Add two columns to `User`: `vip_entry_status` (null | `"pending_entry"` | `"active"`) and `vip_entry_stage` (null | `1` | `2` | `3`).
- Phase 1 (`stage=1`): ritual message + button "Continuar" → advances to `stage=2`.
- Phase 2 (`stage=2`): alignment message + button "Estoy listo" → advances to `stage=3`.
- Phase 3 (`stage=3`): generate one-time invite link, send final message, set `vip_entry_status="active"`, `vip_entry_stage=null`.
- If the user returns to `/start` (with or without the same token), resume from the current stage by reading the `User` fields.
- If the subscription expires before completing the flow, cancel the process and inform the user.

**State persistence: DB fields vs. FSM:** The PRD explicitly requires DB fields, not aiogram FSM states. This is the correct choice because:
1. The ritual can span hours/days; FSM `MemoryStorage` would lose state on restart, and even `RedisStorage` is tied to a single chat session and could be cleared.
2. The fields must survive across `/start` invocations, including when the user clicks a deep link with the same token again.
3. It keeps the logic queryable (e.g., analytics can later count users stuck in `pending_entry`).

**Handler location for VIP flow callbacks:** Two clean options were considered:
- Add callback handlers to `vip_handlers.py` (where `TariffStates` and `TokenStates` already live).
- Add them to `common_handlers.py` near `cmd_start`.

**Recommendation:** Place the new VIP entry-flow callbacks in `vip_handlers.py` to keep VIP domain handlers together, but `cmd_start` in `common_handlers.py` must check `user.vip_entry_status == "pending_entry"` every time it runs (before token processing). This follows the existing router separation: `common_handlers.py` = entry commands, `vip_handlers.py` = VIP management and now VIP entry ritual.

**`/start` resumption logic:** In `cmd_start`, after getting/creating the `db_user`, add a guard:
```python
if db_user.vip_entry_status == "pending_entry":
    # Check subscription is still active; if expired, clear state and notify
    # Otherwise route to the appropriate stage message via VIPService
    await message.answer(...)
    return
```
This handles both plain `/start` and `/start <token>` because the token was already redeemed on the first visit.

**What if the user sends `/start <same_token>` again?** Since the token is already `USED`, `redeem_token()` will return `None`. But before hitting token validation logic, the `pending_entry` guard above will intercept and resume the ritual, avoiding the "token already used" error message entirely.

**Subscription expiration during flow:** `VIPService` should expose a method like `get_vip_entry_subscription(user_id)` that returns the active `Subscription` for the user. If `subscription.end_date < now` or `subscription.is_active == False`, the handler/service should:
1. Set `vip_entry_status = None`, `vip_entry_stage = None`.
2. Send an expiration notice (`LucienVoice.vip_expired()` or a new specific message).
3. Not generate the invite link.

**Invite link generation in Phase 3:** Reuse the exact pattern from `common_handlers.py`:
```python
invite_link = await message.bot.create_chat_invite_link(
    chat_id=vip_channel.channel_id,
    name=f"VIP {user.id}",
    creates_join_request=False,
    member_limit=1
)
```
With fallback to `vip_channel.invite_link` if the API call raises.

### Keyboard and naming conventions

**Current pattern in `keyboards/inline_keyboards.py`:**
- Functions return `InlineKeyboardMarkup(inline_keyboard=buttons)`.
- Button text uses emojis and elegant Spanish per Lucien’s voice.
- Callback data uses lowercase with underscores: `back_to_main`, `manage_tariffs`, `select_tariff_{id}`, etc.

**New keyboards needed:**
1. `free_welcome_keyboard()` — buttons for Instagram, TikTok, X with callback data like `social_instagram`, `social_tiktok`, `social_x` (or external URLs). Actually, these are **external links**, so they should use `url=` parameter of `InlineKeyboardButton`, not `callback_data`. Example:
   ```python
   InlineKeyboardButton(text="Instagram", url="https://www.instagram.com/srta.kinky")
   ```
2. `vip_entry_phase1_keyboard()` — single button with callback data `vip_entry_continue`.
3. `vip_entry_phase2_keyboard()` — single button with callback data `vip_entry_ready`.

**Naming convention:** Per `keyboards/CLAUDE.md`, keep keyboards concise (no more than 3 rows), always include a back/cancel where appropriate. For these ritual keyboards, no back button is needed because the flow is linear and intentional.

### Database migration requirements

**Alembic is integrated and actively used.** The project uses Alembic with `SQLAlchemyJobStore` pointing to the same database. Any schema change must include an Alembic migration.

**Changes required:**
1. Add `vip_entry_status` (String, nullable, default=None) to `users` table.
2. Add `vip_entry_stage` (Integer, nullable, default=None) to `users` table.

**Migration command:** `alembic revision --autogenerate -m "add vip entry status and stage to users"` should be run after updating `models.py`. The migration file will be generated under `migrations/versions/`.

**Important:** The `conftest.py` test fixtures create tables via `Base.metadata.create_all(engine)` on an in-memory SQLite, so new columns will automatically be available in tests without a migration file. However, production (Railway/PostgreSQL) requires the migration.

### Scheduler bug and interval-based approvals

**Current bug (CRITICAL):** `scheduler_service.py` registers `_process_pending_requests` with:
```python
trigger="cron", hour=9, minute=0
```
This means pending free-channel requests are only approved once per day at 9:00 AM, regardless of their `scheduled_approval_at`. The intent of `wait_time_minutes` (default 3 minutes) is completely broken.

**Fix:** Change the trigger to:
```python
trigger=IntervalTrigger(seconds=30)
```
(or `minutes=1` if 30s feels too aggressive). The `_process_pending_requests` function already queries `get_ready_to_approve()` which filters by `scheduled_approval_at <= now`, so running it frequently is safe and correct.

**No other scheduler changes needed** beyond adding the new `DateTrigger` job for the Free welcome message delay.

### VIPService and ChannelService extension points

**VIPService additions needed:**
- `set_user_vip_entry_status(user_id, status, stage)` — atomic update.
- `get_vip_entry_state(user_id)` — returns `(status, stage)` or `None`.
- `advance_vip_entry_stage(user_id)` — moves `1→2→3` and handles boundary.
- `clear_vip_entry_state(user_id)` — sets both fields to `None`.
- `get_active_subscription_for_entry(user_id)` — validates subscription is still active before Phase 3 link generation.

**ChannelService additions needed:**
- `schedule_free_welcome(bot, user_id, channel_id)` — or this could live in `SchedulerService` as discussed. Given the handler layer restriction (no business logic), the cleanest split is:
  - `ChannelService` checks whether to schedule or send the repeated-request message.
  - `SchedulerService` exposes `add_job` wrapper for the delay.

Because `SchedulerService` already has `_scheduler` and the lazy bot pattern, adding a public method like `SchedulerService.schedule_free_welcome(user_id, channel_id)` is architecturally sound. However, handlers must not talk to two services if possible. **Better pattern:** `ChannelService` takes an optional `scheduler` reference, or `SchedulerService` is called explicitly from the handler. Given the handler rules say "call exactly 1 service," and the delay is a channel-domain concern, the pragmatic approach is to extend `ChannelService` with a `scheduler` parameter in its constructor or add a standalone `SchedulerService` call with a thin `ChannelService` wrapper.

**Decision at planner discretion:** Either add a `scheduler` dependency to `ChannelService` or let the handler call `channel_service.handle_join_request_event(...)` which internally delegates scheduling. The key is keeping handler code minimal.

### Message templates (LucienVoice)

**New methods required in `utils/lucien_voice.py`:**
- `free_welcome_ritual()` — Message 1 (with social buttons).
- `free_request_already_pending()` — Message 2.
- `free_access_approved_ritual(channel_name)` — Message 3 (replaces current `free_access_approved`).
- `vip_entry_phase1()` — "Veo que ha dado el paso..."
- `vip_entry_phase2()` — "El Diván no es un lugar..."
- `vip_entry_phase3()` — "Entonces no le haré esperar más..."
- `vip_entry_expired()` — new message if subscription expires during ritual (can reuse `vip_expired()` if appropriate, but a distinct message is preferable per PRD).

All must follow the existing convention: `@staticmethod`, return `str`, `parse_mode="HTML"`.

### Router registration

**Current pattern in `bot.py`:**
```python
from handlers import (
    common_router, admin_router, channel_router, vip_router,
    free_channel_router, ...
)
```
No new router is needed if callbacks are added to existing `vip_router` or `common_router`. The `free_channel_router` already handles `ChatJoinRequest` and `ChatMemberUpdated`.

## Recommendations

### 1. Fix scheduler approval interval immediately
Change `_process_pending_requests` in `SchedulerService.start()` from `trigger="cron", hour=9, minute=0` to `trigger=IntervalTrigger(seconds=30)` (or `minutes=1`). This is a one-line fix with high impact.

### 2. Implement Free channel delay with `DateTrigger`
In `handle_join_request()`:
- Remove immediate `send_message`.
- After creating `PendingRequest`, schedule a one-time APScheduler job with `DateTrigger(run_date=datetime.utcnow() + timedelta(seconds=30))`.
- The job handler sends `LucienVoice.free_welcome_ritual()` with the social URL keyboard.
- If `existing_request` is found, send `LucienVoice.free_request_already_pending()` and return.

### 3. Add `User` columns and migration
Update `models.py` `User` table:
```python
vip_entry_status = Column(String(20), nullable=True)  # pending_entry | active
vip_entry_stage = Column(Integer, nullable=True)      # 1 | 2 | 3
```
Run Alembic autogenerate and include migration in PR.

### 4. Implement VIP entry ritual in `vip_handlers.py`
Add two callback handlers:
- `@router.callback_query(F.data == "vip_entry_continue")` for Phase 1 → 2.
- `@router.callback_query(F.data == "vip_entry_ready")` for Phase 2 → 3.

Delegate stage advancement to `VIPService` methods (max 50 lines per function).

### 5. Modify `cmd_start` to detect and resume pending entry
Before token redemption logic, after `get_or_create_user`:
```python
if db_user.vip_entry_status == "pending_entry":
    subscription = vip_service.get_active_subscription_for_entry(user.id)
    if not subscription or subscription.end_date < datetime.utcnow():
        vip_service.clear_vip_entry_state(user.id)
        await message.answer(LucienVoice.vip_entry_expired(), parse_mode="HTML")
        return
    # Route to the correct stage message
    stage = db_user.vip_entry_stage or 1
    ...
    return
```

### 6. New keyboards
Add to `inline_keyboards.py`:
- `free_welcome_keyboard()` with URL buttons.
- `vip_entry_phase1_keyboard()` with callback `vip_entry_continue`.
- `vip_entry_phase2_keyboard()` with callback `vip_entry_ready`.

## Risks and Considerations

### Risk 1: APScheduler job ID collisions
**What can go wrong:** If multiple join requests arrive from the same user for the same channel, `DateTrigger` jobs could overwrite each other if IDs are not unique, or duplicate jobs could accumulate if `replace_existing=False`.
**Mitigation:** Use a deterministic job ID like `f"free_welcome_{user_id}_{channel_id}"` and pass `replace_existing=True`. The handler already checks for `existing_request`, so duplicates should be rare, but `replace_existing` makes the schedule idempotent.

### Risk 2: `ChatJoinRequest` handler takes >10 seconds to respond to Telegram
**What can go wrong:** Telegram expects a quick ack from `ChatJoinRequest`. If the handler schedules an APScheduler job synchronously (it is fast) there is no issue. But if any DB operation hangs, Telegram may retry the join request.
**Mitigation:** The handler logic is lightweight (one insert + one scheduler add). Ensure no `await asyncio.sleep` or long I/O is introduced.

### Risk 3: Subscription expires while user is mid-ritual
**What can go wrong:** If a user stops at Phase 2 and their subscription expires before clicking "Estoy listo", Phase 3 must detect this and refuse link generation.
**Mitigation:** Every transition into Phase 3 must verify `subscription.is_active` and `end_date > now`. Use a `VIPService` guard method shared by the callback handler and `cmd_start` resumption.

### Risk 4: Returning to `/start <used_token>` shows "token used" error instead of resuming
**What can go wrong:** If `cmd_start` processes the token argument before checking `vip_entry_status`, the user sees `LucienVoice.token_used()` and thinks something is broken.
**Mitigation:** Always check `db_user.vip_entry_status == "pending_entry"` **before** any token redemption or validation logic in `cmd_start`.

### Risk 5: Migration not run in production
**What can go wrong:** New code references `vip_entry_status` but the Railway PostgreSQL database doesn't have the columns yet.
**Mitigation:** Include the Alembic migration file in the phase commit and document it as a deployment step. Verify via `alembic upgrade head` before deploying.

### Risk 6: `_process_pending_requests` interval increases DB load
**What can go wrong:** Running every 30 seconds queries `pending_requests` continuously. At current scale this is negligible, but if the table grows very large, frequent polling could become noisy.
**Mitigation:** 30s interval is safe for expected user counts (<10k). The query is a simple indexed filter on `status + scheduled_approval_at`. If scale increases later, consider an event-driven approach or partial index.

### Risk 7: Handler rule violations (logic in handler)
**What can go wrong:** It is tempting to put stage-advancement logic or invite-link generation directly in the callback handlers.
**Mitigation:** Strictly follow `handlers/CLAUDE.md`: handlers route only. All state changes, link generation, and status checks must be in `VIPService` or `ChannelService`. Keep every handler function under 50 lines.

## Validation Architecture

Framework: **pytest** with in-memory SQLite.
Quick run: `pytest tests/unit/test_vip_service.py tests/unit/test_channel_service.py -x`
Full suite: `pytest tests/ -x`

### Phase 10 test gaps (Wave 0)
- [ ] `tests/unit/test_vip_service.py` needs tests for `set_user_vip_entry_status`, `advance_vip_entry_stage`, `clear_vip_entry_state`.
- [ ] `tests/integration/test_vip_flow.py` needs a test for the 3-phase ritual resumption and expiration guard.
- [ ] No existing test covers `handle_join_request` or scheduler job registration (integration level). At minimum, test `ChannelService` scheduling method.

## Sources

### Primary (HIGH confidence)
- `/data/data/com.termux/files/home/repos/lucien_bot/handlers/common_handlers.py` — `cmd_start` VIP token flow
- `/data/data/com.termux/files/home/repos/lucien_bot/handlers/free_channel_handlers.py` — `ChatJoinRequest` handling
- `/data/data/com.termux/files/home/repos/lucien_bot/handlers/vip_handlers.py` — callback patterns and FSM usage
- `/data/data/com.termux/files/home/repos/lucien_bot/services/scheduler_service.py` — APScheduler 3.11.2 setup and job registration
- `/data/data/com.termux/files/home/repos/lucien_bot/services/channel_service.py` — pending request logic
- `/data/data/com.termux/files/home/repos/lucien_bot/services/vip_service.py` — token redemption and subscription queries
- `/data/data/com.termux/files/home/repos/lucien_bot/models/models.py` — `User`, `Channel`, `PendingRequest`, `Subscription`
- `/data/data/com.termux/files/home/repos/lucien_bot/keyboards/inline_keyboards.py` — keyboard conventions
- `/data/data/com.termux/files/home/repos/lucien_bot/utils/lucien_voice.py` — message template conventions
- APScheduler 3.11.2 `DateTrigger` and `IntervalTrigger` API verified in Python REPL

### Secondary (MEDIUM confidence)
- `/data/data/com.termux/files/home/repos/lucien_bot/alembic/env.py` — migration configuration and `Base.metadata`

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries (aiogram 3.26.0, APScheduler 3.11.2, SQLAlchemy 2.0.48) are installed and their APIs were verified in REPL.
- Architecture: HIGH — project follows strict handlers/services/models layering; patterns are well documented in `CLAUDE.md` files.
- Pitfalls: HIGH — the 09:00 cron bug, FSM vs DB tradeoffs, and token-used vs resume race were all identified from direct code reading.

**Research date:** 2026-03-31
**Valid until:** 2026-04-30
