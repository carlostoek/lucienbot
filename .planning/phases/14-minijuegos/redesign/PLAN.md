# Plan: Rediseño del Sistema de Minijuegos

## Goal
Transformar el sistema de minijuegos de Lucien Bot de una experiencia funcional pero mecánica a una experiencia inmersiva y narrativa que refleje la voz elegante y misteriosa del bot. El rediseño introduce variaciones de copy, detección de "casi victorias" (near-miss), sistema de rachas en trivia, y un flujo de datos enriquecido entre services y handlers siguiendo la arquitectura handlers/ → services/ → models/ → database.

## Requirements

### Funcionales
1. **Templates de Copy**: Diccionarios con múltiples variaciones de mensajes para cada escenario (menú, dados, trivia)
2. **Near-Miss Detection**: Detectar cuando los dados son "casi ganadores" (consecutivos o suma 7) para mensajes especiales
3. **Sistema de Rachas**: Calcular y mostrar rachas de respuestas correctas en trivia
4. **Contexto Enriquecido**: Los métodos de service retornan diccionarios estructurados con toda la información necesaria para los handlers
5. **Oportunidades Restantes**: Mostrar cuántas jugadas quedan (no solo el límite)

### No Funcionales
1. **Arquitectura**: Mantener separación handlers/ → services/ → models/ → database
2. **Handlers**: Solo routing, NUNCA lógica de negocio, NUNCA acceso a DB
3. **Services**: Lógica de negocio completa, máximo 50 líneas por función
4. **Logging**: Cada acción importante debe loguear módulo, acción, user_id, resultado
5. **Voz de Lucien**: Elegante, misterioso, 3ra persona, "Visitantes" no "usuarios", nunca vulgar

## Wave Breakdown

| Wave | Foco | Archivos Principales |
|------|------|---------------------|
| **Wave 1** | Templates y métodos base | `services/game_service.py` |
| **Wave 2** | Helpers de formato de mensajes | `services/game_service.py` |
| **Wave 3** | Dados con near-miss | `services/game_service.py` |
| **Wave 4** | Trivia con rachas | `services/game_service.py` |
| **Wave 5** | Handlers simplificados | `handlers/game_user_handlers.py` |
| **Wave 6** | Teclados y verificación | `keyboards/inline_keyboards.py` |

---

### Wave 1: Templates y Metodos Base en game_service.py

**Objective:** Establecer la infraestructura de templates y métodos auxiliares que alimentarán el resto del rediseño.

#### Task 1.1: Agregar Diccionarios de Templates

**Files:** `services/game_service.py`

**Actions:**
1. Agregar `MENU_TEMPLATES` con estructura:
   - `title`: Variaciones del titulo del menu
   - `subtitle`: Variaciones del subtitulo
   - `dice_description`: Variaciones de descripcion del juego de dados
   - `trivia_description`: Variaciones de descripcion de trivia
   - `footer`: Variaciones del pie de pagina

2. Agregar `DICE_TEMPLATES` con estructura:
   - `entry_title`: Variaciones del titulo de entrada
   - `entry_intro`: Variaciones de introduccion
   - `rules`: Variaciones de explicacion de reglas
   - `win_doubles`: Variaciones para victoria con dobles
   - `win_pairs`: Variaciones para victoria con pares
   - `near_miss_consecutive`: Variaciones para dados consecutivos (ej: 3-4, 5-6)
   - `near_miss_seven`: Variaciones para suma 7
   - `loss`: Variaciones para derrota normal
   - `limit_reached`: Variaciones para limite alcanzado

3. Agregar `TRIVIA_TEMPLATES` con estructura:
   - `entry_title`: Variaciones del titulo de entrada
   - `entry_intro`: Variaciones de introduccion
   - `counter`: Variaciones del contador de oportunidades
   - `correct`: Variaciones para respuesta correcta
   - `incorrect`: Variaciones para respuesta incorrecta
   - `streak_messages`: Diccionario de mensajes por nivel de racha (2, 3, 5, 7, 10+)
   - `limit_reached`: Variaciones para limite alcanzado

