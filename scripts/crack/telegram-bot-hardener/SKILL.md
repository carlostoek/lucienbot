---
name: telegram-bot-hardener
description: >
  Robustece y lleva a nivel empresarial bots de Telegram escritos en Python con aiogram 3.
  Usa esta skill siempre que el usuario quiera: analizar la arquitectura de su bot, detectar
  código frágil o acoplado, generar tests (pytest + pytest-asyncio), proponer refactorizaciones,
  revisar patrones de diseño, o blindar módulos como gamificación, narrativa, administración
  de canales o minijuegos. Actívala también cuando el usuario diga "el bot se rompe", "algo
  se descompone", "quiero tests", "quiero refactorizar", "cómo mejoro mi bot", o simplemente
  suba archivos .py de un bot de Telegram.
---

# Telegram Bot Hardener

Skill para analizar, fortalecer y testear bots de Telegram (Python + aiogram 3).
Convierte código funcional-pero-frágil en sistemas robustos, desacoplados y testeables.

---

## 1. Orientación inicial

Antes de cualquier acción, identifica qué tiene el usuario:

| Situación | Acción |
|---|---|
| Sube archivos .py | Leer y hacer análisis completo (ver §3) |
| Describe el problema sin código | Pedir que comparta los archivos relevantes |
| Pide tests específicos | Ir directo a §5 |
| Pide mejoras de arquitectura | Ir directo a §6 |
| Quiere solo detectar problemas | Ejecutar `scripts/analyze_codebase.py` (ver §2) |

**El bot tiene tres sistemas principales a tener en cuenta siempre:**
- `channel_admin` — gestión de canales VIP y gratuito
- `gamification` — puntos, recompensas, interacción de usuario
- `narrative` — historia ramificada, arquetipos, minijuegos

---

## 2. Script de análisis rápido

Ejecuta esto primero si tienes acceso a los archivos del proyecto:

```bash
python telegram-bot-hardener/scripts/analyze_codebase.py <ruta_del_proyecto>
```

Detecta automáticamente: imports circulares, funciones >50 líneas, acoplamiento entre módulos,
ausencia de manejo de errores, handlers sin separación de lógica de negocio.

---

## 3. Análisis de arquitectura

Lee `references/architecture-patterns.md` para el catálogo completo de patrones.

### Checklist de diagnóstico rápido

Revisa cada archivo buscando estas señales de fragilidad:

**Acoplamiento duro (alta prioridad)**
- [ ] ¿Los handlers llaman directamente a funciones de otros módulos sin interfaces?
- [ ] ¿Se importan objetos de estado (`FSMContext`, `State`) entre módulos distintos?
- [ ] ¿La lógica de negocio está dentro de los handlers de aiogram?
- [ ] ¿Se comparten variables globales entre sistemas (gamificación ↔ narrativa)?

**Manejo de errores (alta prioridad)**
- [ ] ¿Existen bloques `try/except` genéricos que silencian errores?
- [ ] ¿Las llamadas a DB/API externas tienen manejo de reconexión?
- [ ] ¿Los callbacks de Telegram tienen `answer()` garantizado aunque falle la lógica?

**Testabilidad (media prioridad)**
- [ ] ¿Las funciones reciben sus dependencias por parámetro (inyección) o las crean internamente?
- [ ] ¿Existe lógica de negocio pura (sin `bot`, `message`, `callback`) que pueda testearse sola?
- [ ] ¿Los accesos a DB están abstraídos en un repositorio o se hacen inline?

**Consistencia de estado (alta prioridad para gamificación + narrativa)**
- [ ] ¿Las transacciones de puntos son atómicas?
- [ ] ¿El FSM de narrativa puede quedar en estado incoherente si un handler falla a mitad?
- [ ] ¿Hay validación de que un usuario no pueda ejecutar dos acciones simultáneas?

---

## 4. Patrones de refactorización a proponer

Lee `references/architecture-patterns.md` para implementaciones detalladas.

### Patrón Service Layer (más impacto)
Separa handlers de lógica de negocio. Cada sistema tiene su servicio:

```
handlers/
  gamification.py      ← solo recibe update, valida, llama servicio
services/
  gamification_service.py  ← lógica pura, testeable, sin aiogram
repositories/
  points_repository.py     ← solo acceso a datos
```

### Patrón Event Bus interno
Cuando gamificación necesita notificar a narrativa (ej: puntos ganados desbloquean capítulo),
usar eventos internos en vez de imports directos:

```python
# En vez de: from narrative import unlock_chapter
# Usar:       await event_bus.emit("points_earned", user_id=uid, points=pts)
```

### Patrón Middleware para contexto compartido
Datos que múltiples handlers necesitan (user, subscription_status, narrative_state)
deben ir en el middleware, no en imports cruzados.

