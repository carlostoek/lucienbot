# Trivia Messages - Nueva Voz de Lucien

**Plan date:** 2026-05-04

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reemplazar los mensajes de trivia con un nuevo sistema de templates usando la voz de Lucien, incluyendo barras de progreso, variaciones elegantes, y diferenciación entre estados con y sin promoción activa.

**Architecture:** El `GameService` ya tiene `TRIVIA_TEMPLATES` y `TRIVIA_VIP_TEMPLATES`. Se agregarán nuevos template groups para el flujo de promoción por racha, y se modificarán los métodos `_build_trivia_message_parts` y handlers asociados para usar estos nuevos templates.

**Tech Stack:** Python, aiogram 3.x, SQLAlchemy

---

## Archivo principal a modificar

- `services/game_service.py` — Templates y lógica de construcción de mensajes
- `handlers/game_user_handlers.py` — Handlers que muestran mensajes al usuario

---

## Task 1: Nuevos STREAK_TEMPLATES en GameService

**Files:**
- Modify: `services/game_service.py:218` (agregar después de TRIVIA_VIP_TEMPLATES)

- [ ] **Step 1: Agregar STREAK_TEMPLATES con todas las variaciones**

Reemplazar la línea 218 (fin de TRIVIA_VIP_TEMPLATES) agregando:

