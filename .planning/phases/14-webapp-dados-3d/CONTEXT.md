# Phase 14: WebApp Dados 3D

**Goal:** Reemplazar el minijuego de dados actual (texto Unicode) con una experiencia 3D interactiva usando Three.js integrada como Telegram WebApp

**Depends on:** Phase 13

---

## Requirements

### DICE-01: WebApp Frontend 3D
- Crear interfaz HTML/CSS/JS con Three.js
- Dos dados 3D realistas con física de lanzamiento
- Botón "Lanzar Dados" con animación
- Visualización del resultado (suma de ambos dados)
- Diseño elegante en tonos oscuros acorde a la estética de Lucien

### DICE-02: Integración Telegram WebApp
- Usar Telegram WebApp API para comunicación bot ↔ WebApp
- Pasar user_id desde el bot a la WebApp
- WebApp debe funcionar en móvil y desktop

### DICE-03: Lógica de Victoria
- Mantiene las reglas actuales:
  - Ambos pares (2,4,6) → Gana 1 besito
  - Dobles (mismo número) → Gana 1 besito
- Calcular resultado en frontend y enviar al backend para validación
- Prevenir manipulación (el backend debe validar el resultado)

### DICE-04: Manejo de Resultados
- WebApp envía resultado al bot via `web_app_data`
- Handler procesa resultado y otorga besitos si aplica
- Mensaje de confirmación en el chat

### DICE-05: Cooldown y Rate Limiting
- Mantener cooldown de 5 segundos entre lanzamientos
- Validación en backend (no confiar solo en frontend)

---

## Success Criteria

1. Usuario abre minijuego y ve dos dados 3D
2. Al tocar "Lanzar", los dados ruedan con animación física
3. El resultado se valida y los besitos se otorgan automáticamente si gana
4. Cooldown funciona correctamente (frontend + backend)
5. Diseño responsive y elegante

---

## Technical Notes

### WebApp URL
- Desarrollo local: `http://localhost:8080/dice.html`
- Producción: Servir desde el mismo dominio del bot o usar hosting estático

### Three.js Approach
- Usar CDN de Three.js para no agregar dependencias
- Geometría Box con texturas de puntos de dado
- Física simple con velocidad angular aleatoria
- Cámara orbital para mejor visualización

### Seguridad
- El backend SIEMPRE debe validar que el resultado sea posible (suma 2-12)
- Cooldown verificado en backend (no solo frontend)
- Rate limiting por user_id
