"""
Handlers de Administracion para Sistema de Descuentos Trivia - Lucien Bot

Gestion de promociones trivia, tiers, codigos y configuracion global.
Con la voz caracteristica de Lucien.
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
from config.settings import bot_config
from services import get_service
from services.trivia_discount_service import TriviaDiscountService
from services.trivia_admin_service import TriviaAdminService
import logging

logger = logging.getLogger(__name__)
router = Router()


# Estados para FSM del wizard de promocion trivia
class TriviaDiscountStates(StatesGroup):
    waiting_promotion_type = State()      # Fixed / Relative
    waiting_dates_or_duration = State()   # Step 2a or 2b
    waiting_name = State()                # Step 3
    waiting_description = State()        # Step 3
    waiting_tiers = State()               # Step 4 - multiple tiers
    waiting_question_set = State()       # Step 5
    waiting_confirmation = State()        # Step 6


class ManageLimitsStates(StatesGroup):
    waiting_free_limit = State()
    waiting_vip_limit = State()
    waiting_vip_exclusive_limit = State()


def is_admin(user_id: int) -> bool:
    return user_id in bot_config.ADMIN_IDS


# ==================== MENU PRINCIPAL ====================

@router.callback_query(F.data == "admin_trivia", lambda cb: is_admin(cb.from_user.id))
async def admin_trivia_menu(callback: CallbackQuery):
    """Menu principal de administracion trivia - Voz de Lucien"""
    with get_service(TriviaAdminService) as admin_service:
        with get_service(TriviaDiscountService) as trivia_service:
            limits = admin_service.get_limits()
            active_promos = trivia_service.get_active_promotions()

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🆕 Forjar nueva promocion", callback_data="trivia_create_promotion")],
                [InlineKeyboardButton(text="📋 Ver promociones", callback_data="trivia_list_promotions")],
                [InlineKeyboardButton(text="🔑 Gestionar codigos", callback_data="trivia_manage_codes")],
                [InlineKeyboardButton(text="📊 Estadisticas", callback_data="trivia_statistics")],
                [InlineKeyboardButton(text="⚙️ Configurar limites", callback_data="trivia_configure_limits")],
                [InlineKeyboardButton(text="🔙 Volver al sanctum", callback_data="admin_gamification")]
            ])

            text = ("🎩 <b>Lucien:</b>\n\n"
                    "<i>Ah... el taller donde se forjan las experiencias trivia.</i>\n\n"
                    "Aqui es donde Diana configura los juegos de trivia que premian "
                    "la constancia con descuentos exclusivos.\n\n"
                    f"📊 <b>Estado del taller:</b>\n"
                    f"   • Promociones activas: {len(active_promos)}\n"
                    f"   • Limite diario (free): {limits.free_daily_limit if limits else 'N/A'}\n"
                    f"   • Limite diario (VIP): {limits.vip_daily_limit if limits else 'N/A'}\n"
                    f"   • Limite VIP exclusivo: {limits.vip_exclusive_daily_limit if limits else 'N/A'}\n\n"
                    "<i>Que aspecto del taller requiere su atencion?</i>")

            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
            await callback.answer()


# ==================== WIZARD CREAR PROMOCION ====================

@router.callback_query(F.data == "trivia_create_promotion", lambda cb: is_admin(cb.from_user.id))
async def create_promotion_start(callback: CallbackQuery, state: FSMContext):
    """Inicia wizard de creacion de promocion trivia - Voz de Lucien"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_trivia")]
    ])

    text = ("🎩 <b>Lucien:</b>\n\n"
            "<i>Vamos a forjar una nueva promocion trivia...</i>\n\n"
            "<b>Paso 1 de 6:</b> Tipo de promocion\n\n"
            "Indique el tipo de promocion:\n\n"
            "📅 <b>Fija:</b> Con fechas de inicio y fin definidas\n"
            "⏱️ <b>Relativa:</b> Con duracion en dias desde el primer juego\n\n"
            "Envie <code>FIJA</code> o <code>RELATIVA</code>")

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    await state.set_state(TriviaDiscountStates.waiting_promotion_type)
    await callback.answer()


