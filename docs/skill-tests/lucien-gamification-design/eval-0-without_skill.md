# Sistema de Referidos para Lucien Bot: Recomendaciones de Gamificacion

## 1. Impulso Octalysis Recomendado: Core Drive 3 y 7 en Combinacion

### Impulso primario: Core Drive 5 - Influencia Social

El referral es inherentemente un acto social. El usuario no solo gana para si, sino que conecta a alguien mas con algo valioso. Esto activa:

- **Filial Social**: "Le estoy dando algo bueno a un amigo"
- **Imitacion Social**: "Mi amigo vio lo que yo hago y quiso estar aqui"
- **Envidia/Pertenencia**: "Yo traje a alguien, mi amigo esta en el circulo de Diana"

**Activacion en Lucien**: Cada visitado ve un contador personal "Visitantes traidos al circulo de Diana" con su nombre. El referidor recibe notificacion cuando alguien acepta la invitacion.

### Impulso secundario: Core Drive 7 - Impredictibilidad

Para evitar la extincion del comportamiento (el usuario deja de invitar despues de las primeras recompensas), se anaden **sorpresas** cada N invitados:

- Cada 5-20 invitados (aleatorio): sorpresa de +X besitos adicionales
- Limite maximo: 3 sorpresas por dia para evitar adiccion tipo slot machine
- Probabilidad maxima: 35% acumulado

### Impulso terciario: Core Drive 2 - Desarrollo y Logro

Cada umbral de referido alcanzado es un logro concreto:

```
1 referido     -> 50 besitos + insignia "Embajador"
3 referidos    -> 100 besitos + acceso a mision exclusiva
5 referidos    -> 200 besitos + 1 dia VIP gratis
10 referidos   -> 500 besitos + rol "Embajador Dorado" en perfil
20 referidos   -> Paquete especial "Circulo Interior" (contenido unico)
```

### Impulso terciario: Core Drive 4 - Posesion y Propiedad

El referidor acumula un historial de quienes trajo. "Has introducido a 12 personas al circulo de Diana." Eso se convierte en badge permanente y fuente de orgullo.

---

## 2. Programa de Reforzamiento Recomendado: Hibrido FR + VR con Techo

### Por que no un programa simple de "1 referido = X besitos"

Los programas de reforzamiento **fijos** (Fixed Ratio) crean meseta de motivacion: una vez que el usuario comprende el patron, la anticipacion desaparece. Para mantener engagement sostenido en referral, se necesita **variabilidad**.

### Programa recomendado: **FR escalonado con splash de VR**

```
Estructura de recompensas escalonadas:

Referidos completados     Recompensa
1                          50 besitos + badge "Embajador"
3                          100 besitos + acceso a mision exclusiva
5                          200 besitos + 1 dia VIP gratis
10                         500 besitos + rol "Embajador Dorado"
20                         Paquete especial "Circulo Interior"
```

**Como funciona (basado en teoria de Skinner)**

1. **FR dentro de cada umbral**: El usuario sabe exactamenteantos referidos necesita para el siguiente nivel. Esto genera alta tasa de respuesta.

2. **VR splash**: En lugar de 10 besitos por referido, el sistema hace que cada 3 referidos de un "splash" de 100 besitos. El cerebro percibe que hay mas valor en esperar al umbral que en referido inmediato.

3. **Escalamiento no lineal**: Los primeros referidos son faciles (baja friccion). Del 5 al 10 es mas dificil, por eso la recompensa salta mas. La curva refleja esfuerzo real.

4. **VR sorpresa adicional**: Cada 5-20 invitados (aleatorio) + sorpresa de +X besitos. Limite de 3 por dia. Probabilidad maxima 35%.

### Evitar: Reforzamiento continuo (CRF)

Dar besitos por cada accion individual (envio link, abrio link, se registro) genera **saciedad prematura**. El usuario pierde el sentido de evento especial. El referral debe sentirse como un **evento**, no como una transaccion.

---

## 3. Dark Patterns a Evitar y Alternativas Eticas

### Dark Pattern 1: Fake social proof ("Tu amigo ya se unio... casi")

- **Que NO hacer**: Mostrar notificaciones falsas de que alguien se unio para presionar accion.
- **Por que es danino**: Rompe confianza con el usuario y con el invitado.
- **Alternativa etica**: Solo mostrar referidos reales verificados. Si hay estado pendiente (invitado creo cuenta pero no verifico), mostrar "invitacion enviada, pendiente de confirmacion" — con transparencia.

### Dark Pattern 2: Ambiguedad predatory ("Invita y... quien sabe que pasa?")

- **Que NO hacer**: Ocultar que recibe el invitado o el referidor hasta despues de que el invitado se une.
- **Alternativa etica**: Diseno de doble ventana:
  - **Para el referidor**: "Tu amigo recibe 20 besitos al unirse; tu recibes 50 besitos cuando el complete su primer besito"
  - **Para el invitado**: "Te envia 20 besitos de bienvenida. Sin compromiso."

