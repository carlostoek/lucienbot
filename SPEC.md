# SPEC.md — Sistema de Trivias con Descuentos Progresivos

## 1. Concepto & Visión

Un juego de trivia gamificado donde los jugadores acumulan rachas de respuestas correctas para desbloquear descuentos progresivos. El sistema premia la consistencia: mientras más respuestas correctas consec cutivas, mayor es el descuento. Si el jugador falla, pierde su racha y el código generado. El administrador tiene control total sobre la configuración de niveles, códigos y duración de las promociones.

**Experiencia del jugador:** Llegar → Jugar → Ganar descuento o perder todo.

**Voz del sistema:** Elegante, misterioso, ligeramente juguetón — inspirado en Lucien.

---

## 2. Experiencia de Usuario

### 2.1 Flujo Principal

```
[Menú de Juegos] → [Iniciar Trivia] → [Pregunta] → [Respuesta]
                                              ↓
                              ┌────────────────┴────────────────┐
                              ↓                                  ↓
                         [Correcto]                        [Incorrecto]
                              ↓                                  ↓
                    [Calcular siguiente umbral]            [Mostrar resultado]
                              ↓                                  ↓
                    ┌────────┴────────┐                        Fin
                    ↓                ↓
              [Umbral alcanzado]  [Sin umbral]
                    ↓                ↓
            [Mostrar descuento    [Siguiente pregunta]
             logrado + opciones]
                    ↓
      ┌─────────────┴─────────────┐
      ↓           ↓              ↓
 [Continuar] [Retirarse]    [Salir sin código]
      ↓           ↓
  Siguiente  Reclamar código
  pregunta   + fin
      ↓
  [Nueva pregunta]
```

### 2.2 Pantallas del Jugador

#### A) Menú de Juegos
- Título: "Trivia"
- Descripción breve del juego actual
- Botón: "Jugar"
- Indicador de límite diario restante (ej: "Hoy te quedan 5 jugadas")

#### B) Pantalla de Pregunta
- Número de pregunta en curso
- Texto de la pregunta
- Contador de racha actual: "Racha: 5 🥂"
- 4 botones de respuesta (A / B / C / D)
- Botón "Abandonar" (opcional)

#### C) Pantalla de Respuesta Correcta
- Mensaje de celebración: "¡Correcto! 🥂"
- Racha actualizada
- Si se alcanzó un umbral:
  - Descuento logrado: "Has desbloqueado un X% de descuento"
  - Keyboard: [Continuar] [Retirarse] [Salir sin reclamar]
- Si no se alcanzó umbral:
  - "Siguiente pregunta en 3... 2... 1..."
  - Auto-avance tras cuenta regresiva

#### D) Pantalla de Respuesta Incorrecta
- Mensaje: "No era la respuesta correcta"
- Respuesta correcta revelada
- Si había código activo:
  - "Tu código ha sido invalidado"
  - Código mostrado como cancelado
- Fin del juego

#### E) Pantalla de Descuento Reclamado
- Código de descuento destacado (ej: "TRI-A3B7C2")
- Botón "Copiar código"
- Instrucciones para usar el código
- "Tu racha ha sido reiniciada"

#### F) Pantalla de Racha Expirada (timeout 2 min)
- Mensaje: "Tu racha ha expirado"
- Código activo invalidado automáticamente

---

## 3. Modelo de Datos

### 3.1 PromotionConfig (Configuración de Promoción)

```
Campo                    Tipo        Descripción
─────────────────────────────────────────────────────────────
id                       UUID        Identificador único
name                    String      Nombre de la promoción
description             String      Descripción (para el jugador)
is_active               Boolean     Si está activa
start_date              DateTime    Inicio (null = inmediata)
end_date                DateTime    Fin (null = sin límite)
duration_days           Integer     Duración en días (para relative)
auto_reset              Boolean     Auto-reset al expirar
question_set_id         UUID        FK al set de preguntas
created_at              DateTime    Timestamp de creación
updated_at              DateTime    Timestamp de actualización
```

### 3.2 Tier (Nivel de Descuento)