**Naming:** Las variaciones deben ser listas de strings, seleccionadas aleatoriamente.

**Verification:**
- Los diccionarios contienen al menos 3 variaciones por categoria
- La voz de Lucien se mantiene en todos los templates (elegante, misteriosa)

#### Task 1.2: Implementar _select_template()

**Files:** `services/game_service.py`

**Actions:**
1. Crear metodo privado `_select_template(self, template_list: list) -> str`
2. Usar `random.choice()` para seleccionar variacion
3. Agregar logging: `logger.debug(f"game_service - _select_template - selected from {len(template_list)} variations")`

**Verification:**
- Metodo retorna string aleatorio de la lista
- No excede 5 lineas de codigo

#### Task 1.3: Implementar _is_near_miss()

**Files:** `services/game_service.py`

**Actions:**
1. Crear metodo privado `_is_near_miss(self, dice1: int, dice2: int) -> dict`
2. Retornar diccionario con:
   - `is_near_miss`: bool
   - `type`: None, 'consecutive', o 'seven'
   - `description`: String descriptivo
3. Detectar consecutivos: `abs(dice1 - dice2) == 1`
4. Detectar suma 7: `dice1 + dice2 == 7`

**Verification:**
- (3, 4) → consecutive
- (1, 6) → seven
- (2, 2) → no es near miss (es victoria)
- (1, 3) → no es near miss

#### Task 1.4: Implementar _get_today_trivia_records()

**Files:** `services/game_service.py`

**Actions:**
1. Crear metodo privado `_get_today_trivia_records(self, user_id: int) -> list`
2. Consultar GameRecord filtrando por:
   - `user_id = user_id`
   - `game_type = 'trivia'`
   - `played_at >= hoy (00:00 UTC)`
3. Ordenar por `played_at DESC`
4. Retornar lista de registros (solo necesitamos `payout` de cada uno)

**Verification:**
- Retorna lista vacia si no hay jugadas hoy
- Retorna registros ordenados por tiempo descendente

---

#### Task 1.5: Implementar _get_trivia_streak()

**Files:** `services/game_service.py`

**Actions:**
1. Crear metodo privado `_get_trivia_streak(self, user_id: int) -> int`
2. Llamar `_get_today_trivia_records(user_id)` para obtener lista
3. Iterar la lista contando victorias consecutivas (`payout > 0`)
4. Detenerse al encontrar primera derrota (`payout == 0`)
5. Retornar conteo entero

**Verification:**
- Si no hay victorias hoy → retorna 0
- Si victorias: [victoria, victoria, derrota, victoria] → retorna 2
- Solo cuenta victorias con payout > 0

#### Task 1.6: Implementar _get_streak_message()

**Files:** `services/game_service.py`

**Actions:**
1. Crear metodo privado `_get_streak_message(self, streak: int) -> Optional[str]`
2. Retornar mensaje segun nivel:
   - 0 o 1: None
   - 2-4: Mensaje nivel "calentando"
   - 5-6: Mensaje nivel "imparable"
   - 7-9: Mensaje nivel "leyenda"
   - 10+: Mensaje nivel "divino"
3. Usar `_select_template()` si hay multiples variaciones por nivel

**Verification:**
- 0 → None
- 3 → mensaje nivel calentando
- 7 → mensaje nivel leyenda
- 12 → mensaje nivel divino

---

#### Task 1.7: Implementar get_menu_data()

**Files:** `services/game_service.py`

**Actions:**
1. Crear metodo `get_menu_data(self, user_id: int) -> dict`
2. Obtener limites con `get_daily_limits(user_id)`
3. Obtener conteos de hoy con `get_today_play_count()`
4. Calcular `remaining = limit - played` para cada juego
5. Construir retorno:
   ```python
   {
       'title': _select_template(MENU_TEMPLATES['title']),
       'subtitle': _select_template(MENU_TEMPLATES['subtitle']),
       'dice_description': _select_template(MENU_TEMPLATES['dice_description']),
       'trivia_description': _select_template(MENU_TEMPLATES['trivia_description']),
       'footer': _select_template(MENU_TEMPLATES['footer']),
       'remaining_dice': int,
       'remaining_trivia': int,
       'limit_dice': int,
       'limit_trivia': int,
       'is_vip': bool
   }
   ```

