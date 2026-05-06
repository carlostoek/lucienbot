# Sistema de Loot Boxes en LucienBot: Ética, Reforzamiento e Implementación

---

## 1. ¿Es ético implementar loot boxes?

**Respuesta corta**: Sí, es ético *si* se implementa con límites estrictos y transparencia. El riesgo no está en la mecánica en sí, sino en cómo se diseña.

### Por qué las loot boxes generan controversy

Las loot boxes son éticamente problemáticas cuando emulan el comportamiento de **slot machines**:
- Probabilidades ocultas o manipuladas
- Sin límites de frecuencia
- Sin transparencia de probabilidades
- Combinadas con presión social ("tu amigo sacó un item raro")
- Orientadas a extraer dinero real sin valor tangible a cambio

### Dark patterns a evitar

| Anti-Patrón | Por qué es problémico | Alternativa ética |
|------------|--------|----------------------|
| Probabilidades ocultas | El usuario no sabe qué tan raro es realmente | Mostrar probabilidad exacta (ej: "1.2%") |
| Sin límite diario | Adicción tipo slot machine | Máximo 3 loot boxes por día |
| VR sin tope | Adicción porque no sabes cuándo viene la siguiente | Tope de probabilidad al 35% |
| Moneda real involved | Transforma en gambling | Solo besitos (moneda virtual del juego) |
| FOMO agresivo | "Última oportunidad" presiona decisiones | Loot boxes siempre disponibles, no countdowns |

### Cuándo es ético

- Usas **besitos** (moneda virtual), no dinero real
- Las probabilidades son **públicas y verificables**
- Hay **límites diarios** (máximo 3 por día)
- La probabilidad máxima es **35%** (nunca más)
- El usuario recibe **valor real** (besitos, badges, contenido)
- Puede **desconectarse** sin perder ventaja significativa

### En el contexto de Lucien

Lucien ya tiene mecánicas de VR funcionando (streak bonuses en trivia, daily gift con espera de 24h). Las loot boxes serían una extensión natural del **Impulso #7 (Impredictibilidad y Curiosidad)** del Framework Octalysis. La diferencia clave es que en Lucien la moneda es simbólico besitos, no dinero real, lo que reduce drásticamente el riesgo de gambling.

---

## 2. ¿Qué programa de reforzamiento es mejor?

**Respuesta corta**: **Razón Variable (VR)** es el más efectivo para loot boxes, pero requiere límites estrictos.

### Análisis de programas para loot boxes

| Programa | Efecto en loot boxes | Veredicto |
|----------|------|--------|
| **Reforzamiento Continuo (CR)** | Cada apertura da recompensa — extinción rápida, aburrido | No adecuado |
| **Razón Fija (FR)** | Tras N aperturas das recompensa — patrón predecible, pierde emoción | No adecuado |
| **Razón Variable (VR)** | Tras N aleatorio (5-20) das recompensa — el más potente, resistente a extinción, sin pausa post-rec | El mejor |
| **Intervalo Fijo (FI)** | Cada 24h puedes abrir — predecible, baja anticipación | No optimal |
| **Intervalo Variable (VI)** | Tiempo aleatorio hasta siguiente loot box — muy bajo engagement | No adecuado |

### Por qué VR es el programa correcto

El sistema VR (Razón Variable) es el más poderoso documentado en psicología conductual. Sus propiedades son:

1. **Tasa más alta de respuesta** — el usuario abre cajas frecuentemente
2. **Resistente a extinción** — aunque las recompensas se vuelven raras, el comportamiento persiste
3. **Sin pausa post-recompensa** — a diferencia de FR, no hay un "bajón" después de abrir una caja porque no puedes predecir cuándo viene la siguiente

Esto es precisamente lo que hace divertida una loot box: la incertidumbre de "cuándo será la próxima" mantiene el comportamiento.

### Implementación VR para loot boxes en Lucien

