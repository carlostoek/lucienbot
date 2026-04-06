# Quick Task: Reorganizar Menú Principal

## Objective
Reorganizar el menú principal del bot (main_menu_keyboard) según nuevo diseño.

## Changes Required
Modificar `keyboards/inline_keyboards.py`, función `main_menu_keyboard()`:

1. **El Diván** (solo VIP) - Primera fila
2. **Minijuegos** - Segunda fila  
3. **Saldo | Regalo** - Tercera fila (dos botones)
4. **Tienda** - Cuarta fila
5. **Misiones | Recompensas** - Quinta fila (dos botones)
6. **Ofertas** - Sexta fila
7. **Historia** - Séptima fila

## Callbacks to preserve
- `vip_area`, `game_menu`, `my_balance`, `daily_gift`, `shop`, `my_missions`, `rewards_list`, `offers`, `narrative`
