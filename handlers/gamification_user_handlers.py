"""
Handlers de Gamificación para Usuarios - Lucien Bot

Handlers para funcionalidades de gamificación accesibles por usuarios.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from services.besito_service import BesitoService
from services.daily_gift_service import DailyGiftService
from services.broadcast_service import BroadcastService
from keyboards.inline_keyboards import back_keyboard, main_menu_keyboard
from utils.lucien_voice import LucienVoice
import asyncio
import random
import logging

logger = logging.getLogger(__name__)
router = Router()

# Deduplication set for reaction callbacks (prevents duplicate processing from Telegram retries)
_reaction_callbacks_being_processed = set()

# Cooldown for dice game per user (prevents rate limit issues)
_dice_game_cooldown: dict[int, float] = {}
_DICE_COOLDOWN_SECONDS = 3  # Minimum seconds between dice games


# ==================== CONSULTAR SALDO ====================

@router.callback_query(F.data == "my_balance")
async def show_balance(callback: CallbackQuery):
    """Muestra el saldo de besitos del usuario"""
    user_id = callback.from_user.id
    
    besito_service = BesitoService()
    stats = besito_service.get_balance_with_stats(user_id)
    
    text = f"""🎩 <b>Lucien:</b>

<i>Permíteme consultar los fragmentos de atención que ha acumulado...</i>

💋 <b>Tu saldo de besitos:</b> {stats['balance']}

📊 <b>Estadísticas:</b>
   • Total acumulado: {stats['total_earned']}
   • Total gastado: {stats['total_spent']}

<i>Diana aprecia cada momento de su atención...</i>"""
    
    await callback.message.edit_text(
        text,
        reply_markup=back_keyboard("back_to_main"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "transaction_history")
async def show_transaction_history(callback: CallbackQuery):
    """Muestra el historial de transacciones"""
    user_id = callback.from_user.id
    
    besito_service = BesitoService()
    transactions = besito_service.get_transaction_history(user_id, limit=10)
    
    if not transactions:
        text = f"""🎩 <b>Lucien:</b>

<i>Aún no hay movimientos registrados en su cuenta...</i>

💋 <b>Tu historial está vacío.</b>

<i>Interactúe más con el reino para acumular besitos.</i>"""
    else:
        text = f"""🎩 <b>Lucien:</b>

<i>Los movimientos de su moneda especial...</i>

📋 <b>Últimas transacciones:</b>

"""
        for tx in transactions:
            emoji = "💚" if tx.amount > 0 else "💔"
            date_str = tx.created_at.strftime("%d/%m %H:%M") if tx.created_at else "?"
            source_name = {
                "reaction": "Reacción",
                "daily_gift": "Regalo diario",
                "mission": "Misión",
                "purchase": "Compra",
                "admin": "Admin"
            }.get(tx.source.value, tx.source.value)
            
            text += f"{emoji} <b>{'+' if tx.amount > 0 else ''}{tx.amount}</b> - {source_name}\n"
            text += f"   <i>{date_str}</i>\n\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=back_keyboard("my_balance"),
        parse_mode="HTML"
    )
    await callback.answer()


# ==================== REGALO DIARIO ====================

@router.callback_query(F.data == "daily_gift")
async def daily_gift_menu(callback: CallbackQuery):
    """Menú del regalo diario"""
    user_id = callback.from_user.id
    
    gift_service = DailyGiftService()
    can_claim, time_remaining, message = gift_service.can_claim(user_id)
    
    if can_claim:
        amount = gift_service.get_gift_amount()
        text = f"""🎩 <b>Lucien:</b>

<i>Diana tiene un obsequio especial para usted hoy...</i>

🎁 <b>Regalo Diario Disponible</b>

💋 <b>Cantidad:</b> {amount} besitos