```python
STREAK_TEMPLATES = {
    # ========================================
    # ENTRADA A TRIVIA (con promoción activa)
    # ========================================
    'entry_header': [
        "🎩 Lucien aguarda, con paciencia infinita...",
        "🎩 Lucien observa, en silencio calculado...",
        "🎩 El salón permanece en calma..."
    ],
    'entry_promotion_bar': [
        "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n┃ 🎁 Su recompensa está cerca. Relativamente. ┃\n┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛",
        "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n┃ 🏆 El destino te observa con好奇. ┃\n┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"
    ],
    'entry_promotion_progress': [
        "▓▓░░░░░░░░  {remaining_streak} aciertos más → {discount}% de descuento",
        "▒▒▒▒░░░░░░  Faltan {remaining_streak} para su {discount}%",
        "▒▒░░░░░░░░  {remaining_streak} más hasta su recompensa"
    ],
    'entry_no_promotion': [
        "No le pido rapidez. Le pido acierto.\nSon cosas distintas, como habrá notado.",
        "La sabiduría no entiende de presión.\nPero Diana... sí.",
        "Cada respuesta es un susurro al oído de quien sabe escuchar."
    ],
    'entry_footer_question': [
        "❓ {question}",
        "❓ La pregunta aguarda su respuesta: {question}",
        "❓ Y bien, ¿qué sabe usted? {question}"
    ],

    # ========================================
    # RESPUESTA CORRECTA (con streak message)
    # ========================================
    'correct_header': [
        "🎩 Lucien hace una reverencia... medida.",
        "🎩 Lucien inclina la cabeza, reconocido.",
        "🎩 Un destello de aprobación cruza el rostro de Lucien."
    ],
    'correct_number_sabe': [
        '"{number}. Ha llegado a {number}. Debo admitir que no lo tenía del todo previsto."',
        '"{number}. Sin duda, {number} no es algo que cualquiera logre."',
        '"{number}. Y {number} sigue siendo {number}, que no es poco."'
    ],
    'correct_reward': [
        "+{besitos} besitos 💋",
        "+{besitos} besitos 💋... bien merecido.",
        "+{besitos} besito{'s' if besitos > 1 else ''} 💋"
    ],
    'correct_encouragement': [
        "Le quedan {remaining} intentos.",
        "Tiene {remaining} oportunidades restantes.",
        "{remaining} caminos aún permanecen abiertos."
    ],
    'correct_next_streak': [
        "El siguiente nivel aguarda a {next_streak} aciertos más.",
        "Faltan {next_streak} para el siguiente nivel.",
        "El destino exige {next_streak} más para la siguiente recompensa."
    ],

    # ========================================
    # RESPUESTA INCORRECTA
    # ========================================
    'incorrect_header': [
        "🎩 Lucien permanece inmóvil, procesando.",
        "🎩 Un silencio breve. Luego, Lucien habla.",
        "🎩 Lucien observa el resultado con expresión indescifrable."
    ],
    'incorrect_answer_reveal': [
        "La respuesta era: <b>{correct_answer}</b>",
        "Correcta era: <b>{correct_answer}</b>",
        "<b>{correct_answer}</b>... esa era la clave."
    ],
    'incorrect_footer': [
        "Diana dice que equivocarse es inevitable.\nLo revelador es cómo uno continúa después.",
        "Lucien ha visto errores подобни. También见证сь подобни successes.",
        "El conocimiento es así. A veces se prueba, a veces no."
    ],

    # ========================================
    # NIVEL ALCANZADO (TIER REACHED)
    # ========================================
    'tier_header': [
        "✦ NIVEL {tier} COMPLETADO ✦",
        "✦ HA ALCANZADO EL NIVEL {tier} ✦",
        "✦ NIVEL {tier} — UNLOGED ✦"
    ],
    'tier_unlock_bar': [
        "───────────────────────────────────────────",
        "───────────────────────────────────────────",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    ],
    'tier_unlock_icon': [
        "🔓",
        "🗝️",
        "✦"
    ],
    'tier_unlock_text': [
        "{discount}% de descuento — desbloqueado",
        "DESCUENTO DE {discount}% — su recompensa",
        "{discount}% de descuento — bien merecido"
    ],
    'tier_options_prompt': [
        '"¿Continuamos? Le prometo que\nlas preguntas no se volverán más sencillas."',
        '"¿Qué elige, visitante? El camino continúa,\no puede asegurar lo que tiene."',
        '"Una decisión delicada. ¿Prosperar o conservar?\nDiana aprecia ambas filosofía."'
    ],
    'tier_exit_message': [
        "El descuento aguarda. Paciente,\ncomo todo lo verdaderamente valioso.",
        "Su recompensa no irá a ninguna parte.\nA diferencia de usted, que puede volver cuando desee."
    ],

    # ========================================
    # STREAK CONTINUE (continuar jugando)
    # ========================================
    'continue_header': [
        "🎯 Continúa en su racha.",
        "🎯 La racha persiste.",
        "🎯 El camino continúa."
    ],
    'continue_progress': [
        "Acumulado: <b>{streak}</b> respuestas correctas.",
        "Lleva <b>{streak}</b> aciertos consecutivos.",
        "<b>{streak}</b>... así se construye una racha."
    ],
    'continue_next_objective': [
        "Próximo objetivo: <b>{next_streak}</b> para el <b>{next_discount}%</b>.",
        "Necesita <b>{next_streak}</b> más para el {next_discount}%.",
        "El {next_discount}% está a {next_streak} aciertos de distancia."
    ],
    'continue_warning': [
        "⚠️ Cuidado: si falla, perderá TODO el descuento acumulado.",
        "⚠️ Un tropiezo y todo vuelve a cero.",
        "⚠️ El precio del fracaso es alto. Muy alto."
    ],
    'continue_prompt_question': [
        "❓ {question}",
        "❓ La siguiente pregunta: {question}",
        "❓ ¿Sabe la respuesta? {question}"
    ],

    # ========================================
    # STREAK CONTINUE — RESPUESTA INCORRECTA (PIERDE TODO)
    # ========================================
    'continue_wrong_header': [
        "🎩 Lucien:\n\n<i>El silencio de una respuesta incorrecta es ensordecedor.</i>",
        "🎩 Lucien observa, impasible:\n\n<i>El destino no perdona.</i>",
        "🎩 Un momento de calma. Luego:\n\n<i>Bueno. Así son los juegos.</i>"
    ],
    'continue_wrong_lost': [
        "Su descuento del <b>{discount}%</b> se ha desvanecido.",
        "El <b>{discount}%</b>... evaporate. Como todo lo que no se asegura.",
        "Todo perdido. El descuento, la racha... el orgullo."
    ],
    'continue_wrong_footer': [
        "Las próximas preguntas esperarán su regreso.",
        "El juego puede volver a comenzar. Suscodes también.",
        "，下次好运气。"
    ],

    # ========================================
    # RETIRARSE (STREAK RETIRE) — ÉXITO
    # ========================================
    'retire_success_header': [
        "🎩 Lucien hace una reverencia... medida.",
        "🎩 Lucien asiente con aprobación contenida.",
        "🎩 Lucien observa cómo asegura su premio."
    ],
    'retire_success_code': [
        "📋 <b>Código:</b> <code>{code}</code>",
        "🎫 Su código: <code>{code}</code>",
        "🔑 Código: <code>{code}</code>"
    ],
    'retire_success_promo': [
        "💰 <b>Descuento:</b> {discount}% en {promo}",
        "🏷️ {discount}% de descuento en {promo}",
        "✦ {discount}% — su descuento en {promo}"
    ],
    'retire_success_footer': [
        "Usa este código al comprar la promoción.",
        "Este código es su llave. No lo pierda.\nAunque... Lucien duda que lo haga.",
        "Uselo cuando guste. No expira...\nAunque su paciencia quizás sí."
    ],
    'retire_no_codes': [
        "🎩 Lucien:\n\n<i>No se pudo generar el código.</i>\n\n<i>Parece que ya no hay códigos disponibles.</i>"
    ],

    # ========================================
    # SALIR SIN RECLAMAR (STREAK EXIT)
    # ========================================
    'exit_header': [
        "🎩 Lucien:\n\n<i>Sabe algo? La paciencia es una virtud\nque pocos cultivan hoy en día.</i>"
    ],
    'exit_discount_waiting': [
        "Su descuento del <b>{discount}%</b> aguarda\npacientemente. Como debe ser.",
        "El <b>{discount}%</b> estará aquí cuando regrese.\nEso sí... quién sabe cuándo será eso."
    ],
    'exit_footer': [
        "Podrá reclamarlo cuando lo desee.",
        "El código no se moverá. Pero usted tampoco\ntiene que hacerlo ahora.",
        "Hasta que nuestros caminos se crucen nuevamente..."
    ],

    # ========================================
    # FINAL WIN (100% DESC)
    # ========================================
    'final_win_header': [
        "🏆 ¡DESCUENTO COMPLETO! 🏆",
        "✦✦✦ 100% DESBLOQUEADO ✦✦✦",
        "🎉 ¡HAS GANADO EL JUEGO! 🎉"
    ],
    'final_win_code': [
        "📋 <b>Código:</b> <code>{code}</code>",
        "🎫 Su código: <code>{code}</code>",
        "🔑 Código: <code>{code}</code>"
    ],
    'final_win_promo': [
        "💰 <b>Descuento:</b> 100% (GRATIS) en {promo}",
        "✦ GRATIS — el precio más elegante.",
        "🏷️ 100% en {promo}... Diana se inclina ante esto."
    ],
    'final_win_footer': [
        "Usa este código para obtener el producto gratuitamente.",
        "Es su momento. El destino ha sido...\nbien, como mínimo, favorable.",
        "Úselo cuando guste. Es, técnicamente, gratis."
    ],

    # ========================================
    # LÍMITE ALCANZADO
    # ========================================
    'limit_reached_header': [
        "🎩 Lucien:\n\n<i>El examen ha terminado... por ahora.</i>",
        "🎩 Lucien cierra el libro de preguntas.",
        "🎩 Diana ha guardado sus preguntas para mañana."
    ],
    'limit_reached_body': [
        "Ha agotado todos sus intentos disponibles.",
        "No quedan más preguntas. Por hoy.",
        "El conocimiento, como el buen vino, requiere pausas."
    ],
    'limit_reached_footer': [
        "Regrese mañana. El descanso también es sabiduría.",
        "Hasta que nuestros caminos se crucen nuevamente...",
        "Que la curiosidad lo guíe de vuelta pronto."
    ]
}
```

