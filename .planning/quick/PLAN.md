# Quick Plan: Reorganizar Menú Principal

## Task 1: Modificar main_menu_keyboard
**File:** `keyboards/inline_keyboards.py`
**Function:** `main_menu_keyboard(is_vip: bool)`

### Current Structure
```python
buttons = [
    [saldo],
    [regalo],
    [misiones],
    [recompensas],
    [tienda],
    [ofertas],
    [historia],
    [minijuegos]
]
# El Diván insertado al inicio si is_vip
```

### New Structure
```python
buttons = []
if is_vip:
    buttons.append([El Diván])

buttons.extend([
    [Minijuegos],
    [Saldo, Regalo],        # Dos botones en fila
    [Tienda],
    [Misiones, Recompensas], # Dos botones en fila
    [Ofertas],
    [Historia]
])
```

### Button Definitions
1. `💎 El Diván` → `vip_area` (solo VIP)
2. `🎮 Minijuegos` → `game_menu`
3. `💋 Mi saldo de besitos` → `my_balance`
4. `🎁 Regalo diario` → `daily_gift`
5. `🛍️ Tienda de Diana` → `shop`
6. `🎯 Mis misiones` → `my_missions`
7. `🎁 Recompensas` → `rewards_list`
8. `✨ Ofertas especiales` → `offers`
9. `📖 Fragmentos de la historia` → `narrative`

## Verification
- [ ] Botones aparecen en orden correcto
- [ ] Saldo y Regalo comparten fila
- [ ] Misiones y Recompensas comparten fila
- [ ] El Diván solo aparece para VIP
- [ ] Todos los callback_data funcionan
