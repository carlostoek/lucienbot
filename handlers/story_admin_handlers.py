"""
Handlers de Narrativa para Administradores - Lucien Bot

Gestion de nodos de historia, arquetipos, logros y estadisticas.
Con la voz caracteristica de Lucien.
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode

from config.settings import bot_config
from services.story_service import StoryService
from models.models import NodeType, ArchetypeType
import json
import logging

logger = logging.getLogger(__name__)
router = Router()


# Estados para FSM
class NodeWizardStates(StatesGroup):
    waiting_title = State()
    waiting_content = State()
    selecting_type = State()
    waiting_chapter = State()
    waiting_requirements = State()
    waiting_cost = State()
    confirming = State()


class ChoiceWizardStates(StatesGroup):
    selecting_node = State()
    waiting_text = State()
    selecting_next_node = State()
    waiting_archetype_points = State()
    confirming = State()


class ArchetypeWizardStates(StatesGroup):
    selecting_type = State()
    waiting_name = State()
    waiting_description = State()
    waiting_welcome = State()
    confirming = State()


def is_admin(user_id: int) -> bool:
    return user_id in bot_config.ADMIN_IDS


# ==================== MENU PRINCIPAL ====================

@router.callback_query(F.data == "admin_narrative", lambda cb: is_admin(cb.from_user.id))
async def admin_narrative_menu(callback: CallbackQuery):
    """Menu de administracion de narrativa - Voz de Lucien"""
    story_service = StoryService()
    stats = story_service.get_story_stats()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Forjar fragmento", callback_data="create_node")],
        [InlineKeyboardButton(text="📋 Ver fragmentos", callback_data="list_nodes")],
        [InlineKeyboardButton(text="🔗 Gestionar opciones", callback_data="manage_choices")],
        [InlineKeyboardButton(text="🎭 Gestionar arquetipos", callback_data="manage_archetypes")],
        [InlineKeyboardButton(text="🏆 Gestionar logros", callback_data="manage_achievements")],
        [InlineKeyboardButton(text="📊 Observar el pulso", callback_data="story_stats")],
        [InlineKeyboardButton(text="🔙 Volver al sanctum", callback_data="admin_gamification")]
    ])

    text = (f"🎩 <b>Lucien:</b>\n\n"
            f"<i>Ah... los Hilos de la Historia de Diana.</i>\n\n"
            f"Aqui es donde se teje la narrativa que los visitantes experimentaran. "
            f"Cada fragmento, cada decision, cada arquetipo... todo se orquesta desde aqui.\n\n"
            f"📊 <b>El estado de los Fragmentos:</b>\n"
            f"   • Fragmentos activos: {stats['total_nodes']}\n"
            f"   • Capitulos: {stats['total_chapters']}\n"
            f"   • Visitantes en la historia: {stats['total_users']}\n"
            f"   • Han completado: {stats['completed_users']}\n"
            f"   • Logros disponibles: {stats['total_achievements']}\n\n"
            f"<i>Que aspecto de la narrativa requiere su atencion?</i>")

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    await callback.answer()


# ==================== CREAR NODO ====================

@router.callback_query(F.data == "create_node", lambda cb: is_admin(cb.from_user.id))
async def create_node_start(callback: CallbackQuery, state: FSMContext):
    """Inicia wizard de creacion de nodo - Voz de Lucien"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_narrative")]
    ])

    text = ("🎩 <b>Lucien:</b>\n\n"
            "<i>Vamos a forjar un nuevo fragmento de la historia...</i>\n\n"
            "<b>Paso 1:</b> El titulo del fragmento\n\n"
            "Indique un titulo evocador:\n"
            "<i>Ejemplo: El Primer Encuentro</i>")

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    await state.set_state(NodeWizardStates.waiting_title)
    await callback.answer()


