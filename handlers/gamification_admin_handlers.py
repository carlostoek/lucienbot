"""
Handlers de Gamificación para Administradores - Lucien Bot

Handlers para configuración de gamificación desde el panel de admin.
"""
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config.settings import bot_config
from services.broadcast_service import BroadcastService
from services.daily_gift_service import DailyGiftService
from services.channel_service import ChannelService
from keyboards.inline_keyboards import (
    back_keyboard, confirmation_keyboard, cancel_keyboard,
    admin_menu_keyboard
)
from utils.lucien_voice import LucienVoice
import logging

logger = logging.getLogger(__name__)
router = Router()


# Función helper para verificar admin
def is_admin(user_id: int) -> bool:
    return user_id in bot_config.ADMIN_IDS


# Estados para FSM
class BroadcastStates(StatesGroup):
    waiting_text = State()
    waiting_attachment_decision = State()
    waiting_attachment = State()
    waiting_reaction_decision = State()
    selecting_reactions = State()
    waiting_protection_decision = State()
    confirming = State()


class EmojiConfigStates(StatesGroup):
    waiting_emoji = State()
    waiting_name = State()
    waiting_value = State()


class DailyGiftConfigStates(StatesGroup):
    waiting_amount = State()


# ==================== MENÚ DE GAMIFICACIÓN ADMIN ====================

@router.callback_query(F.data == "admin_gamification", lambda cb: is_admin(cb.from_user.id))
async def admin_gamification_menu(callback: CallbackQuery):
    """Menú principal de gamificación para admins"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="💋 Configurar besitos",
            callback_data="config_besitos"
        )],
        [InlineKeyboardButton(
            text="📢 Enviar broadcast",
            callback_data="send_broadcast"
        )],
        [InlineKeyboardButton(
            text="🎁 Configurar regalo diario",
            callback_data="config_daily_gift"
        )],
        [InlineKeyboardButton(
            text="📊 Estadísticas",
            callback_data="gamification_stats"
        )],
        [InlineKeyboardButton(
            text="🔙 Volver al sanctum",
            callback_data="back_to_admin"
        )]
    ])
    
    await callback.message.edit_text(
        f"""🎩 <b>Lucien:</b>

<i>El sistema de recompensas que cultiva devoción...</i>

¿Qué aspecto de la gamificación desea calibrar?""",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# ==================== CONFIGURAR BESITOS / EMOJIS ====================

@router.callback_query(F.data == "config_besitos", lambda cb: is_admin(cb.from_user.id))
async def config_besitos_menu(callback: CallbackQuery):
    """Menú de configuración de besitos y emojis"""
    broadcast_service = BroadcastService()
    emojis = broadcast_service.get_all_emojis(active_only=False)
    
    text = f"""🎩 <b>Lucien:</b>

<i>Los fragmentos de atención que Diana otorga...</i>

📋 <b>Emojis configurados:</b>

"""
    
    keyboard_buttons = []
    
    for emoji in emojis:
        status = "✅" if emoji.is_active else "❌"
        text += f"{status} {emoji.emoji} = {emoji.besito_value} besitos"
        if emoji.name:
            text += f" ({emoji.name})"
        text += "\n"
        
        keyboard_buttons.append([InlineKeyboardButton(
            text=f"{emoji.emoji} Editar",
            callback_data=f"edit_emoji_{emoji.id}"
        )])
    
    keyboard_buttons.extend([
        [InlineKeyboardButton(
            text="➕ Agregar emoji",
            callback_data="add_emoji"
        )],
        [InlineKeyboardButton(
            text="🔙 Volver",
            callback_data="admin_gamification"
        )]
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "add_emoji", lambda cb: is_admin(cb.from_user.id))
async def add_emoji_start(callback: CallbackQuery, state: FSMContext):
    """Inicia el flujo de agregar emoji"""
    await callback.message.edit_text(
        f"""🎩 <b>Lucien:</b>

<i>Vamos a configurar un nuevo emoji de reacción...</i>

📋 <b>Paso 1 de 3:</b> Envíe el emoji que desea agregar.

Ejemplos: 💋 ❤️ 🔥 👍""",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(EmojiConfigStates.waiting_emoji)
    await callback.answer()


@router.message(EmojiConfigStates.waiting_emoji)
async def process_emoji(message: Message, state: FSMContext):
    """Procesa el emoji ingresado"""
    emoji_char = message.text.strip()
    
    # Validar que sea un solo emoji (aproximado)
    if len(emoji_char) > 2:
        await message.answer(
            f"🎩 <b>Lucien:</b>\n\n"
            f"<i>Por favor, envíe solo un emoji...</i>",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML"
        )
        return
    
    await state.update_data(emoji=emoji_char)

    await message.answer(
        f"""🎩 <b>Lucien:</b>