**Verification:**
- Retorna diccionario con todas las claves
- `remaining` calcula correctamente (no negativo)
- `is_vip` refleja estado actual del usuario

---

### Wave 2: Helper de Formato de Mensajes

**Objective:** Centralizar la construccion de mensajes finales en el service para mantener handlers libres de logica.

#### Task 2.1: Implementar _build_dice_message()

**Files:** `services/game_service.py`

**Actions:**
1. Crear metodo privado `_build_dice_message(self, parts: dict) -> str`
2. Recibir `parts` con keys: `header`, `dice_display`, `result_text`, `reward_text`, `encouragement`
3. Construir mensaje concatenando partes no vacias:
   ```python
   lines = [parts['header'], '', parts['dice_display'], '', parts['result_text']]
   if parts.get('reward_text'):
       lines.extend(['', parts['reward_text']])
   if parts.get('encouragement'):
       lines.extend(['', parts['encouragement']])
   return '\n'.join(lines)
   ```

**Verification:**
- Retorna string formateado listo para enviar
- Omite partes vacias/nulas
- No excede 15 lineas

---

#### Task 2.2: Implementar _build_trivia_message()

**Files:** `services/game_service.py`

**Actions:**
1. Crear metodo privado `_build_trivia_message(self, parts: dict) -> str`
2. Recibir `parts` con keys: `header`, `result_text`, `correct_answer`, `reward_text`, `streak_text`, `encouragement`
3. Construir mensaje concatenando partes no vacias
4. Incluir respuesta correcta si la hay (cuando se equivoca)

**Verification:**
- Retorna string formateado listo para enviar
- Muestra respuesta correcta cuando aplica
- No excede 15 lineas

---

### Wave 3: Refactor de play_dice_game() con Near-Miss y Variaciones

**Objective:** Enriquecer la experiencia del juego de dados con deteccion de casi-victorias y variaciones de copy.

#### Task 3.1: Crear get_dice_entry_data()

**Files:** `services/game_service.py`

**Actions:**
1. Crear metodo `get_dice_entry_data(self, user_id: int) -> dict`
2. Obtener limites con `get_daily_limits(user_id)`
3. Obtener jugadas de hoy con `get_today_play_count(user_id, 'dice')`
4. Calcular `remaining = limit - played`
5. Construir retorno:
   ```python
   {
       'title': _select_template(DICE_TEMPLATES['entry_title']),
       'intro': _select_template(DICE_TEMPLATES['entry_intro']),
       'rules': _select_template(DICE_TEMPLATES['rules']),
       'remaining': remaining,
       'limit': limit,
       'is_vip': is_user_vip(user_id)
   }
   ```
6. Agregar logging de la accion

**Verification:**
- Retorna diccionario con todas las claves
- `remaining` calcula correctamente (no negativo)

#### Task 3.2: Refactorizar play_dice_game()

**Files:** `services/game_service.py`

**Actions:**
1. Modificar estructura de retorno para incluir mas contexto:
   ```python
   {
       'dice1': int,
       'dice2': int,
       'sum': int,
       'won': bool,
       'win_type': Optional[str],  # 'doubles', 'pairs', None
       'is_near_miss': bool,
       'near_miss_type': Optional[str],  # 'consecutive', 'seven', None
       'besitos': int,
       'remaining_after': int,
       'message_parts': {
           'header': str,
           'dice_display': str,
           'result_text': str,
           'reward_text': Optional[str],
           'encouragement': Optional[str]
       },
       'limit_reached': bool,
       'limit_message': Optional[str]
   }
   ```

2. Despues de lanzar dados, llamar `_is_near_miss()`
3. Seleccionar template segun resultado:
   - Victoria dobles → `win_doubles`
   - Victoria pares → `win_pairs`
   - Near miss → `near_miss_{type}`
   - Derrota → `loss`
4. Construir `message_parts` en lugar de string unico
5. Calcular `remaining_after = limit - (played + 1)`