```python
# Cada N interacciones (aleatorio 5-20) = surprise loot box
import random

def should_spawn_loot_box(interactions_count: int) -> bool:
    base_chance = 0.05  # 5% base
    accumulated = min(base_chance + (interactions_count * 0.03), 0.35)
    return random.random() < accumulated
```

- Rango de interacciones: 5-20 (aleatorio)
- Probabilidad máxima: 35% (nunca más)
- Límite diario: 3 loot boxes máximo

---

## 3. ¿Cómo se implementa en LucienBot?

### Arquitectura recomendada

```
handlers/lootbox_handler.py → services/loot_box_service.py → models/loot_box.py
```

**Regla crítica**: handlers solo enrutan eventos, SIN lógica de negocio. Services hacen toda la lógica.

### Modelo de datos necesario

```python
# models/loot_box.py (nuevo)
class LootBox(Base):
    __tablename__ = "loot_boxes"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))  # "Caja de Diana"
    description = Column(String(255))
    cost_besitos = Column(Integer)  # 50 besitos para abrir
    is_active = Column(Boolean, default=True)
    daily_limit = Column(Integer, default=3)

class LootBoxItem(Base):
    __tablename__ = "loot_box_items"

    id = Column(Integer, primary_key=True)
    loot_box_id = Column(Integer, ForeignKey("loot_boxes.id"))
    name = Column(String(100))  # "Besitos raros", "Badge único"
    item_type = Column(String(20))  # BESITOS, BADGE, PACKAGE, VIP_DAYS
    weight = Column(Integer)  # Probabilidad relativa (mayor = más común)
    min_reward = Column(Integer)  # Rango min
    max_reward = Column(Integer)  # Rango max

class UserLootBoxClaim(Base):
    __tablename__ = "user_loot_box_claims"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    loot_box_id = Column(Integer, ForeignKey("loot_boxes.id"))
    item_id = Column(Integer, ForeignKey("loot_box_items.id"))
    claimed_at = Column(DateTime, default=datetime.utcnow)
```

### LootBoxService (service layer)

```python
# services/loot_box_service.py
class LootBoxService:
    def __init__(self, session: Session):
        self.session = session

    def get_loot_boxes(self) -> List[LootBox]:
        """Lista de cajas disponibles"""
        return self.session.query(LootBox).filter_by(is_active=True).all()

    def get_daily_claims(self, user_id: int, loot_box_id: int) -> int:
        """Cuántas veces abrió hoy"""
        today = date.today()
        return self.session.query(UserLootBoxClaim).filter(
            UserLootBoxClaim.user_id == user_id,
            UserLootBoxClaim.loot_box_id == loot_box_id,
            func.date(UserLootBoxClaim.claimed_at) == today
        ).count()

    def roll_loot_box(self, user_id: int, loot_box_id: int) -> dict:
        """Abre una loot box — retorna item y recompensa"""
        # 1. Verificar límite diario
        daily_claims = self.get_daily_claims(user_id, loot_box_id)
        loot_box = self.session.query(LootBox).get(loot_box_id)
        if daily_claims >= loot_box.daily_limit:
            return {"error": "Límite diario alcanzado", "reset_at": "00:00"}

        # 2. Verificar besitos suficientes
        with get_service(BesitoService) as besito_svc:
            if not besito_svc.has_sufficient_balance(user_id, loot_box.cost_besitos):
                return {"error": "Besitos insuficientes"}

        # 3. Débitar besitos
        with get_service(BesitoService) as besito_svc:
            besito_svc.debit_besitos(user_id, loot_box.cost_besitos, "loot_box", f"Abrir {loot_box.name}")

        # 4. Roll de probabilidad (Weighted random)
        items = self.session.query(LootBoxItem).filter_by(loot_box_id=loot_box_id).all()
        weights = [item.weight for item in items]
        chosen = random.choices(items, weights=weights, k=1)[0]

        # 5. Generar recompensa
        reward_amount = random.randint(chosen.min_reward, chosen.max_reward)

        # 6. Entregar recompensa
        with get_service(BesitoService) as besito_svc:
            if chosen.item_type == "BESITOS":
                besito_svc.credit_besitos(user_id, reward_amount, "loot_box", chosen.name)

        # 7. Registrar claim
        claim = UserLootBoxClaim(user_id=user_id, loot_box_id=loot_box_id, item_id=chosen.id)
        self.session.add(claim)
        self.session.commit()

        return {
            "success": True,
            "item_name": chosen.name,
            "reward_amount": reward_amount,
            "daily_remaining": loot_box.daily_limit - daily_claims - 1
        }
```