- [ ] **Step 2: Ejecutar test de sintaxis**

Run: `python -c "import ast; ast.parse(open('services/game_service.py').read())"`
Expected: Sin errores de sintaxis

- [ ] **Step 3: Commit**

```bash
git add services/game_service.py
git commit -m "feat(trivia): add STREAK_TEMPLATES with Lucien voice variations"
```

---

## Task 2: Helper para Barra de Progreso

**Files:**
- Modify: `services/game_service.py:238` (después de `_select_template`)

- [ ] **Step 1: Agregar helper de barra de progreso**

```python
def _build_progress_bar(self, current: int, total: int, length: int = 10) -> str:
    """Construye una barra de progreso ASCII"""
    filled = int(length * current / total) if total > 0 else 0
    bar = "▓" * filled + "░" * (length - filled)
    return f" [{bar}]"

def _build_streak_promotion_text(
    self,
    current_streak: int,
    required_streak: int,
    discount: int,
    time_remaining: str = None
) -> str:
    """Construye el bloque de promoción con barra de progreso"""
    remaining = max(0, required_streak - current_streak)

    # Barra de progreso
    progress = self._build_progress_bar(current_streak, required_streak, 10)

    # Template de progreso
    progress_template = self._select_template(self.STREAK_TEMPLATES['entry_promotion_progress'])
    progress_text = progress_template.format(
        remaining_streak=remaining,
        discount=discount
    )

    result = f"{progress} {progress_text}"

    if time_remaining:
        result += f"\n⏳ La oferta expira en: {time_remaining}"

    return result
```

- [ ] **Step 2: Testear sintaxis**

Run: `python -c "import ast; ast.parse(open('services/game_service.py').read())"`
Expected: Sin errores

- [ ] **Step 3: Commit**