<i>¿Desea reclamar su regalo?</i>"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎁 Reclamar regalo", callback_data="claim_gift")],
            [InlineKeyboardButton(text="🔙 Volver", callback_data="back_to_main")]
        ])
    else:
        text = f"""🎩 <b>Lucien:</b>

<i>La generosidad de Diana tiene sus tiempos...</i>

⏳ <b>Regalo Diario</b>

{message}

<i>Vuelva más tarde para recibir su próximo obsequio.</i>"""
        
        keyboard = back_keyboard("back_to_main")
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "claim_gift")
async def claim_daily_gift(callback: CallbackQuery):
    """Procesa el reclamo del regalo diario"""
    user_id = callback.from_user.id
    
    gift_service = DailyGiftService()
    success, amount, message = gift_service.claim_gift(user_id)
    
    if success:
        text = f"""🎩 <b>Lucien:</b>

<i>Diana se complace con su dedicación...</i>

✅ <b>¡Regalo reclamado!</b>

{message}

<i>Mañana habrá más besitos esperándole...</i>"""
    else:
        text = f"""🎩 <b>Lucien:</b>

<i>Hmm... algo ocurrió con su solicitud...</i>

⚠️ {message}"""
    
    await callback.message.edit_text(
        text,
        reply_markup=back_keyboard("back_to_main"),
        parse_mode="HTML"
    )
    await callback.answer()


# ==================== REACCIONES A BROADCAST ====================

@router.callback_query(F.data.startswith("react_"))
async def handle_reaction(callback: CallbackQuery):
    """Maneja las reacciones a mensajes de broadcast y actualiza conteos"""
    user = callback.from_user

    # Parsear datos: react_{broadcast_id}_{emoji_id}
    parts = callback.data.split("_")
    if len(parts) != 3:
        await callback.answer("Error en la reacción", show_alert=True)
        return

    try:
        broadcast_id = int(parts[1])
        emoji_id = int(parts[2])
    except ValueError:
        await callback.answer("Error en la reacción", show_alert=True)
        return

    # Deduplication key para prevenir procesamiento duplicado
    dedup_key = f"{user.id}:{broadcast_id}:{emoji_id}"

    # Verificar si ya estamos procesando este callback (race condition protection)
    if dedup_key in _reaction_callbacks_being_processed:
        logger.debug(f"Callback duplicado ignorado: {dedup_key}")
        await callback.answer("Procesando tu reacción...", show_alert=False)
        return

    # Marcar como en proceso
    _reaction_callbacks_being_processed.add(dedup_key)

    try:
        broadcast_service = BroadcastService()

        # Registrar reacción con entrega automática de recompensas (verificación y registro atómico)
        reaction = await broadcast_service.check_and_register_reaction(
            broadcast_id=broadcast_id,
            user_id=user.id,
            emoji_id=emoji_id,
            username=user.username,
            bot=callback.bot
        )

        if reaction:
            # reaction ahora es un diccionario, usar los datos directamente
            emoji_char = reaction.get('emoji_char', '💋')
            besitos = reaction.get('besitos_awarded', 0)

            # Obtener el broadcast para actualizar el mensaje
            broadcast = broadcast_service.get_broadcast(broadcast_id)
            if broadcast and broadcast.has_reactions:
                # Obtener TODOS los emojis originales del broadcast
                selected_emoji_ids = broadcast_service.get_selected_emoji_ids(broadcast_id)

                # Obtener conteo actualizado de reacciones
                reactions = broadcast_service.get_reactions_by_broadcast(broadcast_id)

                # Contar reacciones por emoji
                emoji_counts = {}
                for r in reactions:
                    if r.reaction_emoji:
                        emoji_id_val = r.reaction_emoji.id
                        emoji_counts[emoji_id_val] = emoji_counts.get(emoji_id_val, 0) + 1

                # Reconstruir el teclado con TODOS los emojis originales (con o sin conteo)
                buttons = []
                for emoji_id in selected_emoji_ids:
                    emoji_obj = broadcast_service.get_reaction_emoji(emoji_id)
                    if emoji_obj:
                        count = emoji_counts.get(emoji_id, 0)
                        # Mostrar el emoji con el conteo (o solo el emoji si no hay conteo)
                        text = f"{emoji_obj.emoji} {count}" if count > 0 else emoji_obj.emoji
                        buttons.append(InlineKeyboardButton(
                            text=text,
                            callback_data=f"react_{broadcast_id}_{emoji_id}"
                        ))

                if buttons:
                    new_markup = InlineKeyboardMarkup(inline_keyboard=[buttons])  # Una sola fila
                    try:
                        await callback.bot.edit_message_reply_markup(
                            chat_id=broadcast.channel_id,
                            message_id=broadcast.message_id,
                            reply_markup=new_markup
                        )
                    except Exception as e:
                        logger.warning(f"No se pudo actualizar conteo en mensaje: {e}")

            # Solo notificar via callback (sin mensaje privado)
            await callback.answer(f"¡+{besitos} besitos! 💋")
        else:
            await callback.answer("Ya reaccionaste a este mensaje", show_alert=True)

    finally:
        # Siempre remover el dedup key al finalizar
        _reaction_callbacks_being_processed.discard(dedup_key)