**Verification:**
- Victoria con dobles: `win_type='doubles'`, `is_near_miss=False`
- Victoria con pares: `win_type='pairs'`, `is_near_miss=False`
- (3, 4): `won=False`, `is_near_miss=True`, `near_miss_type='consecutive'`
- (1, 6): `won=False`, `is_near_miss=True`, `near_miss_type='seven'`
- (2, 5): `won=False`, `is_near_miss=False`

---

### Wave 4: Refactor de play_trivia() con Rachas y Variaciones

**Objective:** Enriquecer la experiencia de trivia con sistema de rachas y variaciones de copy.

#### Task 4.1: Crear get_trivia_entry_data()

**Files:** `services/game_service.py`

**Actions:**
1. Crear metodo `get_trivia_entry_data(self, user_id: int) -> dict`
2. Obtener limites y conteos como en get_dice_entry_data
3. Obtener racha actual con `_get_trivia_streak(user_id)`
4. Construir retorno:
   ```python
   {
       'title': _select_template(TRIVIA_TEMPLATES['entry_title']),
       'intro': _select_template(TRIVIA_TEMPLATES['entry_intro']),
       'counter_template': _select_template(TRIVIA_TEMPLATES['counter']),
       'remaining': remaining,
       'limit': limit,
       'current_streak': streak,
       'is_vip': is_user_vip(user_id),
       'can_play': bool,
       'limit_message': Optional[str]
   }
   ```

**Verification:**
- Si no puede jugar, `can_play=False` y `limit_message` poblado
- `current_streak` refleja victorias consecutivas del dia

#### Task 4.2: Refactorizar play_trivia()

**Files:** `services/game_service.py`

**Actions:**
1. Modificar estructura de retorno:
   ```python
   {
       'correct': bool,
       'besitos': int,
       'previous_streak': int,
       'new_streak': int,
       'streak_message': Optional[str],
       'message': str,  # Mensaje YA FORMATEADO listo para enviar
       'message_parts': {  # Para debugging/testing
           'header': str,
           'result_text': str,
           'correct_answer': str,  # "A", "B", "C"
           'reward_text': Optional[str],
           'streak_text': Optional[str],
           'encouragement': Optional[str]
       },
       'remaining_after': int,
       'limit_reached': bool
   }
   ```

2. Antes de procesar, obtener `previous_streak = _get_trivia_streak(user_id)`
3. Si es correcta: `new_streak = previous_streak + 1`
4. Si es incorrecta: `new_streak = 0`
5. Obtener `streak_message = _get_streak_message(new_streak)` si es correcta
6. Seleccionar template segun resultado: `correct` o `incorrect`
7. Construir `message_parts` con las partes del mensaje
8. Llamar `_build_trivia_message(message_parts)` para obtener `message` final

**Verification:**
- Respuesta correcta: `correct=True`, `new_streak = previous + 1`
- Respuesta incorrecta: `correct=False`, `new_streak=0`
- Racha 3 y correcta: incluye `streak_message` nivel calentando
- Racha 7 y correcta: incluye `streak_message` nivel leyenda

---

### Wave 5: Refactor de Handlers

**Objective:** Simplificar handlers para que solo hagan routing, delegando toda la logica a los services.

#### Task 5.1: Refactorizar game_menu()

**Files:** `handlers/game_user_handlers.py`

**Actions:**
1. Usar `service.get_menu_data(user_id)`
2. Construir texto usando templates del service
3. Mostrar oportunidades RESTANTES: "Dados: {remaining_dice} de {limit_dice} disponibles"
4. Mostrar indicador VIP si `data['is_vip']` (formato: "🎩 Lucien:" para todos)
5. Eliminar logica de calculo de limites (ahora viene del service)

**Verification:**
- Muestra "X de Y disponibles" en lugar de solo el limite
- Usa templates variados del service
- Handler tiene maximo 15 lineas

#### Task 5.2: Refactorizar game_dice()

**Files:** `handlers/game_user_handlers.py`