```bash
git add services/game_service.py
git commit -m "feat(trivia): add _build_progress_bar and _build_streak_promotion_text helpers"
```

---

## Task 3: Modificar `get_trivia_entry_data` con nuevo formato

**Files:**
- Modify: `services/game_service.py:569-600` (método `get_trivia_entry_data`)

- [ ] **Step 1: Reemplazar el método completo**

```python
def get_trivia_entry_data(self, user_id: int) -> dict:
    """Obtiene datos enriquecidos para la entrada de trivia"""
    limits = self.get_daily_limits(user_id)
    played = self.get_today_play_count(user_id, 'trivia')
    remaining = max(0, limits['trivia_limit'] - played)
    streak = self._get_trivia_streak(user_id)

    can_play = remaining > 0
    limit_message = None
    if not can_play:
        limit_message = self._select_template(self.TRIVIA_TEMPLATES['limit_reached'])
        is_vip = self.is_user_vip(user_id)
        if not is_vip:
            limit_message += "\n\nLos caminos de VIP siempre tienen más oportunidades..."

    # Información de descuento por racha
    discount_info = self._get_trivia_discount_info(user_id)
    has_promotion = discount_info is not None

    logger.info(f"game_service - get_trivia_entry_data - {user_id} - remaining:{remaining}, streak:{streak}")

    return {
        'title': self._select_template(self.TRIVIA_TEMPLATES['entry_title']),
        'intro': self._select_template(self.TRIVIA_TEMPLATES['entry_intro']),
        'counter_template': self._select_template(self.TRIVIA_TEMPLATES['counter']),
        'remaining': remaining,
        'limit': limits['trivia_limit'],
        'current_streak': streak,
        'is_vip': self.is_user_vip(user_id),
        'can_play': can_play,
        'limit_message': limit_message,
        'discount_info': discount_info,
        'has_promotion': has_promotion
    }
```

- [ ] **Step 2: Commit**

```bash
git add services/game_service.py
git commit -m "feat(trivia): update get_trivia_entry_data with has_promotion flag"
```

---

## Task 4: Modificar `_build_trivia_message_parts` para nuevo formato

**Files:**
- Modify: `services/game_service.py:743-788` (método `_build_trivia_message_parts`)

- [ ] **Step 1: Reemplazar el método completo**

```python
def _build_trivia_message_parts(self, is_correct: bool, question: dict,
                                 besitos: int, streak_message: Optional[str],
                                 remaining: int) -> dict:
    """Construye las partes del mensaje de trivia"""
    # Respuesta correcta (para formatear templates)
    letters = ["A", "B", "C", "D"]
    answer_idx = min(question['answer'], len(letters) - 1)
    correct_letter = letters[answer_idx]
    correct_answer_text = f"{correct_letter}) {question['opts'][question['answer']]}"

    # Header según resultado
    if is_correct:
        header = self._select_template(self.TRIVIA_TEMPLATES['correct'])
    else:
        header_template = self._select_template(self.TRIVIA_TEMPLATES['incorrect'])
        header = header_template.format(correct_answer=correct_answer_text)

    # Resultado de la respuesta - simplificado
    result_text = None

    # Respuesta correcta (solo se muestra si se equivocó - ahora ya está en el header)
    correct_answer = None

    # Recompensa
    reward_text = None
    if is_correct:
        reward_text = f"+{besitos} besitos 💋"

    # Mensaje de racha
    streak_text = streak_message

    # Mensaje de oportunidades/ánimo
    encouragement = None
    if remaining > 0:
        encouragement = f"Le quedan {remaining} intentos."
    else:
        encouragement = "Ha agotado sus preguntas por hoy."

    return {
        'header': header,
        'result_text': result_text,
        'correct_answer': correct_answer,
        'reward_text': reward_text,
        'streak_text': streak_text,
        'encouragement': encouragement
    }
```

- [ ] **Step 2: Commit**

```bash
git add services/game_service.py
git commit -m "refactor(trivia): _build_trivia_message_parts simplified structure"
```

---

## Task 5: Modificar `game_trivia` handler — nuevo formato de entrada

**Files:**
- Modify: `handlers/game_user_handlers.py:94-158` (función `game_trivia`)

- [ ] **Step 1: Reemplazar la función completa**