```
Campo                    Tipo        Descripción
─────────────────────────────────────────────────────────────
id                       UUID        Identificador único
promotion_config_id     UUID        FK a PromotionConfig
tier_number             Integer     Número de tier (1, 2, 3...)
streak_threshold        Integer     Racha requerida para este tier
discount_percentage     Decimal     Porcentaje de descuento (ej: 10.00)
max_codes               Integer     Límite de códigos para este tier
```

### 3.3 DiscountCode (Código de Descuento)

```
Campo                    Tipo        Descripción
─────────────────────────────────────────────────────────────
id                       UUID        Identificador único
code                     String      Código generado (ej: TRI-A3B7C2)
tier_id                 UUID        FK al Tier
user_id                 UUID        FK al usuario (null = disponible)
status                  Enum        AVAILABLE / CLAIMED / USED / CANCELLED / EXPIRED
generated_at            DateTime    Timestamp de generación
claimed_at              DateTime    Timestamp de reclamación (null)
used_at                 DateTime    Timestamp de uso (null)
expires_at              DateTime    Timestamp de expiración
```

### 3.4 UserStreak (Racha del Usuario)

```
Campo                    Tipo        Descripción
─────────────────────────────────────────────────────────────
id                       UUID        Identificador único
user_id                 UUID        FK al usuario
promotion_config_id     UUID        FK a PromotionConfig (nullable)
current_streak          Integer     Racha actual
active_tier_id          UUID        FK al Tier alcanzado (null)
active_code_id          UUID        FK al DiscountCode activo (null)
streak_started_at       DateTime    Inicio de la racha
last_answered_at        DateTime    Última respuesta correcta
is_active               Boolean     Si la racha está activa
```

### 3.5 GameRecord (Registro de Partida)

```
Campo                    Tipo        Descripción
─────────────────────────────────────────────────────────────
id                       UUID        Identificador único
user_id                 UUID        FK al usuario
promotion_config_id     UUID        FK a PromotionConfig
discount_code_id        UUID        FK al DiscountCode (nullable)
game_type               Enum        STANDARD / VIP
questions_answered      Integer     Total de preguntas respondidas
correct_answers         Integer     Respuestas correctas
final_streak            Integer     Racha final al terminar
result                  Enum        WON / LOST / ABANDONED / EXPIRED
played_at               DateTime    Timestamp
```

### 3.6 QuestionSet (Set de Preguntas)

```
Campo                    Tipo        Descripción
─────────────────────────────────────────────────────────────
id                       UUID        Identificador único
name                    String      Nombre del set
description             String      Descripción
file_path               String      Ruta al archivo JSON de preguntas
is_override             Boolean     Si es un override temporal
is_active               Boolean     Si está activo
created_at              DateTime    Timestamp de creación
```

### 3.7 Question (Pregunta)

```
Campo                    Tipo        Descripción
─────────────────────────────────────────────────────────────
id                       UUID        Identificador único
question_set_id         UUID        FK al QuestionSet
question_text           Text        Texto de la pregunta
option_a                String      Opción A
option_b                String      Opción B
option_c                String      Opción C
option_d                String      Opción D
correct_option          Enum        A / B / C / D
difficulty              Enum        EASY / MEDIUM / HARD
category                String      Categoría (opcional)
```

### 3.8 TriviaConfig (Configuración Global)

```
Campo                    Tipo        Descripción
─────────────────────────────────────────────────────────────
id                       UUID        Identificador único
free_daily_limit         Integer     Jugadas diarias para free (default: 7)
vip_daily_limit          Integer     Jugadas diarias para VIP (default: 15)
vip_exclusive_daily_limit Integer     Jugadas diarias para VIP exclusivo (default: 5)
streak_timeout_minutes   Integer     Timeout de racha en minutos (default: 2)
```

---

## 4. Reglas de Negocio

### 4.1 Rachas y Tiers

- La racha se incrementa en 1 por cada respuesta correcta consecutiva
- La racha se reinicia a 0 ante una respuesta incorrecta
- Al alcanzar exactamente un `streak_threshold`, se genera el código del tier correspondiente
- **El jugador elige en cada umbral:** continuar o retirarse con el descuento

