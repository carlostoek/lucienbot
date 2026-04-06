# Phase 14: WebApp Dados 3D — Execution Plan

**Goal:** Reemplazar el minijuego de dados actual con experiencia 3D interactiva usando Three.js como Telegram WebApp

**Phase:** 14
**Status:** Ready for Execution

---

## Overview

Esta fase implementa una WebApp con Three.js que reemplaza el minijuego de dados basado en texto Unicode por una experiencia 3D interactiva. Los usuarios lanzarán dos dados animados que ruedan físicamente, y el resultado se comunica al bot para validación y entrega de recompensas.

---

## Plan 14-01: WebApp Frontend 3D con Three.js

**Goal:** Crear la interfaz HTML/CSS/JS con Three.js para visualizar y lanzar dos dados 3D

**Requirements:** DICE-01, DICE-02

**Affected Components:**
- `webapp/dice.html` — Página principal de la WebApp
- `webapp/css/dice.css` — Estilos elegantes en tonos oscuros
- `webapp/js/dice.js` — Lógica Three.js y física de dados

**Implementation Details:**

### Estructura HTML
- Contenedor para el canvas de Three.js
- Botón "Lanzar Dados" estilizado
- Indicador de resultado
- Integración con Telegram WebApp SDK

### Three.js Implementation
- Dos cubos con geometría Box (geometría de dado)
- Texturas con puntos de dado (1-6) usando canvas dinámico o imágenes
- Cámara orbital para mejor ángulo de vista
- Iluminación ambiental + direccional para realismo
- Física simple: velocidad angular aleatoria + gravedad
- Floor/plano para que los dados rueden y caigan

### Diseño Visual
- Fondo oscuro (#1a1a1a o similar)
- Acabados dorados/bronce para los dados (acorde a estética Lucien)
- Tipografía elegante
- Responsive para móviles

**Success Criteria:**
1. WebApp carga correctamente en navegador
2. Dos dados 3D visibles con texturas de puntos
3. Botón "Lanzar" inicia animación de rodadura
4. Dados se detienen mostrando valores aleatorios 1-6
5. Diseño responsive y elegante

---

## Plan 14-02: Integración Telegram WebApp API

**Goal:** Integrar la WebApp con Telegram para recibir user_id y enviar resultados

**Requirements:** DICE-02, DICE-04

**Affected Components:**
- `webapp/js/dice.js` — Integración WebApp SDK
- `handlers/gamification_user_handlers.py` — Modificar para lanzar WebApp
- `routers/webapp_router.py` — Nuevo router para recibir datos de WebApp

**Implementation Details:**

### Frontend (dice.js)
```javascript
// Inicializar WebApp
declare const Telegram: any;
const tg = window.Telegram.WebApp;
tg.ready();

// Obtener initDataUnsafe para user_id
const user = tg.initDataUnsafe.user;
const userId = user?.id;

// Enviar resultado al bot
tg.sendData(JSON.stringify({
    dice1: value1,
    dice2: value2,
    sum: value1 + value2,
    win: isWin
}));
```

### Backend (gamification_user_handlers.py)
Modificar `show_minigames_menu` y `dice_game`:
- `show_minigames_menu`: Botón "Lanzar dados" usa `web_app` en lugar de callback
- `dice_game`: Handler para recibir `web_app_data`

```python
from aiogram.types import WebAppInfo

keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(
        text="🎲 Lanzar dados",
        web_app=WebAppInfo(url=WEBAPP_URL)
    )],
    [InlineKeyboardButton(text="🔙 Volver", callback_data="back_to_main")]
])
```

### Nuevo Handler WebApp
```python
@router.message(F.web_app_data)
async def handle_dice_webapp(message: Message):
    data = json.loads(message.web_app_data.data)
    # Validar resultado y otorgar besitos
```

**Success Criteria:**
1. WebApp recibe correctamente user_id desde Telegram
2. Botón en Telegram abre la WebApp en pantalla completa
3. WebApp puede enviar datos de vuelta al bot
4. Handler recibe y parsea los datos correctamente

---

## Plan 14-03: Validación y Sistema de Recompensas

**Goal:** Validar resultados en backend, aplicar cooldown y otorgar besitos

**Requirements:** DICE-03, DICE-05

**Affected Components:**
- `handlers/gamification_user_handlers.py` — Handler web_app_data
- `services/besito_service.py` — Verificar y otorgar besitos (ya existe)

**Implementation Details:**

### Validación de Resultado
El backend DEBE validar que:
- Ambos valores están entre 1-6
- La suma está entre 2-12
- El resultado es consistente (no manipulado)

### Reglas de Victoria (mismas que ahora)
```python
def check_win(dice1: int, dice2: int) -> bool:
    # Ambos pares (2, 4, 6)
    both_even = dice1 % 2 == 0 and dice2 % 2 == 0
    # Dobles (mismo número)
    is_double = dice1 == dice2
    return both_even or is_double
```

### Cooldown (mantener existente)
- Reutilizar `_dice_game_cooldown` dict
- Verificar antes de procesar recompensa
- Respaldar con cooldown en base de datos si es necesario

### Flujo Completo
1. WebApp envía resultado → Bot
2. Bot valida que resultado es posible
3. Bot verifica cooldown
4. Si gana: otorga 1 besito via BesitoService
5. Envía mensaje de confirmación al usuario

**Success Criteria:**
1. Resultados inválidos son rechazados
2. Cooldown de 5 segundos funciona correctamente
3. Besitos se otorgan solo cuando aplica (pares o dobles)
4. Mensaje de confirmación muestra resultado y recompensa

---

## Plan 14-04: Deployment y Configuración

**Goal:** Configurar URLs de WebApp para desarrollo y producción

**Requirements:** DICE-02

**Affected Components:**
- `config/settings.py` — Agregar WEBAPP_URL
- `railway.toml` / `Dockerfile` — Servir archivos estáticos
- `bot.py` — Configurar modo WebApp si es necesario

**Implementation Details:**

### Estructura de Archivos
```
webapp/
├── dice.html
├── css/
│   └── dice.css
└── js/
    └── dice.js
```

### Configuración
- `WEBAPP_URL` en variables de entorno
- Desarrollo local: `http://localhost:8080/webapp/dice.html`
- Producción: `https://tudominio.com/webapp/dice.html`

### Servir Estáticos
- Flask/FastAPI para servir archivos estáticos en desarrollo
- Railway/Nginx para servir en producción

**Success Criteria:**
1. WebApp accesible desde URL configurada
2. Variables de entorno correctamente seteadas
3. Funciona tanto en desarrollo como en producción

---

## Execution Order

1. **Plan 14-01:** Crear WebApp frontend 3D
2. **Plan 14-02:** Integrar WebApp con Telegram
3. **Plan 14-03:** Validación y recompensas
4. **Plan 14-04:** Deployment y configuración

---

## Verification Checklist

- [ ] Dados 3D se visualizan correctamente
- [ ] Animación de lanzamiento funciona
- [ ] WebApp se abre desde botón de Telegram
- [ ] Resultados se envían al bot correctamente
- [ ] Validación rechaza resultados inválidos
- [ ] Cooldown funciona (no puede lanzar inmediatamente de nuevo)
- [ ] Besitos se otorgan correctamente al ganar
- [ ] Diseño es responsive en móviles
- [ ] Funciona en producción (Railway)