@router.message(NodeWizardStates.waiting_title)
async def process_node_title(message: Message, state: FSMContext):
    """Procesa titulo del nodo - Voz de Lucien"""
    title = message.text.strip()
    if len(title) < 3:
        await message.answer("El titulo debe tener al menos 3 caracteres.")
        return

    await state.update_data(title=title)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_narrative")]
    ])

    text = ("🎩 <b>Lucien:</b>\n\n"
            "<b>Paso 2:</b> El contenido del fragmento\n\n"
            "Escriba el texto que Diana compartira en este momento:\n\n"
            "<i>Puede usar HTML para formato: &lt;b&gt;negrita&lt;/b&gt;, &lt;i&gt;cursiva&lt;/i&gt;, etc.</i>")

    await message.answer(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    await state.set_state(NodeWizardStates.waiting_content)


@router.message(NodeWizardStates.waiting_content)
async def process_node_content(message: Message, state: FSMContext):
    """Procesa contenido del nodo - Voz de Lucien"""
    content = message.text.strip()
    if len(content) < 10:
        await message.answer("El contenido debe tener al menos 10 caracteres.")
        return

    await state.update_data(content=content)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Narrativo", callback_data="node_type_narrative")],
        [InlineKeyboardButton(text="🎭 Decision", callback_data="node_type_decision")],
        [InlineKeyboardButton(text="🏁 Final", callback_data="node_type_ending")],
        [InlineKeyboardButton(text="❓ Cuestionario", callback_data="node_type_quiz")],
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_narrative")]
    ])

    text = ("🎩 <b>Lucien:</b>\n\n"
            "<b>Paso 3:</b> Tipo de fragmento\n\n"
            "Seleccione que tipo de momento es este:")

    await message.answer(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    await state.set_state(NodeWizardStates.selecting_type)


@router.callback_query(NodeWizardStates.selecting_type, F.data.startswith("node_type_"))
async def select_node_type(callback: CallbackQuery, state: FSMContext):
    """Selecciona tipo de nodo - Voz de Lucien"""
    type_map = {
        "node_type_narrative": NodeType.NARRATIVE,
        "node_type_decision": NodeType.DECISION,
        "node_type_ending": NodeType.ENDING,
        "node_type_quiz": NodeType.QUIZ
    }

    node_type = type_map.get(callback.data)
    if not node_type:
        await callback.answer("Tipo no valido", show_alert=True)
        return

    await state.update_data(node_type=node_type)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_narrative")]
    ])

    text = ("🎩 <b>Lucien:</b>\n\n"
            "<b>Paso 4:</b> Capitulo\n\n"
            "Indique a que capitulo pertenece este fragmento (numero):\n"
            "<i>Ejemplo: 1</i>")

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    await state.set_state(NodeWizardStates.waiting_chapter)
    await callback.answer()


