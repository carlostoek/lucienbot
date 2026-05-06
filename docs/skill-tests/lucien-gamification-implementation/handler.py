"""
Handlers de Racha Diaria - Lucien Bot

Maneja el flujo FSM de reclamo de racha diaria con inline keyboard.
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from keyboards.inline_keyboards import back_keyboard
from services import get_service

logger = logging.getLogger(__name__)
router = Router()


# ==================== CALLBACK DATA CONSTANTS ====================

STREAK_SHOW = "streak:show"
STREAK_CLAIM = "streak:claim"
STREAK_CANCEL = "streak:cancel"


# ==================== TEMPLATES DE COPY ====================

STREAK_TEMPLATES = {
    'title': [
        "🔥 Tu Racha Diaria",
        "🔥 El Ritual de la Constancia",
        "🔥 La llama que arde sin cesar"
    ],
    'already_claimed': [
        "⏳ <b>Ya reclamaste tu racha el día de hoy.</b>\n\n"
        "Diana aprecia tu constancia, pero el tiempo aún no ha vuelto a gir.",
        "⏳ <b>El ritual de hoy ya fue completado.</b>\n\n"
        "La llama sigue ardiendo desde tu último gesto."
    ],
    'grace_period': [
        "🎩 <b>Lucien:</b>\n\n"
        "<i>Interesante... el tiempo between nuestros encuentros\n"
        "es corto, mas no tanto. La llama aún arde.</i>\n\n"
        "🔥 <b>Racha: {streak} días</b>\n"
        "💋 <b>Bonus: +{bonus} besitos</b>\n\n"
        "<i>¿Desea reclamar su recompensa?</i>",
        "🎩 <b>Lucien:</b>\n\n"
        "<i>Qué sorpresa encontrarla aquí otra vez.\n"
        "El tiempo Between visitas es... aceptable.</i>\n\n"
        "🔥 <b>Racha: {streak} días</b>\n"
        "💋 <b>Bonus: +{bonus} besitos</b>\n\n"
        "<i>¿Reclama su lugar en la llama?</i>"
    ],
    'streak_lost': [
        "💔 <b>La llama se extinguió...</b>\n\n"
        "Han pasado <b>{hours}h</b> desde su última visita.\n"
        "La racha de <b>{lost_streak}</b> días se perdió.\n\n"
        "🔥 Pero hoy puede comenzar de nuevo.\n"
        "💋 <b>+{bonus} besitos</b> para reiniciar su camino.",
        "💔 <b>El tiempo no perdona...</b>\n\n"
        "<b>{hours}h</b> sin su presencia.\n"
        "<b>{lost_streak}</b> días de constancia... olvidados.\n\n"
        "🔥 Una nueva llama puede encenderse hoy.\n"
        "💋 <b>+{bonus} besitos</b> para su renaissance."
    ],
    'new_user': [
        "🎩 <b>Lucien:</b>\n\n"
        "<i>Un nuevo visitante en el salón de Diana.\n"
        "Los rituales diarios recompensan la constancia.</i>\n\n"
        "🔥 <b>Comienza tu racha: +{bonus} besitos</b>\n\n"
        "<i>¿Listo para el primer paso?</i>",
        "🎩 <b>Lucien:</b>\n\n"
        "<i>El salón de juegos abre sus puertas\n"
        "para quienes saben volver cada día.</i>\n\n"
        "🔥 <b>+{bonus} besitos</b> para iniciar su camino.\n\n"
        "<i>¿Acepta el desafío?</i>"
    ],
    'claim_success': [
        "🎉 <b>¡Racha reclamada!</b>\n\n"
        "🔥 <b>Racha: {streak} días</b>\n"
        "💋 <b>+{bonus} besitos</b>\n\n"
        "<i>Vuelve mañana para mantener la llama.</i>",
        "🎉 <b>¡La llama arde más fuerte!</b>\n\n"
        "🔥 <b>Racha: {streak} días</b>\n"
        "💋 <b>+{bonus} besitos</b>\n\n"
        "<i>Diana observa su dedicación con agrado.</i>"
    ],
    'footer': [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    ]
}


# ==================== HELPER ====================

def streak_status_keyboard(can_claim: bool) -> InlineKeyboardMarkup:
    """Teclado inline para estado de racha"""
    buttons = []

    if can_claim:
        buttons.append([
            InlineKeyboardButton(
                text="🔥 Reclamar Racha",
                callback_data=STREAK_CLAIM
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="🔙 Menú Principal",
            callback_data="back_to_main"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _select_template(template_list: list) -> str:
    """Selecciona variación aleatoria"""
    import random
    return random.choice(template_list)


def _build_streak_display(status_data: dict, grace_status: str) -> str:
    """Construye mensaje de estado de racha"""
    templates = STREAK_TEMPLATES

    if grace_status == 'already_claimed':
        header = _select_template(templates['already_claimed'])
        return f"🎩 <b>Lucien:</b>\n\n{header}"

    if grace_status == 'grace_period':
        template = _select_template(templates['grace_period'])
        return template.format(
            streak=status_data['streak'] + 1,
            bonus=status_data['bonus_preview']
        )

    if grace_status == 'streak_lost':
        template = _select_template(templates['streak_lost'])
        return template.format(
            hours=int(status_data['hours_since']),
            lost_streak=status_data['streak'],
            bonus=status_data['bonus_preview']
        )

    # new_user
    template = _select_template(templates['new_user'])
    return template.format(bonus=status_data['bonus_preview'])


# ==================== HANDLERS ====================

@router.callback_query(F.data == STREAK_SHOW)
async def streak_show(callback: CallbackQuery, state: FSMContext):
    """Muestra estado actual de racha"""
    user_id = callback.from_user.id

    with get_service(__import__('services.daily_streak_service', fromlist=['DailyStreakService']).DailyStreakService) as service:
        status_data = service.get_streak_status(user_id)

    grace_status = status_data['grace_status']
    can_claim = status_data['can_claim']
    message = _build_streak_display(status_data, grace_status)

    # Guardar en FSM para uso posterior
    await state.update_data(
        streak_data=status_data,
        grace_status=grace_status
    )

    if grace_status == 'already_claimed':
        await state.set_state(
            __import__('services.daily_streak_service', fromlist=['DailyStreakService']).DailyStreakStates.streak_active
        )
    elif grace_status in ('grace_period', 'new_user'):
        await state.set_state(
            __import__('services.daily_streak_service', fromlist=['DailyStreakService']).DailyStreakStates.grace_period
        )
    else:  # streak_lost
        await state.set_state(
            __import__('services.daily_streak_service', fromlist=['DailyStreakService']).DailyStreakStates.streak_lost
        )

    await callback.message.edit_text(
        message,
        reply_markup=streak_status_keyboard(can_claim),
        parse_mode="HTML"
    )
    await callback.answer()
    logger.info(f"daily_streak_handlers - streak_show - {user_id} - status:{grace_status}")


@router.callback_query(F.data == STREAK_CLAIM)
async def streak_claim(callback: CallbackQuery, state: FSMContext):
    """Procesa reclamo de racha"""
    user_id = callback.from_user.id

    with get_service(__import__('services.daily_streak_service', fromlist=['DailyStreakService']).DailyStreakService) as service:
        result = service.claim_daily_streak(user_id)

    templates = STREAK_TEMPLATES

    if result['status'] in ('success', 'grace_claimed'):
        header = _select_template(templates['claim_success'])
        message = f"🎩 <b>Lucien:</b>\n\n{header}".format(
            streak=result['new_streak'],
            bonus=result['bonus']
        )
    elif result['status'] == 'already_claimed':
        message = (
            f"🎩 <b>Lucien:</b>\n\n"
            f"<i>Ya reclamaste tu racha el día de hoy.</i>\n\n"
            f"⏳ Espera {int(20 - (status_data.get('hours_since', 0)))}h más."
        )
        await callback.answer("Ya reclamaste hoy", show_alert=True)
        return
    elif result['status'] == 'streak_lost':
        header = _select_template(templates['streak_lost'])
        message = f"🎩 <b>Lucien:</b>\n\n{header}".format(
            hours=int(result.get('hours_since', 48)),
            lost_streak=result['lost_streak'],
            bonus=result['bonus']
        )
    else:  # new_user
        header = _select_template(templates['claim_success'])
        message = f"🎩 <b>Lucien:</b>\n\n{header}".format(
            streak=result['new_streak'],
            bonus=result['bonus']
        )

    await state.clear()

    await callback.message.edit_text(
        message,
        reply_markup=back_keyboard("back_to_main"),
        parse_mode="HTML"
    )
    await callback.answer(f"+{result['bonus']} besitos! 💋")
    logger.info(
        f"daily_streak_handlers - streak_claim - {user_id} - "
        f"status:{result['status']}, streak:{result['new_streak']}, bonus:{result['bonus']}"
    )


@router.callback_query(F.data == STREAK_CANCEL)
async def streak_cancel(callback: CallbackQuery, state: FSMContext):
    """Cancela flujo de racha"""
    await state.clear()
    await callback.message.edit_text(
        "🎩 <b>Lucien:</b>\n\n"
        "<i>El ritual ha sido postergado.\n"
        "Puedes volver cuando lo desees.</i>",
        reply_markup=back_keyboard("back_to_main"),
        parse_mode="HTML"
    )
    await callback.answer()
