# UI Patterns: Inline Keyboards y Mensajes

## Barra de Progreso

```python
def level_progress_bar(current_xp: int, xp_to_next: int, length: int = 10) -> str:
    """Retorna string tipo '██████░░░░' con length caracteres."""
    if xp_to_next <= 0:
        return "░" * length
    filled = int((current_xp / xp_to_next) * length)
    return "█" * filled + "░" * (length - filled)
```

## Perfil Gamificado

```python
async def send_gamified_profile(message: Message, user: UserProfile):
    bar = level_progress_bar(user.xp, user.xp_next)
    text = (
        f"🏅 <b>{user.display_name}</b>\n"
        f"Nivel: {user.level} {user.rank_emoji}\n"
        f"XP: {user.xp}/{user.xp_next}\n"
        f"{bar}\n\n"
        f"🔥 Racha: {user.streak} días\n"
        f"💰 Besitos: {user.balance}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Leaderboard", callback_data="nav:leaderboard")],
        [InlineKeyboardButton(text="🎁 Regalo Diario", callback_data="daily:claim")],
        [InlineKeyboardButton(text="🎮 Jugar", callback_data="game:menu")],
    ])
    await message.answer(text, reply_markup=kb, parse_mode="HTML")
```

## Menú de Juego

```python
def game_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎲 Dados", callback_data="game:roll:dice"),
            InlineKeyboardButton(text="🧩 Trivia", callback_data="game:trivia:start"),
        ],
        [
            InlineKeyboardButton(text="🔥 Mi Racha", callback_data="streak:status"),
            InlineKeyboardButton(text="🎁 Regalo Diario", callback_data="daily:claim"),
        ],
        [
            InlineKeyboardButton(text="📜 Missiones", callback_data="missions:list"),
            InlineKeyboardButton(text="🏆 Top Besitos", callback_data="nav:top"),
        ],
    ])
```

## Confirmación con Volver

```python
def confirmation_keyboard(action: str, entity_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Confirmar", callback_data=f"confirm:{action}:{entity_id}"),
            InlineKeyboardButton(text="❌ Cancelar", callback_data=f"cancel:{action}:{entity_id}"),
        ],
        [InlineKeyboardButton(text="← Volver", callback_data=f"back:{action}")],
    ])
```

## Estados Visuales con Toggle

```python
# Callback para toggle selección
@router.callback_query(F.data.startswith("select:"))
async def toggle_selection(callback: CallbackQuery):
    item_id = callback.data.replace("select:", "")
    current = selected_items.get(callback.from_user.id, set())

    if item_id in current:
        current.remove(item_id)
        label = f"❌ Opción {item_id}"
    else:
        current.add(item_id)
        label = f"✅ Opción {item_id}"

    # Editar solo el botón, no todo el mensaje
    await callback.answer(f"Selección: {len(current)} items")
```

## Editar Mensaje en Lugar de Enviar Nuevo

```python
# Correcto — editar mensaje existente
await callback.message.edit_text(
    new_text,
    reply_markup=new_keyboard,
    parse_mode="HTML"
)

# Incorrecto — no enviar nuevos mensajes constantemente
# await callback.message.answer(new_text)  # NO HACER ESTO
```

## Reglas de UX

1. **Emoji al inicio**: procesan más rápido que texto
2. **3-4 botones por fila**: funciona bien en móviles
3. **Acciones destructivas al final**: siempre en fila propia
4. **Siempre `callback.answer()`**: evita spinner de 30s
5. **`editMessageReplyMarkup`** para actualizar keyboards sin cambiar texto

## Límites Técnicos

| Límite | Valor | Solución |
|--------|-------|----------|
| `callback_data` | 64 bytes max | Usar prefijo corto |
| Botones por fila | 8 max, práctico 3-4 | Paginar |
| Filas por keyboard | Sin límite técnico, >10 push fuera | Paginar |
| `editMessageText` | Solo mensaje <48h | Nuevo mensaje si viejo |