@router.message(NodeWizardStates.waiting_chapter)
async def process_node_chapter(message: Message, state: FSMContext):
    """Procesa capitulo del nodo - Voz de Lucien"""
    try:
        chapter = int(message.text.strip())
        if chapter < 1:
            raise ValueError("Debe ser mayor a 0")
    except ValueError:
        await message.answer("Por favor indique un numero valido mayor a 0.")
        return

    await state.update_data(chapter=chapter)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌸 Cualquiera", callback_data="req_archetype_none")],
        [InlineKeyboardButton(text="🎭 El Seductor", callback_data="req_archetype_seductor")],
        [InlineKeyboardButton(text="👁️ El Observador", callback_data="req_archetype_observer")],
        [InlineKeyboardButton(text="💎 El Devoto", callback_data="req_archetype_devoto")],
        [InlineKeyboardButton(text="🗺️ El Explorador", callback_data="req_archetype_explorador")],
        [InlineKeyboardButton(text="🌑 El Misterioso", callback_data="req_archetype_misterioso")],
        [InlineKeyboardButton(text="🔥 El Intrepido", callback_data="req_archetype_intrepido")],
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_narrative")]
    ])

    text = ("🎩 <b>Lucien:</b>\n\n"
            "<b>Paso 5:</b> Requisitos de arquetipo\n\n"
            "Este fragmento esta disponible para todos, "
            "o solo para quienes han despertado un arquetipo especifico?")

    await message.answer(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    await state.set_state(NodeWizardStates.waiting_requirements)


@router.callback_query(NodeWizardStates.waiting_requirements, F.data.startswith("req_archetype_"))
async def select_archetype_requirement(callback: CallbackQuery, state: FSMContext):
    """Selecciona requisito de arquetipo - Voz de Lucien"""
    archetype_map = {
        "req_archetype_none": None,
        "req_archetype_seductor": ArchetypeType.SEDUCTOR,
        "req_archetype_observer": ArchetypeType.OBSERVER,
        "req_archetype_devoto": ArchetypeType.DEVOTO,
        "req_archetype_explorador": ArchetypeType.EXPLORADOR,
        "req_archetype_misterioso": ArchetypeType.MISTERIOSO,
        "req_archetype_intrepido": ArchetypeType.INTREPIDO
    }

    required_archetype = archetype_map.get(callback.data)
    await state.update_data(required_archetype=required_archetype)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💋 Sin costo", callback_data="node_cost_0")],
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_narrative")]
    ])

    text = ("🎩 <b>Lucien:</b>\n\n"
            "<b>Paso 6:</b> Costo en besitos\n\n"
            "Indique cuantos besitos cuesta acceder a este fragmento:\n"
            "<i>Ejemplo: 50 (o 0 para gratuito)</i>")

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    await state.set_state(NodeWizardStates.waiting_cost)
    await callback.answer()


@router.callback_query(NodeWizardStates.waiting_cost, F.data == "node_cost_0")
async def node_cost_zero(callback: CallbackQuery, state: FSMContext):
    """Costo cero - Voz de Lucien"""
    await state.update_data(cost_besitos=0)
    await show_node_confirmation(callback, state)


@router.message(NodeWizardStates.waiting_cost)
async def process_node_cost(message: Message, state: FSMContext):
    """Procesa costo del nodo - Voz de Lucien"""
    try:
        cost = int(message.text.strip())
        if cost < 0:
            raise ValueError("Debe ser 0 o mayor")
    except ValueError:
        await message.answer("Por favor indique un numero valido (0 o mayor).")
        return

    await state.update_data(cost_besitos=cost)
    await show_node_confirmation(message, state)


async def show_node_confirmation(target, state: FSMContext):
    """Muestra confirmacion del nodo - Voz de Lucien"""
    data = await state.get_data()

    title = data.get('title', '')
    content = data.get('content', '')[:100] + '...' if len(data.get('content', '')) > 100 else data.get('content', '')
    node_type = data.get('node_type', NodeType.NARRATIVE)
    chapter = data.get('chapter', 1)
    required_archetype = data.get('required_archetype')
    cost_besitos = data.get('cost_besitos', 0)

    archetype_text = "Cualquiera" if not required_archetype else required_archetype.value.title()

    text = (f"🎩 <b>Lucien:</b>\n\n"
            f"<i>Permitame confirmar el fragmento...</i>\n\n"
            f"📖 <b>{title}</b>\n"
            f"Tipo: {node_type.value.title()}\n"
            f"Capitulo: {chapter}\n"
            f"Arquetipo requerido: {archetype_text}\n"
            f"Costo: {cost_besitos} besitos\n\n"
            f"Contenido:\n<i>{content}</i>\n\n"
            f"<i>Desea forjar este fragmento?</i>")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Forjar fragmento", callback_data="confirm_create_node")],
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_narrative")]
    ])

    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    else:
        await target.answer(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

    await state.set_state(NodeWizardStates.confirming)


@router.callback_query(NodeWizardStates.confirming, F.data == "confirm_create_node")
async def confirm_create_node(callback: CallbackQuery, state: FSMContext):
    """Crea el nodo - Voz de Lucien"""
    data = await state.get_data()
    story_service = StoryService()

    try:
        node = story_service.create_node(
            title=data.get('title'),
            content=data.get('content'),
            node_type=data.get('node_type'),
            chapter=data.get('chapter', 1),
            required_archetype=data.get('required_archetype'),
            cost_besitos=data.get('cost_besitos', 0),
            created_by=callback.from_user.id
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Agregar opciones", callback_data=f"add_choices_{node.id}")],
            [InlineKeyboardButton(text="🔙 Volver", callback_data="admin_narrative")]
        ])

        text = (f"🎩 <b>Lucien:</b>\n\n"
                f"<i>Excelente. El fragmento ha sido forjado...</i>\n\n"
                f"📖 <b>{node.title}</b>\n\n"
                f"<i>Ahora puede agregar opciones de decision si es necesario.</i>")

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        logger.info(f"Fragmento creado: {node.title} por custodio {callback.from_user.id}")

    except Exception as e:
        logger.error(f"Error forjando fragmento: {e}")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Volver", callback_data="admin_narrative")]
        ])
        text = ("🎩 <b>Lucien:</b>\n\n"
                "<i>Hmm... algo inesperado ha ocurrido.</i>\n\n"
                "Permitame consultar con Diana sobre este inconveniente.")
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

    await state.clear()
    await callback.answer()