@router.message(TriviaDiscountStates.waiting_promotion_type)
async def process_promotion_type(message: Message, state: FSMContext):
    """Procesa el tipo de promocion - Voz de Lucien"""
    promo_type = message.text.strip().upper()
    if promo_type not in ("FIJA", "RELATIVA"):
        await message.answer(
            "Por favor envie <code>FIJA</code> o <code>RELATIVA</code>",
            parse_mode=ParseMode.HTML
        )
        return

    await state.update_data(promotion_type=promo_type)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_trivia")]
    ])

    if promo_type == "FIJA":
        text = ("🎩 <b>Lucien:</b>\n\n"
                "<b>Paso 2a de 6:</b> Fechas de vigencia\n\n"
                "Indique las fechas de inicio y fin:\n\n"
                "<code>INICIO: YYYY-MM-DD</code>\n"
                "<code>FIN: YYYY-MM-DD</code>\n\n"
                "<i>Ejemplo:</i>\n"
                "<code>INICIO: 2026-05-01</code>\n"
                "<code>FIN: 2026-05-31</code>")
    else:
        text = ("🎩 <b>Lucien:</b>\n\n"
                "<b>Paso 2b de 6:</b> Duracion\n\n"
                "Indique la duracion en dias:\n"
                "<i>Ejemplo: 7 (una semana)</i>")

    await message.answer(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    await state.set_state(TriviaDiscountStates.waiting_dates_or_duration)


@router.message(TriviaDiscountStates.waiting_dates_or_duration)
async def process_dates_or_duration(message: Message, state: FSMContext):
    """Procesa fechas o duracion - Voz de Lucien"""
    data = await state.get_data()
    promo_type = data.get('promotion_type')

    if promo_type == "FIJA":
        text = message.text.strip()
        start_date = None
        end_date = None

        try:
            lines = text.split('\n')
            for line in lines:
                if line.startswith('INICIO:'):
                    date_str = line.replace('INICIO:', '').strip()
                    start_date = datetime.strptime(date_str, '%Y-%m-%d')
                elif line.startswith('FIN:'):
                    date_str = line.replace('FIN:', '').strip()
                    end_date = datetime.strptime(date_str, '%Y-%m-%d')

            if not start_date or not end_date:
                raise ValueError("Ambas fechas son requeridas")

            await state.update_data(start_date=start_date, end_date=end_date, duration_days=None)

        except ValueError:
            await message.answer(
                "Formato incorrecto. Use:\n\n"
                "<code>INICIO: YYYY-MM-DD</code>\n"
                "<code>FIN: YYYY-MM-DD</code>",
                parse_mode=ParseMode.HTML
            )
            return
    else:
        try:
            duration = int(message.text.strip())
            if duration < 1:
                raise ValueError("Debe ser mayor a 0")
            await state.update_data(duration_days=duration, start_date=None, end_date=None)
        except ValueError:
            await message.answer("Por favor indique un numero valido mayor a 0.")
            return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_trivia")]
    ])

    text = ("🎩 <b>Lucien:</b>\n\n"
            "<b>Paso 3 de 6:</b> Nombre de la promocion\n\n"
            "Indique el nombre que capture la esencia de esta promocion:\n"
            "<i>Ejemplo: Trivia San Miguel - Verano 2026</i>")

    await message.answer(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    await state.set_state(TriviaDiscountStates.waiting_name)


@router.message(TriviaDiscountStates.waiting_name)
async def process_name(message: Message, state: FSMContext):
    """Procesa nombre de la promocion - Voz de Lucien"""
    name = message.text.strip()
    if len(name) < 3:
        await message.answer("El nombre debe tener al menos 3 caracteres.")
        return

    await state.update_data(name=name)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_trivia")]
    ])

    text = ("🎩 <b>Lucien:</b>\n\n"
            "<b>Paso 3b de 6:</b> Descripcion\n\n"
            "Describa lo que ofrece esta promocion (opcional):\n"
            "<i>Ejemplo: Un juego diario sobre la vida de Diana...</i>\n\n"
            "Envie /skip para omitir.")

    await message.answer(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    await state.set_state(TriviaDiscountStates.waiting_description)


@router.message(TriviaDiscountStates.waiting_description)
async def process_description(message: Message, state: FSMContext):
    """Procesa descripcion de la promocion - Voz de Lucien"""
    description = None if message.text == "/skip" else message.text.strip()
    await state.update_data(description=description)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_trivia")]
    ])

    text = ("🎩 <b>Lucien:</b>\n\n"
            "<b>Paso 4 de 6:</b> Configurar niveles\n\n"
            "Configure los niveles de descuento. Cada nivel tiene un umbral de racha "
            "y un porcentaje de descuento.\n\n"
            "Indique los datos del primer nivel en este formato:\n"
            "<code>NUMERO: 1</code>\n"
            "<code>UMBRAL: 5</code>\n"
            "<code>DESCUENTO: 10</code>\n"
            "<code>CODIGOS: 100</code>\n\n"
            "<i>Ejemplo: Con umbral 5 y descuento 10, quien llegue a 5 respuestas "
            "correctas seguidas recibira un codigo con 10% de descuento.</i>")

    await message.answer(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    await state.set_state(TriviaDiscountStates.waiting_tiers)


@router.message(TriviaDiscountStates.waiting_tiers)
async def process_tiers(message: Message, state: FSMContext):
    """Procesa configuracion de tiers - Voz de Lucien"""
    text = message.text.strip()

    try:
        tier_data = {}
        lines = text.split('\n')
        for line in lines:
            if line.startswith('NUMERO:'):
                tier_data['tier_number'] = int(line.replace('NUMERO:', '').strip())
            elif line.startswith('UMBRAL:'):
                tier_data['streak_threshold'] = int(line.replace('UMBRAL:', '').strip())
            elif line.startswith('DESCUENTO:'):
                tier_data['discount_percentage'] = int(line.replace('DESCUENTO:', '').strip())
            elif line.startswith('CODIGOS:'):
                tier_data['max_codes'] = int(line.replace('CODIGOS:', '').strip())

        required = ['tier_number', 'streak_threshold', 'discount_percentage', 'max_codes']
        for field in required:
            if field not in tier_data:
                raise ValueError(f"Campo requerido faltante: {field}")

        if tier_data['discount_percentage'] < 1 or tier_data['discount_percentage'] > 100:
            raise ValueError("El descuento debe estar entre 1 y 100")

    except ValueError as e:
        await message.answer(
            f"Formato incorrecto. {str(e)}\n\n"
            "Use:\n"
            "<code>NUMERO: 1</code>\n"
            "<code>UMBRAL: 5</code>\n"
            "<code>DESCUENTO: 10</code>\n"
            "<code>CODIGOS: 100</code>",
            parse_mode=ParseMode.HTML
        )
        return

    # Guardar primer tier y preguntar si hay mas
    existing_tiers = await state.get_data()
    tiers_list = existing_tiers.get('tiers_list', [])
    tiers_list.append(tier_data)
    await state.update_data(tiers_list=tiers_list)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Agregar otro nivel", callback_data="trivia_add_tier")],
        [InlineKeyboardButton(text="✅ Continuar", callback_data="trivia_done_adding_tiers")],
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_trivia")]
    ])

    text = (f"🎩 <b>Lucien:</b>\n\n"
            f"<b>Nivel {tier_data['tier_number']} guardado:</b>\n"
            f"   Umbral: {tier_data['streak_threshold']} respuestas seguidas\n"
            f"   Descuento: {tier_data['discount_percentage']}%\n"
            f"   Codigos disponibles: {tier_data['max_codes']}\n\n"
            f"<i>Desea agregar otro nivel?</i>")

    await message.answer(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "trivia_add_tier", lambda cb: is_admin(cb.from_user.id))