### 4.2 Generación de Códigos

- Cada tier tiene su propio pool de códigos (`max_codes`)
- El sistema verifica que haya códigos disponibles en el tier antes de generar
- Los códigos se marcan como `CLAIMED` al retirarse, `USED` al canjear, `CANCELLED` al fallar, `EXPIRED` tras timeout

### 4.3 Límites Diarios

- Los límites se resetean diariamente a las 00:00 (timezone del servidor)
- Los límites se cuentan por `game_type` (STANDARD vs VIP)
- Un juego abandonado cuenta como jugado

### 4.4 Promociones

- Una promoción puede ser:
  - **Fija:** Fechas específicas de inicio y fin
  - **Relativa:** Duración en días desde la activación
- `auto_reset` permite que una promoción relativa se reinicie automáticamente al expirar

### 4.5 Timeout de Racha

- Si pasan más de `streak_timeout_minutes` sin responder, la racha expira
- El código activo se marca como `EXPIRED`
- El jugador es notificado

---

## 5. Flujo del Administrador

### 5.1 Menú de Administración de Trivia

```
├── Configurar límites diarios
├── Gestionar promociones
│   ├── Ver todas las promociones
│   ├── Crear nueva promoción
│   ├── Editar promoción existente
│   ├── Pausar / Reanudar
│   └── Eliminar
├── Gestionar códigos
│   ├── Ver códigos por promoción
│   ├── Ver códigos por usuario
│   ├── Marcar como usado
│   ├── Cancelar código
│   └── Extender expiración
├── Gestionar sets de preguntas
│   ├── Ver sets
│   ├── Crear nuevo set
│   ├── Activar set
│   └── Desactivar overrides
└── Estadísticas
    ├── Dashboard general
    ├── Por promoción
    ├── Rankings
    └── Exportar CSV
```

### 5.2 Wizard de Creación de Promoción (17 pasos)

**Paso 1:** Tipo de promoción
- Opciones: Fija / Relativa

**Paso 2a (Fija):** Fechas
- Fecha y hora de inicio
- Fecha y hora de fin

**Paso 2b (Relativa):** Duración
- Duración en días
- ¿Auto-reset? (Sí/No)

**Paso 3:** Nombre y descripción
- Nombre interno de la promoción
- Descripción visible para el jugador

**Paso 4:** Configurar tiers
- Lista de tiers con:
  - Número de tier (1, 2, 3...)
  - Racha requerida (threshold)
  - Porcentaje de descuento
  - **Cantidad máxima de códigos** (NUEVO)
- Ejemplo:
  ```
  Tier 1: Racha 5 → 10% descuento → 5 códigos
  Tier 2: Racha 10 → 20% descuento → 6 códigos
  Tier 3: Racha 15 → 30% descuento → 2 códigos
  ```

**Paso 5:** Selección de tema
- Mostrar lista de QuestionSets disponibles
- Seleccionar uno

**Paso 6:** Confirmación
- Resumen de toda la configuración
- Botón "Crear" / "Cancelar"

### 5.3 Gestión de Códigos por Tier

El administrador puede:
- Ver cuántos códigos tiene cada tier (disponibles / total)
- Agregar códigos adicionales a un tier específico
- Ver lista de códigos de un tier específico
- Filtrar por estado (disponible, reclamado, usado, cancelado, expirado)

---

## 6. APIs Internas (Services)

### 6.1 TriviaDiscountService

| Método | Descripción |
|--------|-------------|
| `create_promotion_config(data)` | Crea promoción con tiers |
| `get_promotion_config(id)` | Obtiene config por ID |
| `get_active_promotions()` | Lista promociones activas |
| `update_promotion_config(id, data)` | Actualiza config |
| `delete_promotion_config(id)` | Elimina config |
| `pause_promotion(id)` | Pausa promoción |
| `resume_promotion(id)` | Reanuda promoción |
| `get_tier(id)` | Obtiene tier por ID |
| `get_tiers_by_promotion(promotion_id)` | Lista tiers de una promoción |
| `get_available_codes_count(tier_id)` | Códigos disponibles en un tier |
| `generate_code(tier_id, user_id)` | Genera código para usuario |
| `get_user_active_code(user_id)` | Código activo del usuario |
| `claim_code(code_id)` | Reclama código |
| `use_code(code_id)` | Marca código como usado |
| `cancel_code(code_id)` | Cancela código |
| `expire_code(code_id)` | Expira código |
| `get_codes_by_tier(tier_id, filters)` | Lista códigos con filtros |