**Actions:**
1. Usar `service.get_dice_entry_data(user_id)`
2. Usar `result['message']` directamente (YA FORMATEADO por el service)
3. Eliminar texto hardcodeado actual

**Verification:**
- Mensaje usa variaciones del service
- Handler tiene maximo 10 lineas
- No construye mensaje, solo usa `result['message']`

#### Task 5.3: Simplificar dice_play()

**Files:** `handlers/game_user_handlers.py`

**Actions:**
1. Eliminar logica VIP actual (lineas 69-76)
2. Usar `result['message']` directamente (YA FORMATEADO por el service)
3. Si `limit_reached`, usar `result['limit_message']`

**Verification:**
- Handler tiene maximo 12 lineas
- No hay logica de negocio
- No verifica VIP (el service ya lo hace)
- No construye mensaje, solo usa `result['message']`

#### Task 5.4: Refactorizar game_trivia()

**Files:** `handlers/game_user_handlers.py`

**Actions:**
1. Usar `service.get_trivia_entry_data(user_id)`
2. Si `not data['can_play']`: mostrar `data['limit_message']` y retornar
3. Usar `data['message']` directamente (YA FORMATEADO por el service)
4. Eliminar logica de verificacion de limites actual (ahora en service)

**Verification:**
- Muestra contador de oportunidades
- Muestra racha si existe
- Handler tiene maximo 15 lineas
- No construye mensaje, solo usa `data['message']`

#### Task 5.5: Simplificar trivia_answer()

**Files:** `handlers/game_user_handlers.py`

**Actions:**
1. Eliminar logica VIP actual (lineas 140-143)
2. Usar `result['message']` directamente (YA FORMATEADO por el service)
3. Si `limit_reached`, usar `result['limit_message']`

**Verification:**
- Handler tiene maximo 12 lineas
- No hay logica de negocio
- No construye mensaje, solo usa `result['message']`

---

### Wave 6: Actualizacion de Teclados y Verificacion

**Objective:** Actualizar labels de botones y verificar integridad del sistema.

#### Task 6.1: Actualizar game_menu_keyboard()

**Files:** `keyboards/inline_keyboards.py`

**Actions:**
1. Cambiar "Dados" → "Lanzar los dados del destino"
2. Cambiar "Trivia" → "El examen de Diana"
3. Mantener emojis actuales

**Verification:**
- Botones muestran nuevo texto

#### Task 6.2: Actualizar dice_play_keyboard()

**Files:** `keyboards/inline_keyboards.py`

**Actions:**
1. Cambiar "Tirar dados" → "Invocar el destino"
2. Mantener callback_data igual

**Verification:**
- Boton muestra nuevo texto

#### Task 6.3: Actualizar trivia_keyboard()

**Files:** `keyboards/inline_keyboards.py`

**Actions:**
1. Cambiar formato de opciones de:
   `"A) {texto}"` → `"{texto}"` (solo el texto, sin prefijo A, B, C)
2. Mantener callback_data con indices 0, 1, 2
3. El service mostrara la letra en el resultado, no en el boton

**Verification:**
- Botones muestran solo texto de opcion
- Callbacks mantienen indices correctos

#### Task 6.4: Verificar Integracion

---

## Verification Criteria

### Funcionales
1. [ ] El menu de juegos muestra oportunidades RESTANTES (no solo limites)
2. [ ] Los mensajes de dados varian entre diferentes jugadas
3. [ ] Los dados (3,4) o (5,6) activan mensaje de "casi victoria" (consecutivos)
4. [ ] Los dados (1,6) o (2,5) activan mensaje de "casi victoria" (suma 7)
5. [ ] La trivia muestra la racha actual del visitante
6. [ ] Respuestas correctas consecutivas muestran mensajes de racha especiales
7. [ ] Los handlers tienen maximo 15 lineas cada uno
8. [ ] Los services manejan toda la logica de negocio y construccion de mensajes
9. [ ] Todos los mensajes usan `result['message']` ya formateado por el service

### No Funcionales
1. [ ] Todos los mensajes mantienen la voz de Lucien (elegante, misterioso)
2. [ ] Logging presente en cada accion importante
3. [ ] No hay acceso a DB desde handlers
4. [ ] No hay logica de negocio en handlers
5. [ ] Las funciones no exceden 50 lineas