# ==================== LISTAR NODOS ====================

@router.callback_query(F.data == "list_nodes", lambda cb: is_admin(cb.from_user.id))
async def list_nodes(callback: CallbackQuery):
    """Lista todos los nodos - Voz de Lucien"""
    story_service = StoryService()
    nodes = story_service.get_all_nodes()

    if not nodes:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Forjar fragmento", callback_data="create_node")],
            [InlineKeyboardButton(text="🔙 Volver", callback_data="admin_narrative")]
        ])
        text = ("🎩 <b>Lucien:</b>\n\n"
                "<i>Los Fragmentos aun estan vacios...</i>\n\n"
                "Comience forjando el primer fragmento de la historia.")
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        await callback.answer()
        return

    text = "🎩 <b>Lucien:</b>\n\n"
    text += "<i>Los fragmentos de la historia:</i>\n\n"

    buttons = []
    current_chapter = 0

    for node in nodes:
        if node.chapter != current_chapter:
            current_chapter = node.chapter
            text += f"\n📚 <b>Capitulo {current_chapter}</b>\n"

        status = "✅" if node.is_active else "❌"
        node_type_emoji = {
            NodeType.NARRATIVE: "📖",
            NodeType.DECISION: "🎭",
            NodeType.ENDING: "🏁",
            NodeType.QUIZ: "❓"
        }.get(node.node_type, "📄")

        text += f"{status} {node_type_emoji} {node.title[:30]}\n"

        buttons.append([InlineKeyboardButton(
            text=f"{status} {node.title[:35]}",
            callback_data=f"node_detail_{node.id}"
        )])

    buttons.append([InlineKeyboardButton(text="🔙 Volver", callback_data="admin_narrative")])

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode=ParseMode.HTML)
    await callback.answer()


# ==================== ESTADISTICAS ====================

@router.callback_query(F.data == "story_stats", lambda cb: is_admin(cb.from_user.id))
async def story_stats(callback: CallbackQuery):
    """Muestra estadisticas de la narrativa - Voz de Lucien"""
    story_service = StoryService()
    stats = story_service.get_story_stats()

    # Distribucion de arquetipos
    archetype_text = ""
    for archetype, count in stats['archetype_distribution'].items():
        if count > 0:
            archetype_text += f"   • {archetype.title()}: {count}\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Volver", callback_data="admin_narrative")]
    ])

    text = (f"🎩 <b>Lucien:</b>\n\n"
            f"📊 <b>El pulso de los Fragmentos:</b>\n\n"
            f"📖 <b>Fragmentos:</b>\n"
            f"   • Activos: {stats['total_nodes']}\n"
            f"   • Capitulos: {stats['total_chapters']}\n\n"
            f"👥 <b>Visitantes:</b>\n"
            f"   • En la historia: {stats['total_users']}\n"
            f"   • Han completado: {stats['completed_users']}\n\n"
            f"🎭 <b>Distribucion de arquetipos:</b>\n"
            f"{archetype_text}\n"
            f"🏆 <b>Logros disponibles:</b> {stats['total_achievements']}")

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    await callback.answer()