<i>Excelente. Ahora un nombre descriptivo...</i>

📋 <b>Paso 2 de 3:</b> Nombre del emoji

Ejemplo: 'Beso', 'Corazón', 'Fuego'""",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(EmojiConfigStates.waiting_name)


@router.message(EmojiConfigStates.waiting_name)
async def process_emoji_name(message: Message, state: FSMContext):
    """Procesa el nombre del emoji"""
    name = message.text.strip()
    await state.update_data(name=name)
    
    await message.answer(
        f"""🎩 <b>Lucien:</b>

<i>Finalmente, el valor en besitos...</i>

📋 <b>Paso 3 de 3:</b> Valor de besitos

Ejemplo: <code>5</code> para 5 besitos""",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(EmojiConfigStates.waiting_value)


@router.message(EmojiConfigStates.waiting_value)
async def process_emoji_value(message: Message, state: FSMContext):
    """Procesa el valor y crea el emoji"""
    try:
        value = int(message.text.strip())
        if value <= 0:
            raise ValueError("Valor debe ser positivo")
    except ValueError:
        await message.answer(
            f"🎩 <b>Lucien:</b>\n\n"
            f"<i>Por favor, indique un número válido mayor a cero...</i>",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML"
        )
        return
    
    data = await state.get_data()
    
    broadcast_service = BroadcastService()
    
    try:
        emoji = broadcast_service.create_reaction_emoji(
            emoji=data['emoji'],
            name=data['name'],
            besito_value=value
        )
        
        await message.answer(
            f"""🎩 <b>Lucien:</b>

<i>El emoji ha sido registrado en los archivos de Diana...</i>

✅ <b>Emoji configurado:</b>
   • Emoji: {emoji.emoji}
   • Nombre: {emoji.name}
   • Valor: {emoji.besito_value} besitos

<i>Los visitantes podrán usarlo en las reacciones.</i>""",
            reply_markup=back_keyboard("config_besitos"),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error creando emoji: {e}")
        await message.answer(
            LucienVoice.error_message("la configuración del emoji"),
            reply_markup=back_keyboard("config_besitos"),
            parse_mode="HTML"
        )
    
    await state.clear()


@router.callback_query(F.data.startswith("edit_emoji_"), lambda cb: is_admin(cb.from_user.id))
async def edit_emoji(callback: CallbackQuery):
    """Editar un emoji existente"""
    emoji_id = int(callback.data.replace("edit_emoji_", ""))
    
    broadcast_service = BroadcastService()
    emoji = broadcast_service.get_reaction_emoji(emoji_id)
    
    if not emoji:
        await callback.answer("Emoji no encontrado", show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"Valor: {emoji.besito_value} besitos",
            callback_data=f"change_emoji_value_{emoji_id}"
        )],
        [InlineKeyboardButton(
            text=f"{'Desactivar' if emoji.is_active else 'Activar'}",
            callback_data=f"toggle_emoji_{emoji_id}"
        )],
        [InlineKeyboardButton(
            text="🗑️ Eliminar",
            callback_data=f"delete_emoji_{emoji_id}"
        )],
        [InlineKeyboardButton(
            text="🔙 Volver",
            callback_data="config_besitos"
        )]
    ])
    
    status = "✅ Activo" if emoji.is_active else "❌ Inactivo"
    
    await callback.message.edit_text(
        f"""🎩 <b>Lucien:</b>

<i>Editando emoji...</i>

{emoji.emoji} <b>{emoji.name or 'Sin nombre'}</b>
   • Valor: {emoji.besito_value} besitos
   • Estado: {status}

