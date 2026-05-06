# Leaderboard Service y Handler - Outputs

## Archivos Generados

### 1. `leaderboard_service.py`
Nuevo servicio en `services/` para gestionar leaderboards de besitos.

**Metodos**:
- `get_top_users(limit: int = 10)` - Retorna top N usuarios con besitos
- `get_user_rank(user_id: int)` - Retorna la posicion del usuario en el ranking
- `update_score(user_id, amount, source, description)` - Actualiza besitos con transaccion
- `get_users_around_rank(user_id, range_: int = 2)` - Usuarios cercanos al rank del usuario

**Patron seguir**:
- Usa `with_for_update()` para prevenir race conditions
- Context manager para cleanup de sesiones
- Logging estructurado con `extra={'user_id': ...}`

### 2. `leaderboard_handler.py`
Handler thin que solo enruta eventos al LeaderboardService.

**Callbacks**:
- `leaderboard:menu` - Menu principal del leaderboard
- `leaderboard:my_rank` - Vista detallada del rank propio
- `leaderboard:nearby` - Usuarios cercanos al ranking

**Reglas aplicadas**:
- SIN logica de negocio en el handler
- SIN acceso directo a DB
- Un solo servicio por handler

## Integracion

Para usar estos archivos:
1. Copiar `leaderboard_service.py` a `services/`
2. Copiar `leaderboard_handler.py` a `handlers/`
3. Registrar el router en `bot.py` o en el archivo de routers principal:
   ```python
   from handlers.leaderboard_handler import router as leaderboard_router
   dp.include_router(leaderboard_router)
   ```
4. Agregar botones al menu principal para navegar al leaderboard:
   ```python
   InlineKeyboardButton(text="🏆 Leaderboard", callback_data="leaderboard:menu")
   ```

## Modelo de Datos

El servicio usa el modelo existente `BesitoBalance`:
- `user_id` - Identificador del usuario
- `balance` - Besitos actuales (usado para el ranking)
- `total_earned` - Total acumulado historico
- `total_spent` - Total gastado

No se requieren nuevas migraciones de DB.