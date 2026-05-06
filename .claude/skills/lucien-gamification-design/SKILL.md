---
name: lucien-gamification-design
description: >
  Diseño de sistemas gamificados para el bot Lucien. Úsala cuando el usuario
  quiera diseñar nuevas mecánicas de engagement, entender motivación humana,
  diseñar sistemas de recompensas o analizar por qué usuarios regresan o no.
  Cubre Framework Octalysis, programas de reforzamiento y ética gamificada.
  Conoce los servicios existentes de Lucien y sabe qué se puede implementar
  técnicamente. Para implementación, consultar lucien-gamification-implementation.
---

# Gamification Design Skill

Esta skill ayuda a diseñar sistemas gamificados éticos y efectivos para LucienBot. El foco está en **por qué** usar ciertas mecánicas y **qué efecto** tienen en el comportamiento del usuario.

---

## Framework Octalysis: Los 8 Impulsos de Motivación

Los 8 impulsos de Yu-kai Chou divided en **White Hat** (generan lealtad sostenible) y **Black Hat** (generan engagement intenso pero pueden agotar):

| # | Impulso | Tipo | Qué es | Ejemplo en Lucien |
|---|--------|------|--------|-------------------|
| 1 | Significado Épico | White | "Soy parte de algo mayor" | Narrativa: "Eres pione@ de esta comunidad" |
| 2 | Desarrollo y Logro | White | Progresión visible | Niveles, barras de XP, insignias |
| 3 | Empoderamiento Creativo | White | Personalización + feedback inmediato | Perfil customizable, estrategias |
| 4 | Posesión y Propiedad | White | Acumular recursos | Besitos, coleccionables, avatar |
| 5 | Influencia Social | Black | Competencia, equipos, referidos | Leaderboards, referidos |
| 6 | Escasez e Impaciencia | Black | "Solo quedan 3 cupos" | Recompensas por tiempo limitado |
| 7 | Impredictibilidad | Black | Recompensas sorpresa | Loot boxes, drops aleatorios |
| 8 | Pérdida y Evitación | Black | Racha que se rompe | Racha diaria, penalizaciones |

### Principio Clave

**Priorizar White Hat.** Los impulsos White Hat (1-4) generan retención a largo plazo. Los Black Hat (5-8) son útiles para engagement intenso pero pueden agotar al usuario si se abusa.

**Regla práctica**: Si diseñas un sistema donde el usuario se siente manipulado o ansioso, es Black Hat demasiado agresivo.

---

## Programas de Reforzamiento (Skinner)

**Cuándo** entregas la recompensa importa más que **qué** recompensa entregas:

| Programa | Qué hace | Efecto | Cuándo usar |
|---------|----------|--------|-------------|
| **Reforzamiento Continuo** | Cada acción = recompensa | Aprendizaje rápido, extinción rápida | Onboarding: primer mensaje, primer logro |
| **Razón Fija (FR)** | Recompensa tras N acciones predecibles | Alta tasa con pausa post-recompensa | "Completa 5 misiones para subir nivel" |
| **Razón Variable (VR)** | Recompensa tras N aleatorio (5-20) | **Más potente**. Resistente a extinción | Loot boxes, recompensas sorpresa. Motor de slot machines |
| **Intervalo Fijo (FI)** | Recompensa tras tiempo predecible | Patrón escalonado: baja post-rec, pico antes | Daily rewards, paychecks virtuales |
| **Intervalo Variable (VI)** | Recompensa tras tiempo aleatorio | Baja pero sostenida | Eventos sorpresa impredecibles |

### VR (Razón Variable) en Lucien

El sistema VR es el más poderoso documentado en psicología conductual. Se implementa como:

```
Cada 5-20 interacciones (aleatorio) → recompensa sorpresa
```

Esto evita la "pausa post-recompensa" que ocurre con FR y FI, manteniendo engagement continuo.