async def add_another_tier(callback: CallbackQuery, state: FSMContext):
    """Agrega otro tier al wizard"""
    data = await state.get_data()
    next_tier_number = len(data.get('tiers_list', [])) + 1

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_trivia")]
    ])

    text = (f"🎩 <b>Lucien:</b>\n\n"
            f"<b>Paso 4 de 6:</b> Configurar nivel {next_tier_number}\n\n"
            f"Indique los datos del nivel {next_tier_number}:\n\n"
            "<code>NUMERO: {next_tier_number}</code>\n"
            "<code>UMBRAL: 10</code>\n"
            "<code>DESCUENTO: 20</code>\n"
            "<code>CODIGOS: 50</code>")

    await callback.message.edit_text(
        text.format(next_tier_number=next_tier_number),
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )
    await state.set_state(TriviaDiscountStates.waiting_tiers)
    await callback.answer()


@router.callback_query(F.data == "trivia_done_adding_tiers", lambda cb: is_admin(cb.from_user.id))
async def done_adding_tiers(callback: CallbackQuery, state: FSMContext):
    """Continua al paso de seleccion de question set"""
    data = await state.get_data()
    if not data.get('tiers_list'):
        await callback.answer("Debe agregar al menos un nivel", show_alert=True)
        return

    with get_service(TriviaDiscountService) as trivia_service:
        question_sets = trivia_service.get_all_question_sets(active_only=True)

    if not question_sets:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_trivia")]
        ])
        text = ("🎩 <b>Lucien:</b>\n\n"
                "<i>No hay sets de preguntas activos...</i>\n\n"
                "Debe crear un set de preguntas antes de continuar.")
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        return

    buttons = []
    for qset in question_sets:
        question_count = len(qset.questions) if qset.questions else 0
        buttons.append([InlineKeyboardButton(
            text=f"{qset.name} ({question_count} preguntas)",
            callback_data=f"trivia_select_qset_{qset.id}"
        )])

    buttons.append([InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_trivia")])

    text = ("🎩 <b>Lucien:</b>\n\n"
            "<b>Paso 5 de 6:</b> Seleccionar set de preguntas\n\n"
            "Elija que set de preguntas utilizara esta promocion:")

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode=ParseMode.HTML
    )
    await state.set_state(TriviaDiscountStates.waiting_question_set)
    await callback.answer()


@router.callback_query(TriviaDiscountStates.waiting_question_set, F.data.startswith("trivia_select_qset_"))
async def select_question_set(callback: CallbackQuery, state: FSMContext):
    """Procesa seleccion de question set"""
    try:
        qset_id = int(callback.data.replace("trivia_select_qset_", ""))
    except ValueError:
        await callback.answer("ID invalido", show_alert=True)
        return

    await state.update_data(question_set_id=qset_id)
    await show_trivia_confirmation(callback, state)
    await callback.answer()


async def show_trivia_confirmation(target, state: FSMContext):
    """Muestra confirmacion de la promocion trivia - Voz de Lucien"""
    data = await state.get_data()

    name = data.get('name', '')
    description = data.get('description', 'Sin descripcion')
    promo_type = data.get('promotion_type', '')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    duration_days = data.get('duration_days')
    tiers_list = data.get('tiers_list', [])
    question_set_id = data.get('question_set_id')

    with get_service(TriviaDiscountService) as trivia_service:
        qset = trivia_service.get_question_set(question_set_id) if question_set_id else None

    if promo_type == "FIJA":
        type_text = "Fecha fija"
        if start_date:
            type_text += f"\nInicio: {start_date.strftime('%Y-%m-%d')}"
        if end_date:
            type_text += f"\nFin: {end_date.strftime('%Y-%m-%d')}"
    else:
        type_text = f"Relativa ({duration_days} dias)"

    text = (f"🎩 <b>Lucien:</b>\n\n"
            f"<i>Permitame confirmar los detalles de esta promocion...</i>\n\n"
            f"✨ <b>{name}</b>\n"
            f"📝 {description}\n\n"
            f"📅 <b>Tipo:</b> {type_text}\n\n"
            f"<b>Niveles configurados ({len(tiers_list)}):</b>\n")

    for tier in tiers_list:
        text += (f"   {tier['tier_number']}. Umbral {tier['streak_threshold']} → "
                 f"{tier['discount_percentage']}% ({tier['max_codes']} codigos)\n")

    text += f"\n📚 <b>Set de preguntas:</b> {qset.name if qset else 'N/A'}\n\n"
    text += f"<i>Desea forjar esta promocion?</i>"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Forjar promocion", callback_data="confirm_create_trivia_promotion")],
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_trivia")]
    ])

    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    else:
        await target.answer(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

    await state.set_state(TriviaDiscountStates.waiting_confirmation)


@router.callback_query(TriviaDiscountStates.waiting_confirmation, F.data == "confirm_create_trivia_promotion")
async def confirm_create_promotion(callback: CallbackQuery, state: FSMContext):
    """Crea la promocion trivia - Voz de Lucien"""
    data = await state.get_data()

    with get_service(TriviaDiscountService) as trivia_service:
        try:
            # Crear configuracion de promocion
            config_data = {
                'name': data.get('name'),
                'description': data.get('description'),
                'start_date': data.get('start_date'),
                'end_date': data.get('end_date'),
                'duration_days': data.get('duration_days'),
                'question_set_id': data.get('question_set_id'),
                'is_active': True,
                'auto_reset': True
            }

            config = trivia_service.create_promotion_config(config_data)

            if not config:
                raise Exception("No se pudo crear la configuracion")

            # Crear los tiers
            tiers_list = data.get('tiers_list', [])
            db = trivia_service._get_db()

            from models.models import Tier

            for tier_data in tiers_list:
                tier = Tier(
                    promotion_config_id=config.id,
                    tier_number=tier_data['tier_number'],
                    streak_threshold=tier_data['streak_threshold'],
                    discount_percentage=tier_data['discount_percentage'],
                    max_codes=tier_data['max_codes'],
                    codes_generated=0
                )
                db.add(tier)

            db.commit()

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Volver al taller", callback_data="admin_trivia")]
            ])

            text = (f"🎩 <b>Lucien:</b>\n\n"
                    f"<i>Excelente. La promocion ha sido forjada...</i>\n\n"
                    f"✨ <b>{config.name}</b>\n"
                    f"📅 Tipo: {data.get('promotion_type')}\n"
                    f"📚 Set: {data.get('question_set_id')}\n\n"
                    f"<i>Ya esta disponible para quienes deseen... jugar.</i>")

            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
            logger.info(f"TriviaPromotionConfig creada: {config.name} por custodio {callback.from_user.id}")

        except Exception as e:
            logger.error(f"Error forjando promocion trivia: {e}")
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Volver", callback_data="admin_trivia")]
            ])
            text = ("🎩 <b>Lucien:</b>\n\n"
                    "<i>Hmm... algo inesperado ha ocurrido.</i>\n\n"
                    "Permitame consultar con Diana sobre este inconveniente.")
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

        await state.clear()
        await callback.answer()