```python
@router.callback_query(lambda c: c.data == "game_trivia")
async def game_trivia(callback: CallbackQuery):
    """Inicia trivia con pregunta aleatoria"""
    user_id = callback.from_user.id

    with get_service(GameService) as service:
        data = service.get_trivia_entry_data(user_id)

        if not data['can_play']:
            await callback.message.edit_text(
                data['limit_message'],
                reply_markup=game_menu_keyboard()
            )
            await callback.answer()
            return

        question, question_idx = service.get_random_question()

        if question is None:
            await callback.message.edit_text(
                "🎩 Lucien:\n\n<i>Las preguntas están en el taller de Lucien.\nRegresa más tarde.</i>",
                reply_markup=game_menu_keyboard()
            )
            await callback.answer()
            return

    # Construir header con barra decorativa
    header = service._select_template(service.STREAK_TEMPLATES['entry_header'])

    # Construir línea de stats
    stats_line = f"🔥 Racha: {data['current_streak']}  •  📜 Intentos: {data['remaining']}/{data['limit']}"

    # Construir bloque de promoción si existe
    discount_info = data.get('discount_info')
    if discount_info and discount_info.get('promotion_id'):
        promo_header = service._select_template(service.STREAK_TEMPLATES['entry_promotion_bar'])
        promo_progress = service._build_streak_promotion_text(
            current_streak=data['current_streak'],
            required_streak=discount_info['required_streak'],
            discount=discount_info['discount_percentage'],
            time_remaining=discount_info.get('time_remaining')
        )
        no_promo_text = service._select_template(service.STREAK_TEMPLATES['entry_no_promotion'])
        promotion_block = f"\n{promo_header}\n{promo_progress}\n{no_promo_text}\n"
    else:
        promotion_block = ""

    # Construir texto final
    question_text = service._select_template(
        service.STREAK_TEMPLATES['entry_footer_question']
    ).format(question=question['q'])

    text = (
        f"{header}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{stats_line}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{promotion_block}"
        f"────────────────────────────\n"
        f"{question_text}"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=trivia_keyboard(question, question_idx),
        parse_mode="HTML"
    )
    await callback.answer()
    logger.info(f"game_user_handlers - game_trivia - {user_id} - shown")
```

- [ ] **Step 2: Testear que el handlercompile**

Run: `python -c "from handlers.game_user_handlers import router; print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add handlers/game_user_handlers.py
git commit -m "feat(trivia): update game_trivia handler with new format and progress bar"
```

---

## Task 6: Modificar `trivia_answer` handler — nuevo formato de respuesta correcta

**Files:**
- Modify: `handlers/game_user_handlers.py:161-314` (función `trivia_answer`)

- [ ] **Step 1: Reemplazar sección de respuesta correcta con tier**

```python
# Nota: Esta es una referencia del nuevo flujo
# El código real debe adaptarse en contexto

# Caso 2: Alcanzó un tier -需要进行选择
if tier_info and tier_info.get('tier_reached'):
    current_tier = tier_info['current_tier']
    next_tier = tier_info.get('next_tier')
    is_final = tier_info.get('is_final', False)
    config_id = tier_info.get('config_id')
    tier_index = tier_info.get('tier_index', 1)

    current_discount = current_tier['discount']
    current_streak = current_tier['streak']

    # Caso 2a: Es el tier final (100% - GRATIS)
    if is_final:
        # Generar código 100% automáticamente
        with get_service(GameService) as service:
            discount = service._generate_tier_discount_code(user_id, config_id, 100)

        if discount and discount.get('code'):
            # Nuevo formato para win completo
            header_template = service._select_template(service.STREAK_TEMPLATES['final_win_header'])
            code_template = service._select_template(service.STREAK_TEMPLATES['final_win_code'])
            promo_template = service._select_template(service.STREAK_TEMPLATES['final_win_promo'])
            footer_template = service._select_template(service.STREAK_TEMPLATES['final_win_footer'])

            message = (
                f"{header_template}\n\n"
                f"{code_template.format(code=discount['code'])}\n"
                f"{promo_template.format(promo=discount.get('promotion_name', 'la promoción'))}\n\n"
                f"{footer_template}"
            )
            keyboard = streak_final_keyboard()
        else:
            keyboard = game_menu_keyboard()
    else:
        # Caso 2b: Mostrar opciones de retirarse o continuar
        next_discount = next_tier['discount'] if next_tier else None
        next_streak = next_tier['streak'] if next_tier else current_streak + 5

        # Nuevo formato de nivel alcanzado
        header_template = service._select_template(service.STREAK_TEMPLATES['tier_header'])
        unlock_template = service._select_template(service.STREAK_TEMPLATES['tier_unlock_text'])
        bar_template = service._select_template(service.STREAK_TEMPLATES['tier_unlock_bar'])
        icon_template = service._select_template(service.STREAK_TEMPLATES['tier_unlock_icon'])
        prompt_template = service._select_template(service.STREAK_TEMPLATES['tier_options_prompt'])
        encouragement_template = service._select_template(service.STREAK_TEMPLATES['correct_encouragement'])
        next_template = service._select_template(service.STREAK_TEMPLATES['correct_next_streak'])

        message = (
            f"🎩 Lucien hace una reverencia... medida.\n\n"
            f'"{current_streak}. Ha llegado a {current_streak}.\n'
            f'Debo admitir que no lo tenía del todo previsto."\n\n'
            f"{header_template.format(tier=tier_index)}\n"
            f"{bar_template}\n"
            f"  {icon_template} {unlock_template.format(discount=current_discount)}\n"
            f"{bar_template}\n\n"
            f"{encouragement_template.format(remaining=result['remaining_after'])}\n"
            f"{next_template.format(next_streak=next_streak)}\n\n"
            f"{prompt_template}"
        )

        # Guardar estado para cuando regrese
        await state.update_data(
            streak_mode=True,
            current_tier_streak=current_streak,
            current_tier_discount=current_discount,
            current_config_id=config_id,
            next_tier_streak=next_tier['streak'] if next_tier else None,
            next_tier_discount=next_tier['discount'] if next_tier else None,
            tier_index=tier_index
        )
        await state.set_state(TriviaStreakStates.waiting_streak_choice)

        keyboard = streak_choice_keyboard(current_discount)

    await callback.message.edit_text(message, reply_markup=keyboard)
    await callback.answer()
    logger.info(f"game_user_handlers - trivia_answer - {user_id} - tier_reached:{current_discount}%")
    return
```