### Dark Pattern 3: Coercion disfrazada ("Invita o pierdes tu racha")

- **Que NO hacer**: Amenazar con reset de racha o quitar beneficios si no se invita.
- **Por que es manipulador**: Convierte el referral en obligacion, no en acto voluntario.
- **Alternativa etica**: Ofrecer el referral como **oportunidad adicional**, no como requisito. "Tu racha esta a salvo. Pero si quieres multiplicarla..."

### Dark Pattern 4: Urgencia falsa ("Solo hoy: doble recompensa")

- **Que NO hacer**: Temporizadores artificiales que resetean.
- **Alternativa etica**: Eventos reales con fechas limite honestas, comunicadas con anticipacion. Si no hay fecha limite real, no fingir una.

### Dark Pattern 5: Countdown enganoso

- **Que NO hacer**: "3 personas viendo este link ahora mismo" — datos ficticios.
- **Alternativa etica**: Solo metricas reales. Si no hay datos, simplemente no mostrar ese dato.

### Dark Pattern 6: VR sin limites

- **Que NO hacer**: Recompensas aleatorias cada interaccion sin limite, sin parar.
- **Por que es danino**: Motor de slot machines. El usuario presiona sin pausa.
- **Alternativa etica**:
  - Maximo 3 VR surprises por dia
  - Limite de probabilidad (35% max)
  - Pausa obligatoria despues de N recompensas seguidas
  - Nunca usar VR para transacciones financieras

### Dark Pattern 7: Escalera que desaparece

- **Que NO hacer**: Cuando el usuario alcanza un nivel, el siguiente nivel cambia.
- **Alternativa etica**: Las metas son fijas y publicas. "5 referidos = VIP dia gratis" no cambia una vez comunicado.

---

## 4. Diseno Recomendado para Lucien Bot

### Mecanica Central: "Embajadores de Diana"

```
1. El Visitante genera un link unico: t.me/LucienBot?ref=USERNAME123
2. Cada vez que alguien se une via ese link y completa una accion minima
   (ej: enviar primer besito), el referidor gana.
3. El sistema muestra: progreso + recompensa pendiente + proximo umbral.
4. En cada umbral alcanzado, notificacion discreta tipo:
   "Lucien reconoce tu lealtad: has traido a 3 visitantes al circulo de Diana."
```

### Resumen de Core Drives activados

| Core Drive | Como se activa |
|---|---|---|
| CD5 Impacto Social | Ver a amigos unirse, compartir link |
| CD7 Impredictibilidad | Sorpresa cada 5-20 invitados (con limite) |
| CD2 Logro | Umbrales de referido, insignias |
| CD4 Posesion | Contador personalizado, perfil con badge |
| CD1 Significado Epico | Meta de 20 referidos (logro epico "Circulo Interior") |

### Recompensa etica escalonada

- **50 besitos** por primer referido (baja friccion, onboarding)
- **+20 besitos** al invitado para que sienta valor inmediatamente
- **Recompensa splash** cada 3 referidos (evita saciedad)
- **Badge visible** en perfil (reconocimiento social intrinseco)
- **Premio especial** para 20 referidos: paquete "Circulo Interior" (contenido unico no disponible en tienda)

### Voz de Lucien en las notificaciones

```
"Lucien reconoce tu lealtad: has traido a 3 visitantes al circulo de Diana.
 Tu recompensa de 100 besitos esta lista. Colocale un moño con el brillo
 de quien construye comunidad."
```

---

## 5. Metricas para Medir Salud del Sistema

- **Tasa de conversion**: De clicks en link a registros completados. Objetivo: > 15 por ciento
- **Tasa de activacion**: De registros a primer besito del invitado. Objetivo: > 60 por ciento
- **Viralidad**: R0 efectivo (cada referido cantos trae). Objetivo: > 0.8
- **Churn de referidor**: Vuelven a invitar despues de 30 dias? Esto revela si el programa tiene fatiga o engagement real.
- **Ratio de recompensa**: Besitos entregados vs besitos generados por referido. Debe ser > 1 para ser sostenible.

---

## 6. Checklist de Ethical Gamification (aplicado a referidos)

Antes de implementar, verificar:

- [ ] El usuario puede desconectarse sintiendose bien
- [ ] La escasez es real o artificial
- [ ] Hay limites en VR para evitar adiccion
- [ ] El sistema no fuerza ni presiona a invitar
- [ ] Las notificaciones son consentidas y controladas por el usuario
- [ ] El usuario entiende que obtendra y a que precio
- [ ] La mecanica genera valor real o solo manipulacion
- [ ] No hay fake social proof
- [ ] Las metas son fijas y publicas
- [ ] El invitado tambien recibe valor (no solo el referidor)

**Si la respuesta a cualquiera es "no", reconsiderar el diseno.**