# ==================== LISTAR PROMOCIONES ====================

@router.callback_query(F.data == "trivia_list_promotions", lambda cb: is_admin(cb.from_user.id))
async def list_promotions(callback: CallbackQuery):
    """Lista todas las promociones trivia - Voz de Lucien"""
    with get_service(TriviaAdminService) as admin_service:
        promotions = admin_service.get_all_promotions()

        if not promotions:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Volver", callback_data="admin_trivia")]
            ])
            text = ("🎩 <b>Lucien:</b>\n\n"
                    "<i>El taller esta vacio...</i>\n\n"
                    "Aun no se han forjado promociones trivia.")
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
            await callback.answer()
            return

        text = "🎩 <b>Lucien:</b>\n\n"
        text += "<i>Las promociones en el taller:</i>\n\n"
        buttons = []

        for promo in promotions:
            status = "✅" if promo.is_active else "❌"
            text += f"{status} <b>{promo.name}</b>\n"
            if promo.start_date and promo.end_date:
                text += f"   📅 {promo.start_date.strftime('%Y-%m-%d')} - {promo.end_date.strftime('%Y-%m-%d')}\n"
            elif promo.duration_days:
                text += f"   ⏱️ {promo.duration_days} dias\n"
            text += "\n"

            buttons.append([InlineKeyboardButton(
                text=f"{status} {promo.name[:30]}",
                callback_data=f"trivia_promo_detail_{promo.id}"
            )])

        buttons.append([InlineKeyboardButton(text="🔙 Volver", callback_data="admin_trivia")])

        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode=ParseMode.HTML
        )
        await callback.answer()