- [ ] **Step 2: Commit**

```bash
git add handlers/game_user_handlers.py
git commit -m "feat(trivia): update trivia_answer tier reached format with Lucien voice"
```

---

## Task 7: Modificar handlers de streak (retire, exit, continue, continue_wrong)

**Files:**
- Modify: `handlers/game_user_handlers.py:540-680` (streak handlers)

- [ ] **Step 1: streak_retire handler**

```python
@router.callback_query(F.data == "streak_retire", TriviaStreakStates.waiting_streak_choice)
async def streak_retire(callback: CallbackQuery, state: FSMContext):
    """Usuario elige retirarse con su descuento actual"""
    user_id = callback.from_user.id
    data = await state.get_data()

    config_id = data.get('current_config_id')
    discount_percentage = data.get('current_tier_discount')

    if not config_id or not discount_percentage:
        await callback.message.edit_text(
            "🎩 Lucien:\n\n<i>Algo salió mal. Regresa al menú.</i>",
            reply_markup=game_menu_keyboard()
        )
        await state.clear()
        await callback.answer()
        return

    with get_service(GameService) as service:
        discount = service._generate_tier_discount_code(user_id, config_id, discount_percentage)
        # Romper racha para que si vuelve a jugar, empiece desde 1
        game_type = 'trivia_vip' if data.get('vip_mode', False) else 'trivia'
        service.reset_trivia_streak(user_id, game_type)

    await state.clear()

    if discount and discount.get('code'):
        # Usar templates de retire success
        service_instance = GameService()
        header = service_instance._select_template(service_instance.STREAK_TEMPLATES['retire_success_header'])
        code_t = service_instance._select_template(service_instance.STREAK_TEMPLATES['retire_success_code'])
        promo_t = service_instance._select_template(service_instance.STREAK_TEMPLATES['retire_success_promo'])
        footer = service_instance._select_template(service_instance.STREAK_TEMPLATES['retire_success_footer'])

        message = (
            f"{header}\n\n"
            f"{code_t.format(code=discount['code'])}\n"
            f"{promo_t.format(discount=discount_percentage, promo=discount.get('promotion_name', 'la promoción'))}\n\n"
            f"{footer}"
        )
        keyboard = discount_claim_keyboard(discount['code'])
    else:
        message = service_instance._select_template(service_instance.STREAK_TEMPLATES['retire_no_codes'])
        keyboard = game_menu_keyboard()

    await callback.message.edit_text(message, reply_markup=keyboard)
    await callback.answer()
    logger.info(f"game_user_handlers - streak_retire - {user_id} - discount:{discount_percentage}%")
```

- [ ] **Step 2: streak_exit handler**

