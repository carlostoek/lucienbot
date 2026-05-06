"""
Handlers de Leaderboard - Lucien Bot

Handlers para clasificaciones de gamificacion.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from services.leaderboard_service import LeaderboardService
from keyboards.inline_keyboards import back_keyboard
import logging

logger = logging.getLogger(__name__)
router = Router()


def _format_leaderboard_entry(entry: dict, max_rank_width: int = 2) -> str:
    """Formatea una entrada del leaderboard."""
    rank = entry["rank"]
    name = entry.get("username") or entry.get("first_name") or "Visitante"
    balance = entry["balance"]

    medal = ""
    if rank == 1:
        medal = "👑 "
    elif rank == 2:
        medal = "🥈 "
    elif rank == 3:
        medal = "🥉 "

    return f"{medal}<b>#{rank}</b> {name} — {balance} 💋"


@router.callback_query(F.data == "leaderboard")
async def show_leaderboard(callback: CallbackQuery):
    """Muestra el leaderboard global de besitos."""
    user_id = callback.from_user.id

    service = LeaderboardService()
    try:
        top_users = service.get_top_users(limit=10)
        user_rank = service.get_user_rank(user_id)
    finally:
        service.close()

    if not top_users:
        text = """🎩 <b>Lucien:</b>

<i>El salon permanece vacio...</i>

<b>No hay visitantes en el ranking todavia.</b>

<i>Sea el primero en acumular besitos.</i>"""
    else:
        lines = ["🎩 <b>Lucien:</b>\n", "<i>Los mas devotos seguidores de Diana...</i>\n"]
        lines.append("🏆 <b>Top Besitos:</b>\n")

        for entry in top_users:
            lines.append(_format_leaderboard_entry(entry))

        if user_rank:
            lines.append(f"\n<i>Su posicion: #<b>{user_rank['rank']}</b> "
                         f"de {user_rank['total_active_users']}</i>")
        else:
            lines.append("\n<i>Aun no tiene besitos acumulados.</i>")

        text = "\n".join(lines)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Actualizar", callback_data="leaderboard")],
        [InlineKeyboardButton(text="🔙 Volver", callback_data="back_to_main")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "my_rank")
async def show_my_rank(callback: CallbackQuery):
    """Muestra el ranking detallado del usuario actual."""
    user_id = callback.from_user.id

    service = LeaderboardService()
    try:
        position = service.get_user_position_around(user_id, radius=2)
    finally:
        service.close()

    if not position:
        text = """🎩 <b>Lucien:</b>

<i>Aun no tiene presencia en el salon...</i>

<b>Aun no ha acumulado besitos.</b>

<i>Participe en las misiones y juegos para entrar al ranking.</i>"""

        keyboard = back_keyboard("leaderboard")
    else:
        user = position["user"]
        surrounding = position["surrounding"]

        lines = [f"🎩 <b>Lucien:</b>\n",
                 f"<i>Su lugar en el salon de Diana...</i>\n",
                 f"🏅 <b>Posicion:</b> #<b>{user['rank']}</b> "
                 f"de {user['total_active_users']}\n",
                 f"💋 <b>Besitos:</b> {user['balance']}\n",
                 "<b>Visitantes cercanos:</b>\n"]

        for entry in surrounding:
            marker = "👉 " if entry.get("is_current_user") else "   "
            name = entry.get("username") or entry.get("first_name") or "Visitante"
            lines.append(f"{marker}#{entry['rank']} {name} — {entry['balance']} 💋")

        text = "\n".join(lines)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Actualizar", callback_data="my_rank")],
            [InlineKeyboardButton(text="🔙 Ver Top", callback_data="leaderboard")],
            [InlineKeyboardButton(text="🔙 Volver", callback_data="back_to_main")]
        ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()