### 6.2 GameService

| Método | Descripción |
|--------|-------------|
| `get_entry_data(user_id)` | Datos de entrada (racha, límites) |
| `load_questions(promotion_id)` | Carga preguntas del set |
| `get_random_question()` | Pregunta aleatoria |
| `get_question_by_index(index)` | Pregunta por índice |
| `check_answer(question_id, answer)` | Verifica respuesta |
| `process_answer(user_id, answer)` | Procesa respuesta + lógica |
| `get_active_promotion()` | Obtiene promo activa |
| `invalidate_streak(user_id)` | Invalida racha |
| `reset_streak(user_id)` | Reinicia racha |
| `can_play(user_id)` | ¿Puede jugar? |
| `get_daily_stats(user_id)` | Estadísticas del día |

### 6.3 TriviaAdminService

| Método | Descripción |
|--------|-------------|
| `get_limits()` | Obtiene límites globales |
| `update_limits(data)` | Actualiza límites |
| `get_all_promotions()` | Lista todas las promociones |
| `get_promotion_stats(promotion_id)` | Estadísticas de una promo |
| `get_all_codes(promotion_id)` | Todos los códigos de una promo |
| `export_codes_csv(promotion_id)` | Exporta a CSV |

---

## 7. Estados FSM

### 7.1 TriviaStreak (por usuario)

```
idle → waiting_answer → (streak_choice | game_over)
                         ↓
                   waiting_retire → idle
```

### 7.2 TriviaDiscountAdmin (wizard)

```
idle → waiting_promotion_type → waiting_dates_or_duration
  → waiting_name → waiting_description → waiting_tiers
  → waiting_question_set → waiting_confirmation → idle
```

### 7.3 TriviaLimitsAdmin

```
idle → waiting_free_limit → idle
     → waiting_vip_limit → idle
     → waiting_vip_exclusive_limit → idle
```

### 7.4 QuestionSetAdmin

```
idle → waiting_name → waiting_description
  → waiting_file_path → waiting_confirm → idle
```

---

## 8. Requisitos de Implementación

### 8.1 Indepencia de Pool por Tier
- **Cada tier tiene su propio pool de códigos**
- Un tier no puede "robar" códigos de otro tier
- Al reclamar un descuento, el código se descuenta del pool del tier correspondiente
- El administrador ve: "Tier 1: 3/5 códigos usados" (3 de 5 disponibles)

### 8.2 Validaciones
- No permitir crear promoción sin tiers
- No permitir crear promoción con tiers sin códigos disponibles
- No permitir generar código si el tier está agotado
- No permitir dois tiers con el mismo `streak_threshold`

### 8.3 Concurrencia
- Al generar código: verificar disponibilidad atómicamente (lock de fila)
- Al reclamar: verificar que el código sigue disponible

### 8.4 Logging
- Toda acción de admin logueada con: módulo, acción, user_id, target_id, resultado
- Generación, reclamación, cancelación de códigos logueados

---

## 9. Pantallas de Referencia (Mockups de Texto)

### 9.1 Menú Trivia (Jugador)

```
╔═══════════════════════════════════╗
║         🎯 TRIVIA                 ║
║                                   ║
║   Demuestra tu conocimiento y     ║
║   desbloquea descuentos exclusivos║
║                                   ║
║   ┌─────────────────────────┐     ║
║   │      ▶ JUGAR            │     ║
║   └─────────────────────────┘     ║
║                                   ║
║   Hoy te quedan: 5 jugadas        ║
║   Tu racha actual: 3 🥂           ║
╚═══════════════════════════════════╝
```