```python
@router.callback_query(F.data == "streak_exit", TriviaStreakStates.waiting_streak_choice)
async def streak_exit(callback: CallbackQuery, state: FSMContext):
    """Usuario elige salir sin reclamar su descuento"""
    user_id = callback.from_user.id
    data = await state.get_data()

    tier_discount = data.get('current_tier_discount', 0)
    tier_index = data.get('tier_index', 0)

    await state.clear()

    service = GameService()
    header = service._select_template(service.STREAK_TEMPLATES['exit_header'])
    discount_t = service._select_template(service.STREAK_TEMPLATES['exit_discount_waiting'])
    footer = service._select_template(service.STREAK_TEMPLATES['exit_footer'])

    message = (
        f"{header}\n\n"
        f"{discount_t.format(discount=tier_discount)}\n\n"
        f"{footer}"
    )
    keyboard = game_menu_keyboard()

    await callback.message.edit_text(message, reply_markup=keyboard)
    await callback.answer()
    logger.info(f"game_user_handlers - streak_exit - {user_id} - tier:{tier_index} discount:{tier_discount}%")
```

- [ ] **Step 3: streak_continue handler**

```python
@router.callback_query(F.data == "streak_continue", TriviaStreakStates.waiting_streak_choice)
async def streak_continue(callback: CallbackQuery, state: FSMContext):
    """Usuario elige continuar para buscar mayor descuento"""
    user_id = callback.from_user.id
    data = await state.get_data()
    is_vip = data.get('vip_mode', False)

    # Verificar que aún tiene oportunidades
    with get_service(GameService) as service:
        if is_vip:
            entry_data = service.get_trivia_vip_entry_data(user_id)
        else:
            entry_data = service.get_trivia_entry_data(user_id)

        if not entry_data['can_play']:
            await callback.message.edit_text(
                entry_data['limit_message'],
                reply_markup=game_menu_keyboard()
            )
            await state.clear()
            await callback.answer()
            return

        question, question_idx = service.get_random_vip_question() if is_vip else service.get_random_question()

        if question is None:
            await callback.message.edit_text(
                "🎩 Lucien:\n\n<i>Las preguntas están en el taller de Lucien.\nRegresa más tarde.</i>",
                reply_markup=game_menu_keyboard()
            )
            await state.clear()
            await callback.answer()
            return

    # Construir mensaje de continuar
    current_streak = data.get('current_tier_streak', 0)
    next_streak_val = data.get('next_tier_streak', 0) or (current_streak + 5)
    next_discount = data.get('next_tier_discount', 0)

    service = GameService()
    header = service._select_template(service.STREAK_TEMPLATES['continue_header'])
    progress = service._select_template(service.STREAK_TEMPLATES['continue_progress'])
    next_obj = service._select_template(service.STREAK_TEMPLATES['continue_next_objective'])
    warning = service._select_template(service.STREAK_TEMPLATES['continue_warning'])
    question_t = service._select_template(service.STREAK_TEMPLATES['continue_prompt_question'])

    message = (
        f"{header}\n\n"
        f"{progress.format(streak=current_streak)}\n"
        f"{next_obj.format(next_streak=next_streak_val, next_discount=next_discount)}\n\n"
        f"{warning}\n\n"
        f"────────────────────────────\n"
        f"{question_t.format(question=question['q'])}"
    )

    # Mantener el estado para la siguiente respuesta
    await state.set_state(TriviaStreakStates.streak_continue)

    if is_vip:
        keyboard = trivia_vip_keyboard(question, question_idx)
    else:
        keyboard = trivia_keyboard(question, question_idx)

    await callback.message.edit_text(text=message, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()
    logger.info(f"game_user_handlers - streak_continue - {user_id} - next_question")
```

- [ ] **Step 4: streak_continue_wrong case**

Modificar en `trivia_answer` la sección de streak_continue + wrong:

```python
if is_streak_continue and not result['correct']:
    data = await state.get_data()
    config_id = data.get('current_config_id')
    tier_discount = data.get('current_tier_discount', 0)
    if config_id:
        with get_service(GameService) as svc:
            svc.invalidate_streak_code(user_id, config_id)
    await state.clear()
    keyboard = game_menu_keyboard()

    service = GameService()
    header = service._select_template(service.STREAK_TEMPLATES['continue_wrong_header'])
    lost = service._select_template(service.STREAK_TEMPLATES['continue_wrong_lost'])
    footer = service._select_template(service.STREAK_TEMPLATES['continue_wrong_footer'])

    message = (
        f"{header}\n\n"
        f"{lost.format(discount=tier_discount)}\n\n"
        f"<i>{footer}</i>"
    )

    await callback.message.edit_text(message, reply_markup=keyboard)
    await callback.answer()
    logger.info(f"game_user_handlers - trivia_answer - {user_id} - streak_continue_wrong")
    return
```

- [ ] **Step 5: Commit**

```bash
git add handlers/game_user_handlers.py
git commit -m "feat(trivia): update streak handlers with Lucien voice templates"
```

---

## Task 8: Modificar `trivia_vip` handler con formato equivalente

