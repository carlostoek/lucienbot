# Ética Gamificada: Dark Patterns y Alternativas

## Principio Fundamental

**El diseño debe buscar engagement sostenible, no adicción.** El usuario debe poder desconectarse sintiéndose bien con su tiempo invertido.

Investigaciones de ACM identifican patrones de adicción "oscuros" en interfaces de chatbot:
- Respuestas no deterministas (engagement impredecible)
- Presentación visual inmediata (no dar tiempo a reflexionar)
- Notificaciones excesivas
- Respuestas empáticas artificiales

---

## Dark Patterns Específicos

### 1. FOMO Agresivo (Fear of Missing Out)

**Qué es**: Mensajes como "Perderás tu racha de 15 días si no entras hoy".

**Problema**: Genera ansiedad, guilt-tripping. El usuario entra por miedo, no por diversión.

**Alternativas éticas**:
- Racha con ventana de gracia (48h en vez de 24h exactas)
- Recordatorios positivos ("Tu racha está activa,回来 cuando quieras")
- Recovery mechanic: streak roto = empezar de nuevo con +bonus
- Nunca amenazar con pérdida, solo informar

---

### 2. VR Sin Límites (Variable Ratio sin control)

**Qué es**: Recompensas aleatorias cada interacción sin límite, sin parar.

**Problema**: Motor de slot machines. El usuario presiona sin pausa porque no sabe cuándo viene la siguiente recompensa.

**Alternativas éticas**:
- Máximo 3 VR surprises por día
- Límite de probabilidad (35% max)
- Pausa obligatoria después de N recompensas seguidas
- Nunca usar VR para transacciones financieras

---

### 3. Leaderboards Globales sin Segmentación

**Qué es**: Ranking global donde solo top 10 recibe reconocimiento.

**Problema**: 90% de usuarios nunca estarán en el top. Desmotivación garantizada.

**Alternativas éticas**:
- Leaderboards de grupo/comunidad pequeña
- Rankings por antigüedad (nuevos vs nuevos)
- Múltiples categorías ("Top ganados", "Top activos esta semana", "Top referidos")
- Celebrar mejoras relatives, no solo absolutas

---

### 4. Dark Patterns en Pagos

**Qué es**: Suscribir sin confirmación clara, UI confusing, "dark patterns" en checkout.

**Problema**: Abuso de confianza. El usuario se suscribe sin querer.

**Alternativas éticas**:
- Checkout en 3 pasos mínimo (verificar → confirmar → procesar)
- Confirmación explícita con cantidad y concepto
- Cancelación fácil (un click)
- Nunca pre-seleccionar opciones caras

---

### 5. Escasez Artificial Infinita

**Qué es**: "Solo quedan 3 cupos" que nunca se acaban.

**Problema**: El usuario aprende que la escasez es fake, pierde confianza.

**Alternativas éticas**:
- Escasez real con stock limitado (-2 = no disponible)
- Countdown honesto con fecha de fin
- Si se agota, mostrarlo claro ("Agotado — únete a waitlist")
- Regeneración de stock con transparencia

---

### 6. Extinción de Recompensas Sin Transición

**Qué es**: Dejan de dar recompensas sin gradualmente cambiar hacia recompensas más valiosas.

**Problema**: El usuario siente que "ya no merece la pena" y abandona.

**Alternativas éticas**:
- Transición gradual: recompensas frecuentes pero pequeñas → recompensas raras pero grandes
- Mostrar "próxima recompensa" para mantener anticipation
- Variedad: no siempre besitos — a veces badges, acceso, contenido exclusivo

---

### 7. Notificaciones Intrusivas

**Qué es**: Push notifications constantes reminding al usuario de entrar.

**Problema**: Fatiga de notificaciones, el usuario silencia o abandona el bot.

**Alternativas éticas**:
- Silent push para recordatorios no urgentes (Telegram permite silent=True)
- Never spam — máximo 1 notificación por día
- User-controlled frequency preferences
- Opt-in/opt-out fácil

---

## Checklist de Ethical Gamification

Antes de implementar una mecánica, verificar:

- [ ] ¿El usuario puede desconectarse sintiéndose bien?
- [ ] ¿La escasez es real o artificial?
- [ ] ¿Hay límites en VR para evitar adicción?
- [ ] ¿El leaderboard tiene segmentación para no desmotivar?
- [ ] ¿Las notificaciones son consentidas y controladas por el usuario?
- [ ] ¿El usuario entiende qué obtendrá y a qué precio?
- [ ] ¿La mecánica genera valor real o solo manipulación?

**Si la respuesta a cualquiera es "no", reconsiderar el diseño.**