---

## 5. Generación de tests

Lee `references/testing-strategy.md` para templates completos.

### Estructura de tests recomendada

```
tests/
  conftest.py              ← fixtures compartidos (bot mock, db en memoria, user factory)
  unit/
    test_gamification.py   ← lógica pura sin aiogram
    test_narrative.py
    test_channel_admin.py
  integration/
    test_points_flow.py    ← flujo completo: usuario gana puntos → se guarda → se muestra
    test_narrative_flow.py ← flujo: acción → avanza historia → persiste estado
  handlers/
    test_handlers_gamification.py  ← handlers con bot mockeado
```

### Fixtures esenciales a generar siempre

```python
# conftest.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

@pytest.fixture
def bot():
    bot = AsyncMock(spec=Bot)
    bot.id = 123456789
    return bot

@pytest.fixture
def storage():
    return MemoryStorage()

@pytest.fixture
def dp(storage):
    return Dispatcher(storage=storage)

@pytest.fixture
def make_user():
    def _make(user_id=1, username="test_user", is_premium=False):
        user = MagicMock()
        user.id = user_id
        user.username = username
        user.is_premium = is_premium
        return user
    return _make

@pytest.fixture
def make_message(bot, make_user):
    def _make(text="/start", user=None):
        msg = AsyncMock()
        msg.bot = bot
        msg.from_user = user or make_user()
        msg.text = text
        msg.answer = AsyncMock()
        msg.reply = AsyncMock()
        return msg
    return _make
```

### Tipos de tests por sistema

**Gamificación**
- Sumar puntos no excede el máximo permitido
- Canjear recompensa descuenta puntos y registra transacción
- Usuario sin puntos suficientes recibe mensaje correcto, sin error silencioso
- Dos requests simultáneos no duplican puntos (race condition)

**Narrativa**
- Avanzar en historia persiste el nuevo nodo correctamente
- Arquetipo se asigna una sola vez y no cambia con nuevas interacciones
- Estado FSM se restaura correctamente si el bot se reinicia
- Rama inválida no rompe el flujo, retorna al nodo anterior

**Channel Admin**
- Usuario que paga accede a canal VIP y es removido del gratuito
- Usuario expirado es removido de VIP sin error aunque ya no esté
- Acción de ban propaga correctamente a ambos canales

---

## 6. Mejoras de robustez específicas para aiogram 3

Lee `references/aiogram3-patterns.md` para implementaciones completas.

### Prioridad 1 — Siempre proponer

1. **ErrorHandler global**: middleware que captura toda excepción no manejada,
   responde al usuario con mensaje genérico, y loggea con contexto completo.

2. **Idempotencia en callbacks**: guardar `callback.id` procesados para evitar
   doble ejecución si Telegram reintenta el update.

3. **Timeouts en operaciones externas**: toda llamada a DB o API externa
   debe tener timeout explícito, no confiar en el default del sistema.

### Prioridad 2 — Proponer según el código

4. **FSM con transiciones explícitas**: documentar el grafo de estados de narrativa
   y validar que cada transición es intencional.

5. **Rate limiting por usuario**: middleware que bloquee spam de comandos,
   especialmente en minijuegos.

6. **Health check endpoint**: ruta `/health` que verifique DB, bot token, y
   estado de canales, para monitoreo externo.

---

## 7. Formato de entrega

Al terminar el análisis, entrega siempre en este orden:

### A) Reporte de hallazgos
```
## Hallazgos críticos (rompen el sistema)
1. [archivo:línea] Descripción del problema + impacto

## Hallazgos de fragilidad (pueden romper bajo carga/cambios)
1. ...

## Deuda técnica (no rompe hoy, pero acumula riesgo)
1. ...
```

### B) Plan de acción priorizado
```
Semana 1 (críticos):
  - [ ] Agregar ErrorHandler global
  - [ ] Separar lógica de negocio de handlers en [módulo X]

Semana 2 (tests):
  - [ ] conftest.py con fixtures base
  - [ ] Tests unitarios de gamification_service
  ...
```

### C) Código
- Primero los archivos nuevos (servicios, repositorios, tests)
- Luego los refactorizados (handlers limpios)
- Siempre con comentarios que expliquen el *por qué* del cambio

---

## Referencias

- `references/architecture-patterns.md` — Implementaciones completas de Service Layer,
  Repository, Event Bus, para aiogram 3
- `references/testing-strategy.md` — Templates de tests async, mocks de aiogram,
  fixtures para DB en memoria, ejemplos por sistema
- `references/aiogram3-patterns.md` — Middlewares de error/rate-limit/idempotencia,
  FSM avanzado, patrones de router