<i>¿Qué desea modificar?</i>""",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_emoji_"), lambda cb: is_admin(cb.from_user.id))
async def toggle_emoji(callback: CallbackQuery):
    """Activa/desactiva un emoji"""
    emoji_id = int(callback.data.replace("toggle_emoji_", ""))
    
    broadcast_service = BroadcastService()
    success = broadcast_service.toggle_emoji(emoji_id)
    
    if success:
        await callback.answer("Estado actualizado")
        await edit_emoji(callback)
    else:
        await callback.answer("Error al actualizar", show_alert=True)


# ==================== CONFIGURAR REGALO DIARIO ====================

@router.callback_query(F.data == "config_daily_gift", lambda cb: is_admin(cb.from_user.id))
async def config_daily_gift(callback: CallbackQuery):
    """Configuración del regalo diario"""
    gift_service = DailyGiftService()
    config = gift_service.get_config()
    
    status = "✅ Activo" if config.is_active else "❌ Inactivo"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"Cantidad: {config.besito_amount} besitos",
            callback_data="change_gift_amount"
        )],
        [InlineKeyboardButton(
            text=f"{'Desactivar' if config.is_active else 'Activar'}",
            callback_data="toggle_daily_gift"
        )],
        [InlineKeyboardButton(
            text="🔙 Volver",
            callback_data="admin_gamification"
        )]
    ])
    
    await callback.message.edit_text(
        f"""🎩 <b>Lucien:</b>

<i>La generosidad diaria de Diana...</i>

🎁 <b>Configuración del Regalo Diario:</b>
   • Cantidad: {config.besito_amount} besitos
   • Estado: {status}

<i>Los visitantes pueden reclamar esto una vez cada 24 horas.</i>""",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "change_gift_amount", lambda cb: is_admin(cb.from_user.id))
async def change_gift_amount_start(callback: CallbackQuery, state: FSMContext):
    """Inicia cambio de cantidad del regalo"""
    await callback.message.edit_text(
        f"""🎩 <b>Lucien:</b>

<i>¿Cuántos besitos otorgará Diana cada día?</i>

📋 Indique la cantidad de besitos para el regalo diario:

Ejemplo: <code>15</code>""",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(DailyGiftConfigStates.waiting_amount)
    await callback.answer()


@router.message(DailyGiftConfigStates.waiting_amount)
async def process_gift_amount(message: Message, state: FSMContext):
    """Procesa la nueva cantidad"""
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            raise ValueError("Cantidad debe ser positiva")
    except ValueError:
        await message.answer(
            f"🎩 <b>Lucien:</b>\n\n"
            f"<i>Por favor, indique un número válido mayor a cero...</i>",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML"
        )
        return
    
    gift_service = DailyGiftService()
    gift_service.update_config(amount, admin_id=message.from_user.id)
    
    await message.answer(
        f"""🎩 <b>Lucien:</b>

<i>La generosidad de Diana ha sido ajustada...</i>

✅ <b>Regalo diario actualizado:</b> {amount} besitos

<i>Los visitantes recibirán esta cantidad al reclamar.</i>""",
        reply_markup=back_keyboard("config_daily_gift"),
        parse_mode="HTML"
    )
    await state.clear()


@router.callback_query(F.data == "toggle_daily_gift", lambda cb: is_admin(cb.from_user.id))
async def toggle_daily_gift(callback: CallbackQuery):
    """Activa/desactiva el regalo diario"""
    gift_service = DailyGiftService()
    config = gift_service.get_config()
    
    # Toggle
    config.is_active = not config.is_active
    gift_service.db.commit()
    
    status = "activado" if config.is_active else "desactivado"
    await callback.answer(f"Regalo diario {status}")
    await config_daily_gift(callback)


# ==================== ESTADÍSTICAS ====================

@router.callback_query(F.data == "gamification_stats", lambda cb: is_admin(cb.from_user.id))
async def gamification_stats(callback: CallbackQuery):
    """Estadísticas de gamificación"""
    from services.besito_service import BesitoService
    from services.daily_gift_service import DailyGiftService
    
    besito_service = BesitoService()
    gift_service = DailyGiftService()
    
    total_besitos = besito_service.get_total_besitos_in_circulation()
    top_users = besito_service.get_top_users(limit=5)
    claims_today = gift_service.get_total_claims_today()
    besitos_given_today = gift_service.get_total_besitos_given_today()
    
    text = f"""🎩 <b>Lucien:</b>

<i>Los patrones de la devoción acumulada...</i>

📊 <b>Estadísticas de Gamificación:</b>

💋 <b>Besitos en circulación:</b> {total_besitos}

🎁 <b>Regalos hoy:</b>
   • Reclamos: {claims_today}
   • Besitos entregados: {besitos_given_today}

🏆 <b>Top visitantes:</b>
"""
    
    for i, user in enumerate(top_users, 1):
        text += f"   {i}. ID:{user.user_id} - {user.balance} besitos\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=back_keyboard("admin_gamification"),
        parse_mode="HTML"
    )
    await callback.answer()