@router.callback_query(F.data.startswith("trivia_promo_detail_"), lambda cb: is_admin(cb.from_user.id))
async def promotion_detail(callback: CallbackQuery):
    """Muestra detalle de una promocion trivia - Voz de Lucien"""
    try:
        promo_id = int(callback.data.replace("trivia_promo_detail_", ""))
    except ValueError:
        await callback.answer("ID invalido", show_alert=True)
        return

    with get_service(TriviaDiscountService) as trivia_service:
        promo = trivia_service.get_promotion_config(promo_id)

        if not promo:
            await callback.answer("Promocion no encontrada", show_alert=True)
            return

        with get_service(TriviaAdminService) as admin_service:
            stats = admin_service.get_promotion_stats(promo_id)

        status = "✅ Activa" if promo.is_active else "❌ Inactiva"
        dates_text = "Sin fechas"
        if promo.start_date and promo.end_date:
            dates_text = f"{promo.start_date.strftime('%Y-%m-%d')} - {promo.end_date.strftime('%Y-%m-%d')}"
        elif promo.duration_days:
            dates_text = f"{promo.duration_days} dias de duracion"

        tiers_text = ""
        for tier in promo.tiers:
            tiers_text += f"   {tier.tier_number}. {tier.discount_percentage}% (umbral {tier.streak_threshold})\n"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{'Pausar' if promo.is_active else 'Reanudar'}",
                callback_data=f"trivia_toggle_promo_{promo_id}"
            )],
            [InlineKeyboardButton(
                text="📊 Ver estadisticas",
                callback_data=f"trivia_view_stats_{promo_id}"
            )],
            [InlineKeyboardButton(
                text="📤 Exportar codigos",
                callback_data=f"trivia_export_codes_{promo_id}"
            )],
            [InlineKeyboardButton(
                text="🗑️ Eliminar",
                callback_data=f"trivia_delete_promo_{promo_id}"
            )],
            [InlineKeyboardButton(text="🔙 Volver", callback_data="trivia_list_promotions")]
        ])

        text = (f"🎩 <b>Lucien:</b>\n\n"
                f"✨ <b>{promo.name}</b>\n\n"
                f"📝 {promo.description or 'Sin descripcion'}\n\n"
                f"📅 <b>Tipo:</b> {dates_text}\n"
                f"📊 <b>Estado:</b> {status}\n\n"
                f"<b>Niveles:</b>\n{tiers_text or '   Sin niveles configurados'}\n"
                f"<b>Codigos:</b>\n"
                f"   Total: {stats.get('total_codes', 0)}\n"
                f"   Disponibles: {stats.get('available_codes', 0)}\n"
                f"   Reclamados: {stats.get('claimed_codes', 0)}\n"
                f"   Usados: {stats.get('used_codes', 0)}\n\n"
                "<i>Que desea hacer con esta promocion?</i>")

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        await callback.answer()