**Aplicación en Lucien**: `GameService.play_trivia()` ya usa streaks — se puede añadir un bonus VR (besitos sorpresa cada N preguntas contestadas) para evitar extinción.

---

## Servicios Existentes y Qué Impulsos Cubren

Conocer estos servicios ayuda a diseñar mecánicas que se integren con lo existente:

| Servicio | Qué hace | Impulso Octalysis que cubre |
|----------|----------|----------------------------|
| **BesitoService** | Moneda virtual (besitos), balance, historial | #4 Posesión y Propiedad |
| **DailyGiftService** | Regalo diario (5 besitos/24h) | #8 Pérdida (por FOMO), #2 Logro |
| **GameService** | Dados, trivia con rachas | #2 Logro, #7 Impredictibilidad |
| **MissionService** | Misiones recurrentes/únicas | #1 Significado, #2 Logro, #8 Pérdida |
| **RewardService** | Deliver recompensas (besitos, paquetes, VIP) | #4 Posesión |
| **StoreService** | Tienda, paquetes de contenido | #4 Posesión, #6 Escasez |

### Qué FALT'A en Servicios

- **No hay leaderboard completo** — `BesitoService.get_top_users()` existe pero no hay UI de ranking
- **No hay sistema de referidos** — potapital para crecimiento orgánico
- **No hay VR surprises** — solo FI (daily gift) y FR (misiones)
- **No hay gacha/loot boxes**

---

## Diseño de una Nueva Mecánica: Preguntas Clave

Antes de diseñar, responder estas preguntas:

1. **¿Qué impulso Octalysis quieres activar?** (1-8)
2. **¿Qué programa de reforzamiento es mejor?**
   - Onboarding → Reforzamiento Continuo
   - Engagement sostenido → Razón Variable
   - Recompensa predecible → Intervalo Fijo
3. **¿Cómo mide el éxito?** (retention day 7, DAU, besitos ganados...)
4. **¿Es ético?** ¿El usuario se sentiramanipulado o ansioso?
5. **¿Existe ya algo similar?** Revisar servicios arriba

---

## Ética Gamificada: Anti-Patrones

Evitar estos patrones que pueden dañar al usuario:

| Anti-Patrón | Qué es | Por qué es problémico | Alternativa |
|------------|--------|----------------------|--------------|
| **FOMO agresivo** | "Perderás tu racha si no entras hoy" | Ansiedad, guilt-tripping | Racha con gracia period (48h en vez de 24h) |
| **VR sin límites** | Recompensas random cada interacción sin parar | Adición tipo slot machine | Límites diarios, pausa obligatoria |
| **Leaderboard global sin segmentación** | Top 10 global | 90% de usuarios nunca entran al top | Leaderboards de grupo o comunidad cercana |
| **Dark patterns en pagos** | Suscribir sin confirmar, UI confusing | Abuso de confianza | Checkout claro, confirmación explícita |
| **Extinción de recompensas** | Dejan de dar recompensas sin progresión | Frustración, abandonment | Transición gradual a recompensas más raras pero valiosas |

---

## Cross-Reference: Límites Técnicos

Para saber qué se puede implementar, conocer estos límites de Lucien:

- **Callbacks**: 64 bytes max en `callback_data`
- **FSM**: `StatesGroup` con `State()` para flujos multi-step
- **Storage**: RedisStorage en producción, MemoryStorage en dev
- **Servicios existentes**: Ver lista arriba — evitar duplicación
- **Handlers thin**: No lógica en handlers, solo llamar servicios

**Para implementación técnica, consultar `lucien-gamification-implementation`**.

---

## Recursos de Referencia

| Archivo | Contenido |
|---------|-----------|
| `REFERENCES/octalysis.md` | Detalle completo de los 8 impulsos con ejemplos |
| `REFERENCES/reinforcement.md` | Programas de reforzamiento con más ejemplos |
| `REFERENCES/ethics.md` | Dark patterns específicos y cómo evitarlos |