**Files:**
- Modify: `handlers/game_user_handlers.py:318-536` (game_trivia_vip y trivia_vip_answer)

- [ ] **Step 1: game_trivia_vip handler**

Aplicar formato similar a game_trivia, pero con context VIP:
- Usar `TRIVIA_VIP_TEMPLATES` para titles/intros
- Agregar emojis distintivos como `👑` en lugar de `❓`
- Incluir las mismas barras de progreso cuando hay promoción activa

- [ ] **Step 2: trivia_vip_answer handler**

Aplicar los mismos cambios que trivia_answer, pero:
- Usar `trivia_vip_keyboard` en lugar de `trivia_keyboard`
- Incluir `vip_mode=True` en el state update
- Usar los streak_continue handlers existentes (ya soportan vip_mode)

- [ ] **Step 3: Commit**

```bash
git add handlers/game_user_handlers.py
git commit -m "feat(trivia): update VIP trivia handlers with equivalent format"
```

---

## Task 9: Verificación y Pruebas

**Files:**
- Test: `tests/e2e/test_lucien_voice.py` (verificar que exista)

- [ ] **Step 1: Crear test de smoke**

```python
# tests/e2e/test_trivia_messages.py
import pytest
from services.game_service import GameService

def test_streak_templates_exist():
    """Verify all STREAK_TEMPLATES keys exist"""
    service = GameService()
    required_keys = [
        'entry_header', 'entry_promotion_bar', 'entry_promotion_progress',
        'entry_no_promotion', 'entry_footer_question',
        'correct_header', 'correct_number_sabe', 'correct_reward',
        'correct_encouragement', 'correct_next_streak',
        'tier_header', 'tier_unlock_bar', 'tier_unlock_text', 'tier_options_prompt',
        'continue_header', 'continue_progress', 'continue_next_objective',
        'continue_warning', 'continue_prompt_question',
        'continue_wrong_header', 'continue_wrong_lost', 'continue_wrong_footer',
        'retire_success_header', 'retire_success_code', 'retire_success_promo', 'retire_success_footer',
        'exit_header', 'exit_discount_waiting', 'exit_footer',
        'final_win_header', 'final_win_code', 'final_win_promo', 'final_win_footer'
    ]
    for key in required_keys:
        assert hasattr(service.STREAK_TEMPLATES, key), f"Missing template: {key}"

def test_progress_bar_builder():
    """Test progress bar generation"""
    service = GameService()
    bar = service._build_progress_bar(3, 5, 10)
    assert len(bar) == 12  # "[▓▓▓▓░░░░░░]"
    assert "▓" in bar
    assert "░" in bar

def test_streak_promotion_text():
    """Test promotion text generation"""
    service = GameService()
    text = service._build_streak_promotion_text(2, 5, 50, "10 min")
    assert "50%" in text
    assert "3" in text  # remaining streak
    assert "10 min" in text
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/e2e/test_trivia_messages.py -v`
Expected: PASS (3 tests)

- [ ] **Step 3: Commit**

```bash
git add tests/e2e/test_trivia_messages.py
git commit -m "test(trivia): add smoke tests for streak templates and helpers"
```

---

## Task 10: Commit final de consolidación

- [ ] **Step 1: Verificar que todo compila**

Run: `python -c "from bot import *; print('All imports OK')"`
Expected: Sin errores

- [ ] **Step 2: Commit final**

```bash
git add -A
git commit -m "feat(trivia): complete rewrite of trivia messages with Lucien voice

- Added STREAK_TEMPLATES with 30+ variations for all messages
- Added _build_progress_bar helper for ASCII progress bars
- Added _build_streak_promotion_text for promotion blocks
- Updated game_trivia handler with new format and progress display
- Updated trivia_answer handler with tier reached messages
- Updated all streak handlers (retire, exit, continue, continue_wrong)
- Added progress bar in trivia entry when promotion is active
- New format includes stats line, promotion bar, and question"
```

---

## Notas de Implementación

1. **Progreso de barra**: La barra usa caracteres `▓` (filled) y `░` (empty) en un formato `[▓▓░░░░░░░░]`.

2. **Tiempo restante**: Solo se muestra si `discount_info.get('time_remaining')` y `is_duration_based` son ambos truthy.

3. **Diferenciación CON/SIN promoción**: El bloque de promoción solo aparece cuando `discount_info` y `discount_info['promotion_id']` existen.

4. **Variaciones aleatorias**: Cada template tiene 2-3 variaciones para evitar repetitividad.

5. **Voz de Lucien**: Todos los templates siguen la guía de estilo (elegante, misterioso, referencias a Diana).