@router.callback_query(F.data.startswith("trivia_toggle_promo_"), lambda cb: is_admin(cb.from_user.id))
async def toggle_promotion(callback: CallbackQuery):
    """Activa/desactiva una promocion trivia"""
    try:
        promo_id = int(callback.data.replace("trivia_toggle_promo_", ""))
    except ValueError:
        await callback.answer("ID invalido", show_alert=True)
        return

    with get_service(TriviaDiscountService) as trivia_service:
        promo = trivia_service.get_promotion_config(promo_id)

        if not promo:
            await callback.answer("Promocion no encontrada", show_alert=True)
            return

        if promo.is_active:
            trivia_service.pause_promotion(promo_id)
        else:
            trivia_service.resume_promotion(promo_id)

        status = "pausada" if promo.is_active else "reactivada"
        await callback.answer(f"Promocion {status}")
        await promotion_detail(callback)


@router.callback_query(F.data.startswith("trivia_delete_promo_"), lambda cb: is_admin(cb.from_user.id))
async def delete_promotion_confirm(callback: CallbackQuery):
    """Confirma eliminacion de promocion trivia"""
    try:
        promo_id = int(callback.data.replace("trivia_delete_promo_", ""))
    except ValueError:
        await callback.answer("ID invalido", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Si, eliminar", callback_data=f"trivia_confirm_delete_{promo_id}")],
        [InlineKeyboardButton(text="❌ Cancelar", callback_data=f"trivia_promo_detail_{promo_id}")]
    ])

    text = ("🎩 <b>Lucien:</b>\n\n"
            "<i>Esta seguro de eliminar esta promocion?</i>\n\n"
            "Esta accion no se puede deshacer. "
            "Todos los codigos asociados tambien se perderan...")

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    await callback.answer()


@router.callback_query(F.data.startswith("trivia_confirm_delete_"), lambda cb: is_admin(cb.from_user.id))
async def confirm_delete_promotion(callback: CallbackQuery):
    """Elimina la promocion trivia"""
    try:
        promo_id = int(callback.data.replace("trivia_confirm_delete_", ""))
    except ValueError:
        await callback.answer("ID invalido", show_alert=True)
        return

    with get_service(TriviaDiscountService) as trivia_service:
        success = trivia_service.delete_promotion_config(promo_id)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Volver al taller", callback_data="admin_trivia")]
        ])

        if success:
            text = ("🎩 <b>Lucien:</b>\n\n"
                    "<i>La promocion ha sido eliminada del taller.</i>")
        else:
            text = ("🎩 <b>Lucien:</b>\n\n"
                    "<i>Hmm... no se pudo eliminar la promocion.</i>")

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        await callback.answer()


# ==================== ESTADISTICAS ====================

@router.callback_query(F.data.startswith("trivia_view_stats_"), lambda cb: is_admin(cb.from_user.id))
async def view_promotion_stats(callback: CallbackQuery):
    """Muestra estadisticas de una promocion especifica"""
    try:
        promo_id = int(callback.data.replace("trivia_view_stats_", ""))
    except ValueError:
        await callback.answer("ID invalido", show_alert=True)
        return

    with get_service(TriviaDiscountService) as trivia_service:
        promo = trivia_service.get_promotion_config(promo_id)

        if not promo:
            await callback.answer("Promocion no encontrada", show_alert=True)
            return

    with get_service(TriviaAdminService) as admin_service:
        stats = admin_service.get_promotion_stats(promo_id)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Volver", callback_data=f"trivia_promo_detail_{promo_id}")]
    ])

    by_tier = stats.get('by_tier', [])
    tiers_text = ""
    for tier in by_tier:
        tiers_text += (f"   Nivel {tier['tier_number']}: {tier['discount_percentage']}%\n"
                       f"      Generados: {tier['codes_generated']} / {tier['max_codes']}\n"
                       f"      Disponibles: {tier['available']}\n")

    text = (f"🎩 <b>Lucien:</b>\n\n"
            f"📊 <b>Estadisticas: {promo.name}</b>\n\n"
            f"<b>Codigos:</b>\n"
            f"   Total: {stats.get('total_codes', 0)}\n"
            f"   Disponibles: {stats.get('available_codes', 0)}\n"
            f"   Reclamados: {stats.get('claimed_codes', 0)}\n"
            f"   Usados: {stats.get('used_codes', 0)}\n\n"
            f"<b>Por nivel:</b>\n{tiers_text or '   Sin datos'}")

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    await callback.answer()