### Handler (thin, solo routing)

```python
# handlers/lootbox_handler.py
@router.callback_query(F.data.startswith("lootbox:open:"))
async def open_loot_box(callback: CallbackQuery, state: FSMContext):
    loot_box_id = int(callback.data.split(":")[2])

    with get_service(LootBoxService) as service:
        result = service.roll_loot_box(callback.from_user.id, loot_box_id)

    if "error" in result:
        await callback.answer(result["error"], show_alert=True)
    else:
        await callback.message.edit_text(
            f"¡Abriste la caja y encontraste {result['item_name']}! "
            f"+{result['reward_amount']} besitos. "
            f"Te quedan {result['daily_remaining']} aperturas hoy"
        )
    await callback.answer()

@router.callback_query(F.data == "lootbox:menu")
async def show_loot_boxes(callback: CallbackQuery):
    with get_service(LootBoxService) as service:
        boxes = service.get_loot_boxes()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{box.name} ({box.cost_besitos} besitos)", callback_data=f"lootbox:open:{box.id}")]
        for box in boxes
    ])
    await callback.message.edit_text("**Cajas de Diana**\n\nElige una caja para abrir:", reply_markup=kb)
    await callback.answer()
```

### Items sugeridos para las loot boxes

| Item | Tipo | Rango de reward | Probabilidad (weight) |
|------|------|---------|--------|
| Besitos comunes | BESITOS | 5-15 | 50 |
| Besitos raros | BESITOS | 20-50 | 30 |
| Besitos épicos | BESITOS | 100-200 | 10 |
| Badge "Coleccionista" | BADGE | 1 (único) | 5 |
| Acceso VIP 1 día | VIP_DAYS | 1 | 3 |
| Paquete de contenido | PACKAGE | 1 | 2 |

### Integración con impulsos Octalysis

| Qué implementas | Impulso Octalysis | Notas |
|----------------|--------------------|------|
| Loot box con items raros | #7 Impredictibilidad | VR, máximo 35% probabilidad |
| Badge de coleccionista | #4 Posesión y Propiedad | Coleccionable único |
| Besitos épicos | #2 Desarrollo y Logro | Progresión visible |
| Límite diario 3 | #7 con control | Evita adicción |
| Probabilidades públicas | Diseño ético | Transparencia |

---

## 4. Recomendaciones finales

### Para implementar de forma ética

1. **Máximo 3 loot boxes por día** por usuario — previene adicción
2. **Probabilidad máxima 35%** — no crear jackpot permanente
3. **Solo besitos (moneda virtual)** — no dinero real
4. **Probabilidades públicas** — mostrar odds en la UI
5. **Reset diario a las 00:00** — ventana predecible, no FOMO
6. **Nunca combinar con presión social** ("tu amigo sacó esto")
7. **Incluir items "garantizados"** — al menos un item fijo para que el usuario siempre gane algo

### Siguiente paso: lucien-gamification-implementation

Para la implementación técnica completa (FSM, migración Alembic, UI con inline keyboards), consultar `lucien-gamification-implementation`. La estructura de archivos sería:

```
services/loot_box_service.py      # Lógica de negocio
handlers/lootbox_handler.py        # Routing (thin)
models/loot_box.py                # Modelos SQLAlchemy
migrations/xxx_add_lootbox.py    # Migración Alembic
```

---

*Respuesta generada usando Framework Octalysis, programas de reforzamiento de Skinner, y ética gamificada. Compatible con la arquitectura existente de LucienBot (handlers → services → models).*
