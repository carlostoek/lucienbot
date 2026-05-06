# Sistema de Racha Diaria - Implementación

## Archivos Generados

| Archivo | Descripción |
|---------|-------------|
| `fsm.py` | Estados FSM y constantes de ventana de gracia |
| `service.py` | `DailyStreakService` con lógica de negocio |
| `handler.py` | Handlers con inline keyboard para flujo de racha |

## Arquitectura

```
handlers/ → DailyStreakService → models/ → database
              ↓
         FSM (DailyStreakStates)
```

## FSM States

- `checking_streak` - Verificando estado inicial
- `streak_active` - Racha activa (ya reclamó hoy, <20h)
- `streak_claiming` - Procesando reclamo
- `streak_lost` - Racha rota (>48h gap)
- `grace_period` - Ventana de gracia (20-48h gap)

## Ventana de Gracia (48 horas)

```
< 20h          → already_claimed (ya reclamó hoy)
20h - 48h      → grace_period (puede reclamar, streak mantenida)
> 48h          → streak_lost (streak se reinicia a 1)
```

## Bonus Formula

```
bonus = min(streak_days * 5, 50)  # Cap en 50 besitos
```

## Callback Data Convention

```
streak:show    → Ver estado de racha
streak:claim   → Reclamar racha
streak:cancel  → Cancelar flujo
```

## Integración Requerida

1. **Modelos**: Agregar campos `streak` (int) y `last_checkin` (datetime) al modelo `User`:
   ```python
   # En models/models.py - modelo User
   streak = Column(Integer, default=0)
   last_checkin = Column(DateTime(timezone=True), nullable=True)
   ```

2. **Migration**:
   ```bash
   alembic revision --autogenerate -m "add_streak_fields_to_user"
   alembic upgrade head
   ```

3. **Registrar router en bot.py**:
   ```python
   from handlers.daily_streak_handlers import router as streak_router
   dp.include_router(streak_router)
   ```

4. **Agregar botón al menú principal** (en `inline_keyboards.py`):
   ```python
   [InlineKeyboardButton(text="🔥 Mi Racha", callback_data="streak:show")]
   ```

## Notas de Implementación

- El servicio usa `DailyGiftClaim` como proxy para tracking si no existen los campos en `User`
- La ventana de gracia de 48h permite mantener la racha aunque el usuario no entre exactamente a las 24h
- El bonus es `streak_days * 5` con máximo de 50 besitos
- El servicio es atómico: usa transacciones para evitar race conditions