# ==================== GESTIONAR ARQUETIPOS ====================

@router.callback_query(F.data == "manage_archetypes", lambda cb: is_admin(cb.from_user.id))
async def manage_archetypes(callback: CallbackQuery):
    """Menu de gestion de arquetipos - Voz de Lucien"""
    story_service = StoryService()
    archetypes = story_service.get_all_archetypes()

    buttons = []

    # Mostrar arquetipos existentes
    for archetype in archetypes:
        buttons.append([InlineKeyboardButton(
            text=f"🎭 {archetype.name}",
            callback_data=f"archetype_detail_{archetype.archetype_type.value}"
        )])

    # Opcion para crear nuevo
    buttons.append([InlineKeyboardButton(
        text="➕ Definir nuevo arquetipo",
        callback_data="create_archetype"
    )])
    buttons.append([InlineKeyboardButton(text="🔙 Volver", callback_data="admin_narrative")])

    text = ("🎩 <b>Lucien:</b>\n\n"
            "<i>Los arquetipos que Diana ha definido...</i>\n\n"
            "Cada uno representa una faceta de quienes experimentan los Fragmentos.")

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode=ParseMode.HTML)
    await callback.answer()


# ==================== GESTIONAR LOGROS ====================

@router.callback_query(F.data == "manage_achievements", lambda cb: is_admin(cb.from_user.id))
async def manage_achievements(callback: CallbackQuery):
    """Menu de gestion de logros - Voz de Lucien"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Crear reconocimiento", callback_data="create_achievement")],
        [InlineKeyboardButton(text="📋 Ver reconocimientos", callback_data="list_achievements")],
        [InlineKeyboardButton(text="🔙 Volver", callback_data="admin_narrative")]
    ])

    text = ("🎩 <b>Lucien:</b>\n\n"
            "<i>Los reconocimientos que los visitantes pueden obtener...</i>\n\n"
            "Cada logro es un hito en su viaje por los Fragmentos de Diana.")

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    await callback.answer()


# ==================== GESTIONAR OPCIONES ====================

@router.callback_query(F.data == "manage_choices", lambda cb: is_admin(cb.from_user.id))
async def manage_choices(callback: CallbackQuery):
    """Menu de gestion de opciones - Voz de Lucien"""
    story_service = StoryService()
    nodes = story_service.get_all_nodes()

    # Solo nodos de decision
    decision_nodes = [n for n in nodes if n.node_type == NodeType.DECISION]

    if not decision_nodes:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Forjar fragmento de decision", callback_data="create_node")],
            [InlineKeyboardButton(text="🔙 Volver", callback_data="admin_narrative")]
        ])
        text = ("🎩 <b>Lucien:</b>\n\n"
                "<i>No hay fragmentos de decision...</i>\n\n"
                "Cree un fragmento de tipo 'Decision' primero.")
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        await callback.answer()
        return

    buttons = []
    for node in decision_nodes:
        buttons.append([InlineKeyboardButton(
            text=f"🎭 {node.title[:35]}",
            callback_data=f"add_choices_{node.id}"
        )])

    buttons.append([InlineKeyboardButton(text="🔙 Volver", callback_data="admin_narrative")])

    text = ("🎩 <b>Lucien:</b>\n\n"
            "<i>Seleccione el fragmento al que desea agregar opciones:</i>")

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode=ParseMode.HTML)
    await callback.answer()
