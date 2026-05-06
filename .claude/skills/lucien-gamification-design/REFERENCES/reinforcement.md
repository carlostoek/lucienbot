# Programas de Reforzamiento de Skinner

## Contexto

B.F. Skinner demostró que **cuándo** entregas la recompensa importa más que **qué** recompensa. Esto se llama "programa de reforzamiento".

---

## Los 5 Programas

### 1. Reforzamiento Continuo (CR)

**Qué es**: Cada acción produce recompensa.

```
Acción → Recompensa → Acción → Recompensa → ...
```

**Efecto**: Aprendizaje muy rápido, pero extinción también rápida (cuando se deja de dar recompensa, el comportamiento se extingue rápido).

**En Lucien (onboarding)**:
- Primer mensaje de bienvenida con besitos bonus
- Primer logro unlocked
- Tutorial interactivo

**Cuándo usar**: Onboarding, aprender nuevas acciones.

---

### 2. Razón Fija (FR)

**Qué es**: Recompensa tras exactamente N acciones.

```
Acción → Acción → Acción → [Recompensa] → Acción → ...
        3 acciones          Vuelve a empezar
```

**Efecto**: Alta tasa de respuesta, pero pausa post-recompensa (después de recompensa, baja motivación momentáneamente).

**En Lucien**:
- "Completa 5 misiones para subir de nivel"
- "Responde 10 trivias para desbloquear VIP trivia"

**Cuándo usar**: Progresión predecible, punch cards.

---

### 3. Razón Variable (VR) — EL MÁS POTENTE

**Qué es**: Recompensa tras un número **aleatorio** de acciones (entre M y N).

```
Acción → Acción → [Recompensa] → Acción → Acción → Acción → Acción → [Recompensa] → ...
        2 acciones                              5 acciones
```

**Efecto**:
- La **tasa más alta** de todas
- **Resistente a extinción** — el comportamiento persiste aunque las recompensas se vuelven raras
- Sin pausa post-recompensa (porque no puedes predecir cuándo viene la siguiente)

**Por qué es peligroso**: Es el motor de las slot machines y gacha games. Sin límites, puede ser adictivo.

**En Lucien — aplicaciones sanas**:
```python
# Probabilidad acumulativa
interactions_since_reward = data.get("interactions_since_reward", 0)
base_chance = 0.05
accumulated_chance = min(base_chance + (interactions_since_reward * 0.03), 0.35)

if random.random() < accumulated_chance:
    reward = generate_random_reward(tier=user.level)
    # Otorgar sorpresa
    await state.update_data(interactions_since_reward=0)
```

- Cada 5-20 interacciones (aleatorio), besitos sorpresa
- Límite máximo de 35% de probabilidad
- Diario, no infinito

**Cuándo usar**: Recompensas sorpresa, evitar extinción, mantener engagement.

---

### 4. Intervalo Fijo (FI)

**Qué es**: Recompensa tras un tiempo **predecible** (ej: cada 24 horas).

```
[Recompensa] → esperar 24h → [Recompensa] → esperar 24h → ...
```

**Efecto**: Patrón escalonado:
- Baja actividad justo después de la recompensa
- Pico de actividad justo antes de que llegue la recompensa

**En Lucien**:
- Daily gift (24h cooldown)
- Missions semanales

**Cuándo usar**: Engagement recurrente, recompensas diarias.

---

### 5. Intervalo Variable (VI)

**Qué es**: Recompensa tras un tiempo **aleatorio**.

```
[Recompensa] → esperar 2h → [Recompensa] → esperar 6h → esperar 1h → [Recompensa] → ...
```

**Efecto**: Baja tasa de respuesta pero **sostenida** — no hay pico pre-recompensa porque no sabes cuándo viene.

**En Lucien**:
- Eventos sorpresa temporales impredecibles
- Drops aleatorios por festividades

**Cuándo usar**: Mantener presencia sin presión, notificaciones de eventos.

---

## Comparativa Rápida

| Programa | Tasa | Sostenibilidad | Riesgo |
|----------|------|-----------------|--------|
| CR | Alta (al inicio) | Baja | Extinción rápida |
| FR | Alta | Media | Pausa post-rec |
| **VR** | **La más alta** | **Muy alta** | **Adicción** |
| FI | Variable | Alta | Pico pre-rec |
| VI | Baja | Alta | Bajo engagement |

---

## Diseñando con Programas en Lucien

**Ejemplo: Sistema de besitos por reacciones**

1. **Onboarding** (CR): Primer reacción = +2 besitos inmediato
2. **Establecimiento** (FR): "Cada 10 reacciones = +5 besitos bonus"
3. **Mantenimiento** (VR): "Cada 5-20 reacciones (aleatorio) = sorpresa de +10 besitos"
4. **Recurrencia** (FI): "Daily reaction bonus: +20 besitos cada 24h"
5. **Sorpresa** (VI): "Drop aleatorio: hasta +50 besitos en evento especial"

**Clave**: Transicionar del CR/FR inicial al VR/FI sostenido.