# ==================== MINIJUEGOS ====================

import random


@router.callback_query(F.data == "minigames")
async def minigames_menu(callback: CallbackQuery):
    """Menú de minijuegos"""
    text = f"""🎩 <b>Lucien:</b>

<i>¿Busca un momento de entretenimiento?</i>

🎲 <b>Minijuegos</b>

<b>🎲 Dados de Diana</b>
<i>Lance dos dados:</i>
• Si caen <b>ambos pares</b> (2,4,6) → ¡Ganas 1 besito!
• Si caen <b>dobles</b> (mismo número) → ¡Ganas 1 besito!
• Probabilidad de victoria: ~33%

<i>¿Se siente con suerte?</i>"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Lanzar dados", callback_data="dice_game")],
        [InlineKeyboardButton(text="🔙 Volver", callback_data="back_to_main")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "dice_game")
async def dice_game(callback: CallbackQuery):
    """Juego de dados con dos dados - cooldown interno para evitar rate limits"""
    user_id = callback.from_user.id
    import time

    logger.info(f"[dice_game] Handler called for user {user_id}")

    # Verificar cooldown ANTES de enviar dados
    now = time.monotonic()
    if user_id in _dice_game_cooldown:
        elapsed = now - _dice_game_cooldown[user_id]
        if elapsed < _DICE_COOLDOWN_SECONDS:
            remaining = int(_DICE_COOLDOWN_SECONDS - elapsed)
            await callback.answer(
                f"🎩 Lucien:\n\n"
                f"<i>Calma, visitante...</i>\n\n"
                f"Espera {remaining} segundos antes de volver a lanzar.",
                show_alert=True
            )
            return

    # Actualizar cooldown
    _dice_game_cooldown[user_id] = now

    # Lanzar dos dados (valores aleatorios 1-6)
    value1 = random.randint(1, 6)
    value2 = random.randint(1, 6)
    logger.info(f"[dice_game] Dice values: {value1}, {value2} for user {user_id}")

    # Verificar victoria: ambos pares o ambos iguales
    dice1_even = value1 % 2 == 0
    dice2_even = value2 % 2 == 0
    is_double = value1 == value2
    is_win = (dice1_even and dice2_even) or is_double

    if is_win:
        besito_service = BesitoService()
        besito_service.add_besitos(user_id, 1, source="dice_game")
        result_text = "✨ <b>¡Victoria!</b>"
    else:
        result_text = "💫 <b>No fue esta vez...</b>"

    # Formatear dados
    dice_faces = {
        1: "⚀", 2: "⚁", 3: "⚂",
        4: "⚃", 5: "⚄", 6: "⚅"
    }
    dice_str = f"{dice_faces[value1]} {dice_faces[value2]}"

    if is_double:
        condition = "¡Dobles!"
    elif dice1_even and dice2_even:
        condition = "¡Ambos pares!"
    else:
        condition = "Inténtalo de nuevo"

    text = f"""🎩 <b>Lucien:</b>

<i>Los dados han sido lanzados...</i>

🎲 <b>Dados de Diana</b>

{dice_str}

{result_text}

<i>{condition}</i>

{'💋 <b>+1 besito</b> añadido a tu saldo' if is_win else '<i>Vuelve a intentarlo...</i>'}"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Lanzar de nuevo", callback_data="dice_game")],
        [InlineKeyboardButton(text="🎲 Ver otros juegos", callback_data="minigames")],
        [InlineKeyboardButton(text="🔙 Volver", callback_data="back_to_main")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer(f"+1 besito" if is_win else "Intenta de nuevo")



