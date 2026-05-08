"""
Handlers de Trivia Discount para Usuarios - Lucien Bot

FSM de juego para trivia de descuentos con sistema de rachas.
Flow: idle → waiting_answer → (streak_choice if threshold | game_over if wrong)
                              ↓
                        waiting_retire → idle
"""
import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from services import get_service
from services.game_service import GameService
from services.trivia_discount_service import TriviaDiscountService

logger = logging.getLogger(__name__)
router = Router()


# Estados FSM para Trivia Discount
class TriviaStreakStates(StatesGroup):
    waiting_answer = State()   # Jugador respondiendo pregunta
    streak_choice = State()    # Alcanzó threshold, elige retiro/continuar
    waiting_retire = State()   # Jugador eligió retiro, procesando código


# ==================== MENU PRINCIPAL ====================

@router.callback_query(F.data == "trivia_discount_menu")
async def trivia_discount_menu(callback: CallbackQuery):
    """Punto de entrada mostrando promoción disponible, racha actual, jugadas restantes"""
    user_id = callback.from_user.id

    with get_service(GameService) as service:
        data = service.get_trivia_discount_entry_data(user_id)

    if not data.get('can_play'):
        promotion_name = "Trivia del Destino"
        text = (
            f"🎰 <b>{promotion_name}</b>\n\n"
            f"<i>No hay promoción activa o ha agotado sus jugadas por hoy.</i>\n\n"
            f"🔄 <i>Regrese mañana para nuevas oportunidades.</i>"
        )
        buttons = [[InlineKeyboardButton(text="🔙 Volver", callback_data="back_to_main")]]
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        await callback.answer()
        return

    # Construir info de tiers
    tier_lines = []
    for tier in data.get('tier_info', []):
        pct = tier['discount_percentage']
        threshold = tier['streak_threshold']
        available = tier['available_codes']
        tier_lines.append(
            f"   🏷️ {pct}% descuento — {threshold} aciertos — {available} códigos"
        )
    tiers_text = "\n".join(tier_lines) if tier_lines else ""

    streak_text = ""
    if data['current_streak'] > 0:
        streak_text = f"\n🔥 <b>Racha actual:</b> {data['current_streak']}"

    text = (
        f"🎰 <b>{data['title']}</b>{streak_text}\n\n"
        f"<i>{data['intro']}</i>\n\n"
        f"📊 <b>Oportunidades:</b> {data['remaining']} de {data['limit']}\n\n"
        f"🏆 <b>Tiers de descuento:</b>\n{tiers_text}\n\n"
        f"<i>¿Desea probar su suerte?</i>"
    )

    buttons = [
        [InlineKeyboardButton(text="🎮 Jugar Trivia", callback_data="start_trivia_discount")],
        [InlineKeyboardButton(text="🔙 Volver", callback_data="back_to_main")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()
    logger.info(f"trivia_discount_user_handlers - trivia_discount_menu - {user_id} - shown")


# ==================== INICIAR JUEGO ====================

@router.callback_query(F.data == "start_trivia_discount")
async def start_trivia_discount(callback: CallbackQuery, state: FSMContext):
    """Inicia juego, muestra primera pregunta, setea FSM a waiting_answer"""
    user_id = callback.from_user.id

    with get_service(GameService) as service:
        can_play, _, _, limit_msg = service.can_play_trivia_discount(user_id)

        if not can_play:
            text = f"🎰 <b>Trivia del Destino</b>\n\n<i>{limit_msg}</i>\n\n🔄 Regresa mañana."
            buttons = [[InlineKeyboardButton(text="🔙 Menú", callback_data="trivia_discount_menu")]]
            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
            await callback.answer()
            return

        question, question_idx = service.get_random_trivia_question()

        if question is None:
            text = "🎰 <b>Trivia del Destino</b>\n\n<i>Las preguntas están en el taller de Lucien. Regresa más tarde.</i>"
            buttons = [[InlineKeyboardButton(text="🔙 Menú", callback_data="trivia_discount_menu")]]
            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
            await callback.answer()
            return

    # Guardar estado en FSM
    await state.update_data(
        question_id=question.id,
        question_idx=question_idx,
        current_streak=0
    )

    text = (
        f"🎰 <b>Trivia del Destino</b>\n\n"
        f"<i>Responde correctamente para acumular tu racha.</i>\n\n"
        f"❓ <b>Pregunta:</b>\n{question.question_text}"
    )

    keyboard = trivia_discount_question_keyboard(question)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await state.set_state(TriviaStreakStates.waiting_answer)
    await callback.answer()
    logger.info(f"trivia_discount_user_handlers - start_trivia_discount - {user_id} - started, q:{question_idx}")


# ==================== PROCESAR RESPUESTA ====================

@router.callback_query(TriviaStreakStates.waiting_answer, F.data.startswith("trivia_discount_answer_"))
async def process_trivia_answer(callback: CallbackQuery, state: FSMContext):
    """Maneja callback de respuesta (trivia_discount_answer_{idx}_{question_id}), verifica, actualiza racha"""
    user_id = callback.from_user.id

    # Parsear callback: trivia_discount_answer_{idx}_{question_id}
    parts = callback.data.split("_")
    answer_idx = int(parts[3])  # A=0, B=1, C=2, D=3
    question_id = int(parts[4])
    answer_letter = ["A", "B", "C", "D"][answer_idx]

    with get_service(GameService) as service:
        result = service.process_trivia_answer(user_id, question_id, answer_letter)

    # Obtener datos de FSM
    fsm_data = await state.get_data()
    previous_streak = fsm_data.get('current_streak', 0)

    if result['correct']:
        new_streak = result['new_streak']
        tier_reached = result.get('tier_reached')

        # Actualizar FSM
        await state.update_data(current_streak=new_streak)

        if tier_reached:
            # Alcanzó un tier → mostrar opciones de retiro
            discount = tier_reached['discount_percentage']
            threshold = tier_reached['streak_threshold']

            text = (
                f"🎰 <b>¡Racha de {new_streak}!</b>\n\n"
                f"🔥 Ha alcanzado el tier de <b>{discount}% de descuento</b>\n"
                f"<i>con {threshold} aciertos consecutivos.</i>\n\n"
                f"¿Qué desea hacer?"
            )

            keyboard = streak_choice_keyboard(discount)
            await state.set_state(TriviaStreakStates.streak_choice)

            await callback.message.edit_text(text, reply_markup=keyboard)
            await callback.answer()
            logger.info(
                f"trivia_discount_user_handlers - process_trivia_answer - {user_id} - "
                f"correct, streak:{new_streak}, tier_reached:{discount}%"
            )
        else:
            # Respuesta correcta pero sin tier aún → siguiente pregunta
            await show_next_question(callback, state, user_id, new_streak)

    else:
        # Respuesta incorrecta → game over
        await state.update_data(current_streak=0)
        await state.set_state(TriviaStreakStates.waiting_answer)

        text = (
            f"🎰 <b>¡Fin del juego!</b>\n\n"
            f"<i>La respuesta era incorrecta.</i>\n\n"
            f"🔢 Su racha terminó en <b>{previous_streak}</b>\n\n"
            f"<i>¿Desea intentarlo de nuevo?</i>"
        )

        buttons = [
            [InlineKeyboardButton(text="🔄 Jugar de nuevo", callback_data="start_trivia_discount")],
            [InlineKeyboardButton(text="🔙 Menú", callback_data="trivia_discount_menu")]
        ]
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        await callback.answer()
        logger.info(
            f"trivia_discount_user_handlers - process_trivia_answer - {user_id} - "
            f"wrong, final_streak:{previous_streak}"
        )


async def show_next_question(callback: CallbackQuery, state: FSMContext, user_id: int, streak: int):
    """Muestra siguiente pregunta después de respuesta correcta sin tier"""
    with get_service(GameService) as service:
        can_play, _, _, _ = service.can_play_trivia_discount(user_id)

        if not can_play:
            text = (
                f"🎰 <b>¡Juego terminado!</b>\n\n"
                f"🔥 Alcanzó una racha de <b>{streak}</b>\n\n"
                f"<i>Ha agotado sus oportunidades por hoy.</i>"
            )
            buttons = [[InlineKeyboardButton(text="🔙 Menú", callback_data="trivia_discount_menu")]]
            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
            await state.set_state(TriviaStreakStates.waiting_answer)
            await callback.answer()
            return

        question, question_idx = service.get_random_trivia_question()

        if question is None:
            text = (
                f"🎰 <b>¡Juego terminado!</b>\n\n"
                f"🔥 Racha final: <b>{streak}</b>\n\n"
                f"<i>Las preguntas están en el taller de Lucien. Regresa más tarde.</i>"
            )
            buttons = [[InlineKeyboardButton(text="🔙 Menú", callback_data="trivia_discount_menu")]]
            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
            await state.set_state(TriviaStreakStates.waiting_answer)
            await callback.answer()
            return

        await state.update_data(question_id=question.id, question_idx=question_idx)

    text = (
        f"🎰 <b>Trivia del Destino</b>\n\n"
        f"🔥 Racha: <b>{streak}</b>\n\n"
        f"❓ <b>Pregunta:</b>\n{question.question_text}"
    )

    keyboard = trivia_discount_question_keyboard(question)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await state.set_state(TriviaStreakStates.waiting_answer)
    await callback.answer()
    logger.info(f"trivia_discount_user_handlers - show_next_question - {user_id} - streak:{streak}, q:{question_idx}")


# ==================== STREAK CHOICE (THRESHOLD ALCANZADO) ====================

@router.callback_query(TriviaStreakStates.streak_choice, F.data == "trivia_continue")
async def process_continue(callback: CallbackQuery, state: FSMContext):
    """Jugador eligió continuar gambleando, mostrar siguiente pregunta"""
    user_id = callback.from_user.id
    fsm_data = await state.get_data()
    current_streak = fsm_data.get('current_streak', 0)

    await show_next_question(callback, state, user_id, current_streak)


@router.callback_query(TriviaStreakStates.streak_choice, F.data.startswith("trivia_retire_"))
async def process_retire(callback: CallbackQuery, state: FSMContext):
    """Jugador eligió retirarse, reclamar código, mostrar código"""
    user_id = callback.from_user.id
    fsm_data = await state.get_data()
    current_streak = fsm_data.get('current_streak', 0)

    # Extraer discount del callback: trivia_retire_{discount}
    parts = callback.data.split("_")
    discount = int(parts[2])

    with get_service(GameService) as service:
        # Obtener código disponible para el tier con este descuento
        code = service.claim_discount_code(user_id, discount)

        if not code:
            text = (
                f"🎰 <b>Trivia del Destino</b>\n\n"
                f"<i>Lo siento, no hay códigos disponibles para {discount}% de descuento.</i>\n\n"
                f"Sus códigos fueron cancelados."
            )
            buttons = [[InlineKeyboardButton(text="🔙 Menú", callback_data="trivia_discount_menu")]]
            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
            await state.set_state(TriviaStreakStates.waiting_answer)
            await callback.answer()
            return

        await state.update_data(current_streak=0)
        await state.set_state(TriviaStreakStates.waiting_retire)

        text = (
            f"🎰 <b>¡Código Reclamado!</b>\n\n"
            f"🔥 Racha final: <b>{current_streak}</b>\n\n"
            f"🏷️ <b>Código de {discount}% de descuento:</b>\n\n"
            f"<code>{code}</code>\n\n"
            f"<i>Úselo al realizar su compra.</i>"
        )

        buttons = [[InlineKeyboardButton(text="🔙 Menú", callback_data="trivia_discount_menu")]]
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        await callback.answer()
        logger.info(
            f"trivia_discount_user_handlers - process_retire - {user_id} - "
            f"claimed {discount}% code:{code}, streak:{current_streak}"
        )


@router.callback_query(TriviaStreakStates.streak_choice, F.data == "trivia_abandon")
async def process_abandon(callback: CallbackQuery, state: FSMContext):
    """Jugador eligió abandonar, sin código"""
    user_id = callback.from_user.id
    fsm_data = await state.get_data()
    current_streak = fsm_data.get('current_streak', 0)

    await state.update_data(current_streak=0)
    await state.set_state(TriviaStreakStates.waiting_answer)

    text = (
        f"🎰 <b>Juego Abandonado</b>\n\n"
        f"🔥 Racha: <b>{current_streak}</b> (sin código)\n\n"
        f"<i>Lamentablemente no hay premio esta vez.</i>\n\n"
        f"¿Desea intentarlo de nuevo?"
    )

    buttons = [
        [InlineKeyboardButton(text="🔄 Jugar de nuevo", callback_data="start_trivia_discount")],
        [InlineKeyboardButton(text="🔙 Menú", callback_data="trivia_discount_menu")]
    ]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()
    logger.info(f"trivia_discount_user_handlers - process_abandon - {user_id} - abandoned at streak:{current_streak}")


# ==================== GAME OVER / FINAL ====================

@router.callback_query(TriviaStreakStates.waiting_answer, F.data == "trivia_game_over")
async def show_game_over(callback: CallbackQuery, state: FSMContext):
    """Muestra resultado final (respuesta incorrecta o abandonado)"""
    user_id = callback.from_user.id
    fsm_data = await state.get_data()
    final_streak = fsm_data.get('current_streak', 0)

    text = (
        f"🎰 <b>Trivia del Destino</b>\n\n"
        f"<i>El juego ha terminado.</i>\n\n"
        f"🔢 Racha final: <b>{final_streak}</b>\n\n"
        f"<i>¿Desea probar suerte de nuevo?</i>"
    )

    buttons = [
        [InlineKeyboardButton(text="🔄 Jugar de nuevo", callback_data="start_trivia_discount")],
        [InlineKeyboardButton(text="🔙 Menú", callback_data="trivia_discount_menu")]
    ]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()
    logger.info(f"trivia_discount_user_handlers - show_game_over - {user_id} - final_streak:{final_streak}")


@router.callback_query(TriviaStreakStates.waiting_retire, F.data == "trivia_show_code")
async def show_code_claimed(callback: CallbackQuery, state: FSMContext):
    """Muestra el código de descuento reclamado con opción de copiar"""
    user_id = callback.from_user.id

    with get_service(GameService) as service:
        # Buscar código activo del usuario
        code_data = service.get_active_discount_code(user_id)

        if not code_data:
            text = (
                f"🎰 <b>Trivia del Destino</b>\n\n"
                f"<i>No tiene códigos activos.</i>"
            )
            buttons = [[InlineKeyboardButton(text="🔙 Menú", callback_data="trivia_discount_menu")]]
            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
            await state.set_state(TriviaStreakStates.waiting_answer)
            await callback.answer()
            return

        discount = code_data['discount_percentage']
        code = code_data['code']

        text = (
            f"🎰 <b>Su Código de Descuento</b>\n\n"
            f"🏷️ <b>Descuento:</b> {discount}%\n"
            f"🔑 <b>Código:</b>\n\n"
            f"<code>{code}</code>\n\n"
            f"<i>Copie el código y úselo al comprar.</i>"
        )

        buttons = [[InlineKeyboardButton(text="🔙 Menú", callback_data="trivia_discount_menu")]]
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        await callback.answer()
        logger.info(f"trivia_discount_user_handlers - show_code_claimed - {user_id} - showing code:{code}")


# ==================== KEYBOARDS ====================

def trivia_discount_question_keyboard(question) -> InlineKeyboardMarkup:
    """Teclado con opciones de trivia discount A, B, C, D"""
    buttons = []

    options = [
        ("A", question.option_a),
        ("B", question.option_b),
        ("C", question.option_c),
        ("D", question.option_d),
    ]

    for idx, (letter, text) in enumerate(options):
        buttons.append([InlineKeyboardButton(
            text=f"{letter}) {text}",
            callback_data=f"trivia_discount_answer_{idx}_{question.id}"
        )])

    buttons.append([InlineKeyboardButton(
        text="🔙 Abandonar",
        callback_data="trivia_discount_menu"
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def streak_choice_keyboard(discount: int) -> InlineKeyboardMarkup:
    """Teclado para elección de streak: continuar, retirarse con X%, abandonar"""
    buttons = [
        [InlineKeyboardButton(
            text="🔄 Continuar",
            callback_data="trivia_continue"
        )],
        [InlineKeyboardButton(
            text=f"🏷️ Retirarse con {discount}% de descuento",
            callback_data=f"trivia_retire_{discount}"
        )],
        [InlineKeyboardButton(
            text="❌ Abandonar",
            callback_data="trivia_abandon"
        )]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)