@router.callback_query(F.data == "trivia_statistics", lambda cb: is_admin(cb.from_user.id))
async def show_global_stats(callback: CallbackQuery):
    """Muestra estadisticas globales trivia"""
    with get_service(TriviaAdminService) as admin_service:
        with get_service(TriviaDiscountService) as trivia_service:
            promotions = admin_service.get_all_promotions()
            limits = admin_service.get_limits()

            total_codes = 0
            total_available = 0

            for promo in promotions:
                stats = admin_service.get_promotion_stats(promo.id)
                total_codes += stats.get('total_codes', 0)
                total_available += stats.get('available_codes', 0)

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Volver", callback_data="admin_trivia")]
            ])

            text = (f"🎩 <b>Lucien:</b>\n\n"
                    f"📊 <b>Estado global del taller trivia:</b>\n\n"
                    f"✨ <b>Promociones:</b> {len(promotions)}\n"
                    f"📝 Activas: {sum(1 for p in promotions if p.is_active)}\n\n"
                    f"<b>Limites diarios:</b>\n"
                    f"   Free: {limits.free_daily_limit if limits else 'N/A'}\n"
                    f"   VIP: {limits.vip_daily_limit if limits else 'N/A'}\n"
                    f"   VIP Exclusivo: {limits.vip_exclusive_daily_limit if limits else 'N/A'}\n\n"
                    f"<b>Codigos en circulation:</b>\n"
                    f"   Total generados: {total_codes}\n"
                    f"   Disponibles: {total_available}")

            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
            await callback.answer()


# ==================== EXPORTAR CODIGOS ====================

@router.callback_query(F.data.startswith("trivia_export_codes_"), lambda cb: is_admin(cb.from_user.id))
async def export_codes(callback: CallbackQuery):
    """Exporta codigos de una promocion a CSV"""
    try:
        promo_id = int(callback.data.replace("trivia_export_codes_", ""))
    except ValueError:
        await callback.answer("ID invalido", show_alert=True)
        return

    with get_service(TriviaDiscountService) as trivia_service:
        promo = trivia_service.get_promotion_config(promo_id)

        if not promo:
            await callback.answer("Promocion no encontrada", show_alert=True)
            return

    with get_service(TriviaAdminService) as admin_service:
        csv_content = admin_service.export_codes_csv(promo_id)

        # Crear archivo CSV
        from io import StringIO
        import datetime as dt

        filename = f"trivia_codes_{promo_id}_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        await callback.message.answer_document(
            document=StringIO(csv_content),
            filename=filename,
            caption=f"🎩 <b>Exportacion de codigos</b>\n\n"
                    f"Promocion: {promo.name}\n"
                    f"Fecha: {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}",
            parse_mode=ParseMode.HTML
        )

        logger.info(f"CSV exportado: promocion {promo_id} por custodio {callback.from_user.id}")
        await callback.answer()


# ==================== GESTIONAR CODIGOS ====================

@router.callback_query(F.data == "trivia_manage_codes", lambda cb: is_admin(cb.from_user.id))
async def manage_codes_menu(callback: CallbackQuery):
    """Menu de gestion de codigos - Voz de Lucien"""
    with get_service(TriviaAdminService) as admin_service:
        promotions = admin_service.get_all_promotions()

        if not promotions:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Volver", callback_data="admin_trivia")]
            ])
            text = ("🎩 <b>Lucien:</b>\n\n"
                    "<i>No hay promociones disponibles...</i>\n\n"
                    "Primero debe crear una promocion.")
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
            await callback.answer()
            return

        buttons = []
        for promo in promotions:
            buttons.append([InlineKeyboardButton(
                text=promo.name[:30],
                callback_data=f"trivia_codes_promo_{promo.id}"
            )])

        buttons.append([InlineKeyboardButton(text="🔙 Volver", callback_data="admin_trivia")])

        text = ("🎩 <b>Lucien:</b>\n\n"
                "<i>Seleccione la promocion cuyos codigos desea gestionar:</i>")

        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode=ParseMode.HTML
        )
        await callback.answer()


@router.callback_query(F.data.startswith("trivia_codes_promo_"), lambda cb: is_admin(cb.from_user.id))
async def select_promotion_for_codes(callback: CallbackQuery):
    """Selecciona una promocion para ver sus codigos"""
    try:
        promo_id = int(callback.data.replace("trivia_codes_promo_", ""))
    except ValueError:
        await callback.answer("ID invalido", show_alert=True)
        return

    with get_service(TriviaDiscountService) as trivia_service:
        promo = trivia_service.get_promotion_config(promo_id)

        if not promo:
            await callback.answer("Promocion no encontrada", show_alert=True)
            return

    with get_service(TriviaAdminService) as admin_service:
        stats = admin_service.get_promotion_stats(promo_id)

    # Mostrar resumen con botones de filtro
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Exportar CSV", callback_data=f"trivia_export_codes_{promo_id}")],
        [InlineKeyboardButton(text="🔙 Volver", callback_data="trivia_manage_codes")]
    ])

    text = (f"🎩 <b>Lucien:</b>\n\n"
            f"📋 <b>Gestion de codigos: {promo.name}</b>\n\n"
            f"<b>Resumen:</b>\n"
            f"   Total: {stats.get('total_codes', 0)}\n"
            f"   Disponibles: {stats.get('available_codes', 0)}\n"
            f"   Reclamados: {stats.get('claimed_codes', 0)}\n"
            f"   Usados: {stats.get('used_codes', 0)}\n\n"
            f"<i>Use el boton de exportar para descargar todos los codigos en CSV.</i>")

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    await callback.answer()


