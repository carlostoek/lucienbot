# Servicios Existentes de Gamificación

## BesitoService

**Archivo**: `services/besito_service.py`

| Método | Qué hace | Retorna |
|--------|----------|---------|
| `get_or_create_balance(user_id)` | Get or create balance | `BesitoBalance` |
| `get_balance(user_id)` | Get current balance | `int` |
| `credit_besitos(user_id, amount, source, description)` | Add besitos | `int` (new balance) |
| `debit_besitos(user_id, amount, source, description)` | Remove besitos | `int` (new balance) |
| `has_sufficient_balance(user_id, amount)` | Check balance | `bool` |
| `get_transaction_history(user_id, limit)` | Transaction log | `List[BesitoTransaction]` |
| `get_top_users(limit)` | Leaderboard | `List[BesitoBalance]` |

---

## DailyGiftService

**Archivo**: `services/daily_gift_service.py`

| Método | Qué hace | Retorna |
|--------|----------|---------|
| `get_config()` | Get daily gift config | `DailyGiftConfig` |
| `can_claim(user_id)` | Check if 24h passed | `bool` |
| `claim_gift(user_id)` | Process daily claim | `dict` con status, message, amount |
| `get_claim_history(user_id, limit)` | Claim history | `List[DailyGiftClaim]` |

---

## GameService

**Archivo**: `services/game_service.py`

| Método | Qué hace | Retorna |
|--------|----------|---------|
| `play_dice_game(user_id)` | Roll dice, check win | `dict` con result, payout, message |
| `play_trivia(user_id, question_idx, answer_idx)` | Answer trivia | `dict` con correct, payout, streak |
| `play_trivia_vip(user_id, question_idx, answer_idx)` | VIP trivia | `dict` con correct, payout |
| `_get_streak_tier_info(user_id, streak)` | Check discount tier | `dict` con tier, discount |
| `invalidate_streak_code(user_id, config_id)` | Invalidate streak | `None` |

---

## MissionService

**Archivo**: `services/mission_service.py`

| Método | Qué hace | Retorna |
|--------|----------|---------|
| `create_mission(...)` | Create mission | `Mission` |
| `get_missions_by_type(mission_type)` | List missions | `List[Mission]` |
| `get_or_create_progress(user_id, mission_id)` | Get/create progress | `UserMissionProgress` |
| `increment_progress(user_id, mission_type, amount, reference_id)` | Track progress | `List[Mission]` (completed) |
| `increment_progress_and_deliver(user_id, mission_type, amount, bot, reference_id)` | Auto-deliver | `List[Mission]` |

---

## RewardService

**Archivo**: `services/reward_service.py`

| Método | Qué hace | Retorna |
|--------|----------|---------|
| `create_reward_besitos(name, description, besito_amount, created_by)` | Create besitos reward | `Reward` |
| `create_reward_package(name, description, package_id, created_by)` | Create package reward | `Reward` |
| `create_reward_vip(name, description, tariff_id, created_by)` | Create VIP reward | `Reward` |
| `deliver_reward(bot, user_id, reward_id, mission_id)` | Deliver async | `bool` |
| `get_user_reward_history(user_id, limit)` | Reward history | `List[UserRewardHistory]` |

---

## Modelos Relacionados

| Modelo | Ubicación | Campos clave |
|--------|-----------|-------------|
| `BesitoBalance` | `models/models.py` | user_id, balance, total_earned, total_spent |
| `BesitoTransaction` | `models/models.py` | user_id, amount, source, description, created_at |
| `DailyGiftConfig` | `models/models.py` | besito_amount, is_active |
| `DailyGiftClaim` | `models/models.py` | user_id, besitos_received, claimed_at |
| `Mission` | `models/models.py` | name, type, target_value, reward_id, frequency, is_active |
| `MissionType` | `models/models.py` (enum) | MESSAGE, REPLY, REACTION, BROADCAST |
| `UserMissionProgress` | `models/models.py` | user_id, mission_id, current_value, is_completed |
| `Reward` | `models/models.py` | name, type, besito_amount, package_id, tariff_id |
| `GameRecord` | `models/models.py` | user_id, game_type, result, payout |

---

## Patrones de Uso

```python
# Besitos
with get_service(BesitoService) as service:
    balance = service.get_balance(user_id)
    service.credit_besitos(user_id, 10, "daily_gift", "Regalo diario")

# Missions
with get_service(MissionService) as service:
    completed = service.increment_progress(user_id, MissionType.MESSAGE, 1, message_id)
    for mission in completed:
        service.deliver_reward(bot, user_id, mission.reward_id, mission.id)

# Rewards
with get_service(RewardService) as service:
    reward = service.create_reward_besitos("Bonus 100", "Por completar 100 msgs", 100, admin_id)
```

---

## Servicios Relacionados (no gamificación directa)

| Servicio | Archivo | Relación gamificación |
|----------|---------|----------------------|
| `UserService` | `services/user_service.py` | Perfil con nivel, streak |
| `StoreService` | `services/store_service.py` | Compra con besitos |
| `VIPService` | `services/vip_service.py` | VIP como recompensa |
| `BroadcastService` | `services/broadcast_service.py` | Missions de broadcast |