### Integration
1. [ ] El bot inicia sin errores: `python bot.py`
2. [ ] El menu de juegos responde al callback `game_menu`
3. [ ] El juego de dados funciona completo
4. [ ] El juego de trivia funciona completo
5. [ ] Los limites diarios se respetan correctamente

---

## Revision History

### v2 (Correcciones post-review)
- **Fixed:** Task 1.4 dividido en 1.4 (`_get_today_trivia_records`) y 1.5 (`_get_trivia_streak`) para cumplir limite de 50 lineas
- **Fixed:** Agregado Task 1.7 (`get_menu_data`) en Wave 1 para resolver dependencia de Task 5.1
- **Fixed:** Agregada Wave 2 con `_build_dice_message` y `_build_trivia_message` para centralizar construccion de mensajes en service
- **Fixed:** Tasks de handlers (ahora Wave 5) simplificados - usan `result['message']` directamente sin construccion
- **Fixed:** Renumeracion de waves: 5 waves originales → 6 waves corregidas

---

## Rollback Plan

### Pre-conditions
1. Crear branch de trabajo: `git checkout -b gsd/minijuegos-redesign`
2. Tener working directory limpio antes de iniciar

### Rollback Steps
1. **Por Wave:**
   ```bash
   git checkout -- services/game_service.py
   git checkout -- handlers/game_user_handlers.py
   git checkout -- keyboards/inline_keyboards.py
   ```

2. **Completo:**
   ```bash
   git checkout main
   git branch -D gsd/minijuegos-redesign
   ```

3. **Database:** No hay cambios de schema, solo logica. No se requiere rollback de DB.

### Checkpoints
- [ ] Wave 1 completada y probada (Templates y metodos base)
- [ ] Wave 2 completada y probada (Helpers de formato)
- [ ] Wave 3 completada y probada (Dados con near-miss)
- [ ] Wave 4 completada y probada (Trivia con rachas)
- [ ] Wave 5 completada y probada (Handlers simplificados)
- [ ] Wave 6 completada y probada (Teclados y verificacion)

---

## Success Criteria

1. **Experiencia de Usuario:**
   - Los visitantes experimentan variedad en los mensajes
   - Las "casi victorias" crean tension y engagement
   - Las rachas en trivia motivan a continuar jugando

2. **Calidad de Codigo:**
   - Handlers simplificados (< 25 lineas)
   - Services con logica completa pero funciones < 50 lineas
   - Separacion de responsabilidades respetada

3. **Voz de Marca:**
   - Todos los mensajes suenan como Lucien
   - Experiencia inmersiva y elegante
   - Nunca vulgar, siempre misterioso

---

## Notas de Implementacion

### Para el Implementer (Claude)

1. **Prioridad:** Mantener la arquitectura handlers/ → services/ → models/ → database es NO NEGOCIABLE
2. **Templates:** Crear al menos 3 variaciones por categoria para que la experiencia sea notable
3. **Near-Miss:** Los dados (3,4) y (4,3) son consecutivos. (1,6) y (6,1) suman 7.
4. **Rachas:** Solo cuentan victorias del mismo dia (UTC). Una derrota rompe la racha.
5. **Logging:** Usar el pattern: `logger.info(f"game_service - action_name - {user_id} - result")`

### Ejemplos de Copy (para referencia)

**Near-Miss Consecutivos:**
- "Los dados bailan cerca... 3 y 4, casi un paso perfecto."
- "Un suspiro de diferencia... los numeros se tocan pero no se abrazan."

**Near-Miss Suma 7:**
- "Siete, el numero de la fortuna... pero no hoy."
- "La suma perfecta, pero no la combinacion."

**Racha Trivia:**
- Nivel 2-4: "Diana asiente con aprobacion..."
- Nivel 5-6: "Imparable. La sabiduria fluye en ti."
- Nivel 7-9: "Una leyenda nace..."
- Nivel 10+: "Divino. Los dioses envidian tu conocimiento."
