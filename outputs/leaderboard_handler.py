"""
Handlers de Leaderboard - Lucien Bot

Handlers thin que only routing events to LeaderboardService.
SIN lógica de negocio, SIN acceso directo a DB.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from services.leaderboard_service import LeaderboardService
from keyboards.inline_keyboards import back_keyboard
from utils.lucien_voice import LucienVoice
import logging

logger = logging.getLogger(__name__)
router = Router()


# ==================== LEADERBOARD MENU ====================

@router.callback_query(F.data == "leaderboard:menu")
async def leaderboard_menu(callback: CallbackQuery):
    """Menú principal del leaderboard"""
    user_id = callback.from_user.id

    leaderboard_service = LeaderboardService()
    try:
        top_users = leaderboard_service.get_top_users(limit=10)
        user_rank_info = leaderboard_service.get_user_rank(user_id)
    finally:
        leaderboard_service.close()

    # Construir texto del leaderboard
    if top_users:
        lines = ["🏆 <b>Top Besitos</b>\n"]
        medals = ["🥇", "🥈", "🥉"]

        for entry in top_users:
            rank = entry['rank']
            if rank <= 3:
                emoji = medals[rank - 1]
            elif rank <= 10:
                emoji = f"#{rank}"
            else:
                emoji = f"#{rank}"

            user_display = f"Visitante {entry['user_id']}"
            if entry['user_id'] == user_id:
                user_display = f"<b>Tú</b>"

            lines.append(f"{emoji} {user_display}: {entry['balance']} 💋")

        top_text = "\n".join(lines)
    else:
        top_text = "<i>Aún no hay visitantes en el leaderboard...</i>"

    # Posición del usuario
    if user_rank_info:
        rank_text = f"\n📍 Tu posición: <b>#{user_rank_info['rank']}</b> con {user_rank_info['balance']} 💋"
    else:
        rank_text = "\n📍 Aún no tienes besitos registrados."

    text = f"""🎩 <b>Lucien:</b>

<i>La corte de Diana tiene su registro de devotion...</i>

{top_text}
{rank_text}

<i>Demuestra tu compromiso y escala posiciones...</i>"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Mi Ranking", callback_data="leaderboard:my_rank")],
        [InlineKeyboardButton(text="👥 Cerca de Mí", callback_data="leaderboard:nearby")],
        [InlineKeyboardButton(text="🔙 Volver", callback_data="back_to_main")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "leaderboard:my_rank")
async def show_my_rank(callback: CallbackQuery):
    """Muestra el ranking detallado del usuario"""
    user_id = callback.from_user.id

    leaderboard_service = LeaderboardService()
    try:
        rank_info = leaderboard_service.get_user_rank(user_id)
        nearby = leaderboard_service.get_users_around_rank(user_id, range_=2)
    finally:
        leaderboard_service.close()

    if not rank_info:
        text = f"""🎩 <b>Lucien:</b>

<i>No tienes besitos registrados aún...</i>

💋 <b>Tu posición:</b> No clasificado

<i>Interactúa más con el reino para aparecer en el leaderboard.</i>"""
    else:
        # Construir tabla de usuarios cercanos
        lines = []
        medals = ["🥇", "🥈", "🥉"]

        for entry in nearby:
            rank = entry['rank']
            emoji = medals[rank - 1] if rank <= 3 else f"#{rank}"
            marker = " 👑" if entry.get('is_current_user') else ""
            lines.append(f"{emoji} {entry['user_id']}: {entry['balance']} 💋{marker}")

        nearby_text = "\n".join(lines) if lines else "No hay usuarios cercanos"

        text = f"""🎩 <b>Lucien:</b>

<i>El lugar que ocupas en la corte de Diana...</i>

📍 <b>Tu posición:</b> #{rank_info['rank']}
💋 <b>Besitos:</b> {rank_info['balance']}
📈 <b>Total ganado:</b> {rank_info['total_earned']}

<b>Alrededores:</b>
{nearby_text}

<i>La competencia es feroz entre los devotos...</i>"""

    await callback.message.edit_text(
        text,
        reply_markup=back_keyboard("leaderboard:menu"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "leaderboard:nearby")
async def show_nearby_leaderboard(callback: CallbackQuery):
    """Muestra usuarios cercanos en el ranking"""
    user_id = callback.from_user.id

    leaderboard_service = LeaderboardService()
    try:
        nearby = leaderboard_service.get_users_around_rank(user_id, range_=3)
    finally:
        leaderboard_service.close()

    if not nearby:
        text = f"""🎩 <b>Lucien:</b>

<i>No hay ranking cercano que mostrar...</i>

💋 Asegúrate de tener besitos acumulados.

<i>Vuelve cuando hayas interactuado más.</i>"""
    else:
        lines = ["👥 <b>Usuarios Cercanos</b>\n"]
        medals = ["🥇", "🥈", "🥉"]

        for entry in nearby:
            rank = entry['rank']
            emoji = medals[rank - 1] if rank <= 3 else f"#{rank}"
            marker = " ← Tú" if entry.get('is_current_user') else ""
            lines.append(f"{emoji} {entry['user_id']}: {entry['balance']} 💋{marker}")

        nearby_text = "\n".join(lines)

        text = f"""🎩 <b>Lucien:</b>

<i>Los devotos más cercanos a tu posición...</i>

{nearby_text}

<i>¡Sigue acumulando para superarlos!</i>"""

    await callback.message.edit_text(
        text,
        reply_markup=back_keyboard("leaderboard:menu"),
        parse_mode="HTML"
    )
    await callback.answer()