# ==================== CONFIGURAR LIMITES ====================

@router.callback_query(F.data == "trivia_configure_limits", lambda cb: is_admin(cb.from_user.id))
async def configure_limits(callback: CallbackQuery, state: FSMContext):
    """Configura limites diarios - Voz de Lucien"""
    with get_service(TriviaAdminService) as admin_service:
        limits = admin_service.get_limits()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_trivia")]
    ])

    text = ("🎩 <b>Lucien:</b>\n\n"
            "<i>Configure los limites diarios de trivia...</i>\n\n"
            f"<b>Limites actuales:</b>\n"
            f"   Free: {limits.free_daily_limit if limits else 'N/A'}\n"
            f"   VIP: {limits.vip_daily_limit if limits else 'N/A'}\n"
            f"   VIP Exclusivo: {limits.vip_exclusive_daily_limit if limits else 'N/A'}\n\n"
            "<b>Paso 1 de 3:</b> Limite diario para visitantes free\n\n"
            "Indique el numero de juegos diarios permitidos:\n"
            "<i>Ejemplo: 7</i>")

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    await state.set_state(ManageLimitsStates.waiting_free_limit)
    await callback.answer()


@router.message(ManageLimitsStates.waiting_free_limit)
async def process_free_limit(message: Message, state: FSMContext):
    """Procesa limite free"""
    try:
        limit = int(message.text.strip())
        if limit < 0:
            raise ValueError("Debe ser 0 o mayor")
    except ValueError:
        await message.answer("Por favor indique un numero valido (0 o mayor).")
        return

    await state.update_data(free_limit=limit)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_trivia")]
    ])

    text = ("🎩 <b>Lucien:</b>\n\n"
            "<b>Paso 2 de 3:</b> Limite diario para visitantes VIP\n\n"
            "Indique el numero de juegos diarios permitidos:\n"
            "<i>Ejemplo: 15</i>")

    await message.answer(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    await state.set_state(ManageLimitsStates.waiting_vip_limit)


@router.message(ManageLimitsStates.waiting_vip_limit)
async def process_vip_limit(message: Message, state: FSMContext):
    """Procesa limite VIP"""
    try:
        limit = int(message.text.strip())
        if limit < 0:
            raise ValueError("Debe ser 0 o mayor")
    except ValueError:
        await message.answer("Por favor indique un numero valido (0 o mayor).")
        return

    await state.update_data(vip_limit=limit)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_trivia")]
    ])

    text = ("🎩 <b>Lucien:</b>\n\n"
            "<b>Paso 3 de 3:</b> Limite diario para visitantes VIP exclusivos\n\n"
            "Indique el numero de juegos diarios permitidos:\n"
            "<i>Ejemplo: 5</i>")

    await message.answer(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    await state.set_state(ManageLimitsStates.waiting_vip_exclusive_limit)


@router.message(ManageLimitsStates.waiting_vip_exclusive_limit)
async def process_vip_exclusive_limit(message: Message, state: FSMContext):
    """Procesa limite VIP exclusivo y guarda"""
    try:
        limit = int(message.text.strip())
        if limit < 0:
            raise ValueError("Debe ser 0 o mayor")
    except ValueError:
        await message.answer("Por favor indique un numero valido (0 o mayor).")
        return

    data = await state.get_data()

    with get_service(TriviaAdminService) as admin_service:
        success = admin_service.update_limits({
            'free_daily_limit': data.get('free_limit'),
            'vip_daily_limit': data.get('vip_limit'),
            'vip_exclusive_daily_limit': limit
        })

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Volver al taller", callback_data="admin_trivia")]
        ])

        if success:
            text = ("🎩 <b>Lucien:</b>\n\n"
                    "<i>Los limites han sido actualizados...</i>\n\n"
                    f"✅ Free: {data.get('free_limit')} juegos diarios\n"
                    f"✅ VIP: {data.get('vip_limit')} juegos diarios\n"
                    f"✅ VIP Exclusivo: {limit} juegos diarios\n\n"
                    "<i>Diana apreciara esta organizacion.</i>")
            logger.info(f"Trivia limits actualizados por custodio {message.from_user.id}")
        else:
            text = ("🎩 <b>Lucien:</b>\n\n"
                    "<i>Hmm... no se pudieron guardar los limites.</i>")

        await message.answer(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

    await state.clear()


# Import para datetime usado en process_promotion_type
from datetime import datetime