### 9.2 Pregunta

```
╔═══════════════════════════════════╗
║   Pregunta 5/10       🥂 Racha: 7 ║
║───────────────────────────────────║
║                                   ║
║   ¿Cuál es la capital de Japón?   ║
║                                   ║
║   ┌─────────┐  ┌─────────┐        ║
║   │    A    │  │    B    │        ║
║   │ Seúl    │  │ Tokio   │        ║
║   └─────────┘  └─────────┘        ║
║   ┌─────────┐  ┌─────────┐        ║
║   │    C    │  │    D    │        ║
║   │ Kioto   │  │ Osaka   │        ║
║   └─────────┘  └─────────┘        ║
║                                   ║
║   ┌─────────────────────────┐     ║
║   │      ✕ Abandonar       │     ║
║   └─────────────────────────┘     ║
╚═══════════════════════════════════╝
```

### 9.3 Umbral Alcanzado

```
╔═══════════════════════════════════╗
║         🥂 ¡FELICIDADES!          ║
║───────────────────────────────────║
║                                   ║
║   ¡Has alcanzado la racha de 10!  ║
║                                   ║
║   ┌─────────────────────────┐     ║
║   │   DESCUNTO DESBLOQUEADO │     ║
║   │        20% OFF          │     ║
║   └─────────────────────────┘     ║
║                                   ║
║   ¿Qué deseas hacer?              ║
║                                   ║
║   ┌─────────┐  ┌─────────────┐    ║
║   │ Continuar│  │ Retirarse   │    ║
║   └─────────┘  └─────────────┘    ║
║   ┌─────────────────────────┐     ║
║   │    Salir sin reclamar   │     ║
║   └─────────────────────────┘     ║
╚═══════════════════════════════════╝
```

### 9.4 Panel Admin - Detalle de Tier

```
╔═══════════════════════════════════╗
║   PROMO: San Valentín 2026       ║
║───────────────────────────────────║
║                                   ║
║   TIER 1: 10% OFF                 ║
║   Racha requerida: 5              ║
║   Códigos: 3/5 disponibles       ║
║   [███░░] 3 usados de 5          ║
║                                   ║
║   TIER 2: 20% OFF                 ║
║   Racha requerida: 10             ║
║   Códigos: 6/6 disponibles       ║
║   [░░░░░░░] 0 usados de 6       ║
║                                   ║
║   TIER 3: 30% OFF                 ║
║   Racha requerida: 15             ║
║   Códigos: 1/2 disponibles       ║
║   [█░░] 1 usado de 2             ║
║                                   ║
║   [+ Agregar códigos al Tier 1]  ║
╚═══════════════════════════════════╝
```

---

## 10. Criterios de Éxito

| ID | Criterio | Validación |
|----|----------|------------|
| CE-01 | Un jugador puede completar una racha y reclamar un descuento | Test E2E |
| CE-02 | Cada tier tiene pool independiente de códigos | Test unitario |
| CE-03 | Admin puede crear promoción con 3 tiers, cada uno con cantidad diferente de códigos | Test E2E |
| CE-04 | Al agotar códigos de un tier, ese tier ya no se ofrece | Test unitario |
| CE-05 | Los límites diarios se respetan | Test unitario |
| CE-06 | El timeout de 2 min invalida el código | Test |
| CE-07 | Estadísticas muestran códigos por tier | Test E2E |

---

## 11. Dependencias

- AIogram 3.x (bot framework)
- SQLAlchemy (ORM)
- Alembic (migraciones)
- APScheduler (jobs programados)
- FSM con MemoryStorage o RedisStorage

---

## 12. Alcance de Esta Spec

**Incluido:**
- Sistema de trivia con rachas
- Descuentos progresivos por tiers
- Pool independiente de códigos por tier
- Wizard de configuración de promociones para admin
- Límites diarios por tipo de usuario
- Timeout de racha

**Excluido de esta spec:**
- Trivia VIP (será especificación aparte)
- Sistema de besitos/recompensas (ya existe)
- Narrativa/historias (ya existe)
