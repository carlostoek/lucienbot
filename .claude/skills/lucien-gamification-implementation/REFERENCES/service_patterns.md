# Service Patterns para Gamificación

## Estructura Base

```python
class GamificationService:
    def __init__(self):
        self.session = Session()

    def close(self):
        self.session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        self.close()
```

## Context Manager Pattern

```python
from services import get_service

# En handlers:
with get_service(GamificationService) as service:
    result = service.process_streak(user_id)
```

El `get_service` factory ya existe en `services/__init__.py`.

---

## CRUD de Balance (Besitos)

```python
async def get_or_create_balance(self, user_id: int) -> BesitoBalance:
    balance = self.session.query(BesitoBalance).filter_by(user_id=user_id).first()
    if not balance:
        balance = BesitoBalance(user_id=user_id, balance=0, total_earned=0, total_spent=0)
        self.session.add(balance)
        self.session.flush()
    return balance

async def credit_besitos(self, user_id: int, amount: int, source: str, description: str) -> int:
    """Credita besitos con transacción para evitar race conditions."""
    with self.session.begin():
        balance = self.session.query(BesitoBalance).filter_by(user_id=user_id).with_for_update().first()
        if not balance:
            balance = BesitoBalance(user_id=user_id, balance=0, total_earned=0, total_spent=0)
            self.session.add(balance)

        balance.balance += amount
        balance.total_earned += amount

        tx = BesitoTransaction(
            user_id=user_id,
            amount=amount,
            source=source,
            description=description
        )
        self.session.add(tx)

    return balance.balance
```

**Importante**: `with_for_update()` previene race conditions en concurrent writes.

---

## Racha Diaria (Daily Streak)

```python
async def process_daily_streak(self, user_id: int) -> dict:
    """Retorna dict con {status, message, bonus}."""
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    last = user.last_checkin

    # Ventana de gracia: 20-48 horas
    if last and (now - last) < timedelta(hours=20):
        return {"status": "already_claimed", "message": "⏳ Ya reclamaste hoy."}

    if last and (now - last) > timedelta(hours=48):
        # Racha rompida
        lost = user.streak
        user.streak = 1
        user.last_checkin = now
        return {
            "status": "streak_lost",
            "message": f"💔 Racha perdida ({lost} días). Empezando de nuevo.",
            "bonus": 10
        }

    # Racha mantenida
    user.streak += 1
    user.last_checkin = now
    bonus = min(user.streak * 5, 50)  # Cap en 50

    return {
        "status": "success",
        "message": f"🔥 Racha: {user.streak} días (+{bonus} bonus)",
        "bonus": bonus
    }
```

---

## VR Surprise Reward

```python
import random

async def check_vr_reward(self, user_id: int, state: FSMContext) -> bool:
    """Check si usuario recibe reward VR. Retorna True si sí."""
    data = await state.get_data()
    interactions = data.get("vr_interactions", 0)

    base_chance = 0.05
    accumulated = min(base_chance + (interactions * 0.03), 0.35)

    if random.random() < accumulated:
        # Reward!
        reward = random.randint(5, 20)
        await self.credit_besitos(user_id, reward, "vr_surprise", "Recompensa sorpresa VR")
        await state.update_data(vr_interactions=0)
        return True
    else:
        await state.update_data(vr_interactions=interactions + 1)
        return False
```

---

## Validación Pre-Transacción

```python
async def debit_if_possible(self, user_id: int, amount: int, source: str, description: str) -> bool:
    """Returns True si se pudo debitar, False si saldo insuficiente."""
    balance = self.get_balance(user_id)
    if balance < amount:
        return False

    with self.session.begin():
        bal = self.session.query(BesitoBalance).filter_by(user_id=user_id).with_for_update().first()
        if bal.balance < amount:
            return False
        bal.balance -= amount
        bal.total_spent += amount
        tx = BesitoTransaction(...)
        self.session.add(tx)
    return True
```

---

## Anti-Patrones Services

| Anti-Patrón | Problema | Alternativa |
|------------|---------|-------------|
| Lógica de negocio en handler | Viola arquitectura | Solo services |
| Sin `with_for_update()` en créditos | Race conditions | Row locking |
| No cerrar sessions | Memory leaks | Context manager |
| Hardcodear IDs | Tight coupling | Constants/enums |
| No logging | Debugging difícil | `logger.info(f"...", extra={"user_id": ...})` |
