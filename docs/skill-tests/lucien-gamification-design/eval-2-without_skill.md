# Sistema de Loot Boxes para Lucien Bot: Ethics, Reforzamiento e Implementacion

## 1. Analisis Etico

### 1.1 Es etico implementar loot boxes?

**Respuesta corta:** Depende criticamente de como se disen e implementen.

**Analisis desde la perspectiva de Gamificacion Etica (Octalysis):**

El Framework Octalysis de Yu-Kai Chou identifica que los sistemas de recompensas aleatorias pueden ser:
- **Eticos** cuando: la curva de valor es justa, hay transparencia total, no hay perdida financiera real, y el usuario tiene agencia real
- **Manipulativos** cuando: explotan variabilidad emocional (variable ratio reinforcement), ocultan probabilidades reales, o usan deuda emocional para forzar repeticion

### 1.2 Criterios de Etica para Lucien Bot

Dado que es un bot de Telegram con moneda virtual (besitos):

**Principio 1: Moneda Virtual, No Real**
- Los besitos son moneda virtual gratuita/ganable, no tienen valor monetario real
- Esto mitiga concerns de gambling regulatorio significativamente
- Sin embargo, el hecho de que besitos pueden comprarse con dinero real (a traves de la tienda) introduce un gray area

**Principio 2: Transparencia Radical**
- Mostrar probabilidades exactas de cada item
- Permitir al usuario ver el historial de caja abierta
- Sin "fake" percentages o rareza inflada artificialmente

**Principio 3: Sin Presion Economica**
- Nunca bloquear contenido por no abrir cajas
- Ofrecer alternativas earn-free (grinding) para items
- Permitir guardado de besitos indefinidamente

**Principio 4: Valor Real del Item**
- Items utiles en el ecosystem (no solo cosmetics "brillantes")
- Items que mejoren la experiencia genuinamente
- Transferability para dar valor de reventa

### 1.3 Red Flags Eticos a Evitar

- **Dark patterns:** "Solo 3 cajas restantes hoy", cuentas regresivas falsas
- **Artificial scarcity:** Items que "nunca mas estaran disponibles"
- **Pity systems ocultos:** No revelar que despues de N intentos garantizas rareza
- **Priming emocional:** mensajes que manipulan emocion antes de abrir
- **Conflicto de interes:** El bot gana mas cuanto mas abras

### 1.4 Recomendacion Final de Etica

**Si se implementa, seguir el modelo "Honest Gacha":**
- Transparente con probabilidades
- Items con valor real transferible
- Siempre earnable por grinding (no solo comprable)
- Sin timers artificiales o FOMO

---

## 2. Programa de Reforzamiento Optimo

### 2.1 Comparacion de Programas de Reforzamiento

| Programa | Descripcion | Engagement | Ethicalidad | Adecuacion Lucien |
|----------|-------------|------------|-------------|-------------------|
| **Fixed Ratio (FR)** | Recompensa cada N acciones | Muy alto | Media | - Requiere muchas jugadas |
| **Variable Ratio (VR)** | Recompensa impredecible por accion | EXTREMO | Baja | - Modelo loot box estandar - peligroso |
| **Fixed Interval (FI)** | Recompensa cada X tiempo | Medio | Alta | - Modelo daily gift - ya existe |
| **Variable Interval (VI)** | Recompensa inesperada por tiempo | Alto | Alta | - Modelo mystery box - excelente |
| **Continuous** | Recompensa cada accion | Bajo | N/A | - Sin variedad |

### 2.2 Analisis Detallado

#### Variable Interval (VI) - El Mas Etico y Efectivo

**Por que es superior:**
- Emocion de lo inesperado sin manipulacion
- Produce engagement sostenido sin-addiction
- No explota dopamine loops intensos
- El usuario puede predecir "algo viene" pero no cuando

**Implementacion en Lucien:**
```
- Cada 4-8 horas de actividad, posibilidad de loot box gratis
- No强制性, solo cuando el usuario decide jugar
- Cooldown logico pero no timer agresivo
```

#### Variable Ratio (VR) - El Mas Adictivo (Usar con Precaucion)

**Por que es problematico:**
- El clasico slot machine pattern
- Famoso por crear behavior addiction
- Casinos y mobile games mas rentables
- Pero: regulado en multiples paises

**Si se usa, controles necesarios:**
- Limite de apertura diaria (5-8 max)
- Reset periodico de bad luck protection
- Transparency total de probabilidades
- Auto-exclusion para usuarios problemicos

### 2.3 Programa Recomendado: Tiered VI + VR Controlado

**Modelo hibrido para Lucien Bot:**

```
Nivel 1: VIP Diarios (VI suave)
- Cada 24 horas, VIP recibe una "Caja del Destino" gratuita
- Solo disponible para suscriptores activos
- Items: common/uncommon, 70%/30%

Nivel 2: Grinding VI (Contenido gratuito)
- Cada 50 besitos ganados en trivia/dados = 1 caja gratis
- Max 3 por semana para no VIP, ilimitadas para VIP
- Items: common/uncommon/rare, 60%/30%/10%

Nivel 3: Compras Opcionales (VR Controlado)
- Se puede comprar cajas con besitos
- Limite: max 5 compras directas por semana
- Probabilidades visibles
- Pity system transparente (garantiza rare al 50avo intento)
```

### 2.4 Framework Octalisis Aplicado

**Para engagement sostenible, implementar las 8 cores:**

1. **Epic Meaning & Calling** - "Las cajas contienen artifacts de la mitologia de Diana"
2. **Development & Accomplishment** - Progression visible de coleccion
3. **Empowerment of Creativity** - Items combinables para crear setups unicos
4. **Ownership & Possession** - Inventario personal transferable
5. **Social Influence & Relatedness** - Leaderboard de who opened what
6. **Scarcity & Impatience** - Ediciones limitadas reales (no fake)
7. **Unpredictability & Curiosity** - La emocion VI
8. **Loss & Avoidance** - "Tu caja del destino expira en 24h si no la abres"

---

## 3. Implementacion Tecnica en Lucien Bot

### 3.1 Arquitectura de Modelos

```python
# models/loot_box.py

class LootBoxType(enum.Enum):
    DESTINY_BOX = "destiny_box"        # VIP diario gratis
    GRINDING_BOX = "grinding_box"      # Earned through gameplay
    PREMIUM_BOX = "premium_box"        # Comprado con besitos

class LootRarity(enum.Enum):
    COMMON = "common"      # 60%
    UNCOMMON = "uncommon"  # 30%
    RARE = "rare"          # 8%
    LEGENDARY = "legendary" # 2%

class LootItemType(enum.Enum):
    BADGE = "badge"           # Cosmetico
    TITLE = "title"           # Titulo desbloqueable
    FRAME = "frame"           # Marco de perfil
    EFFECT = "effect"         # Efecto visual
    BESITOS = "besitos"       # Besitos directos
    PACKAGE_ACCESS = "package_access"  # Acceso anticipado
    VIP_DAYS = "vip_days"     # Dias VIP gratis

class LootBox(Base):
    __tablename__ = "loot_boxes"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    box_type = Column(LootBoxType, nullable=False)
    rarity_weights = Column(JSON)  # {"common": 60, "uncommon": 30, ...}
    price_besitos = Column(Integer, nullable=True)  # None = no se compra
    daily_limit = Column(Integer, default=1)
    cooldown_hours = Column(Integer, default=24)
    min_level_required = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class LootItem(Base):
    __tablename__ = "loot_items"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    rarity = Column(LootRarity, nullable=False)
    item_type = Column(LootItemType, nullable=False)
    
    # Para items con valor numerico
    value_besitos = Column(Integer, nullable=True)
    value_vip_days = Column(Integer, nullable=True)
    
    # Para items cosmicos
    badge_icon = Column(String, nullable=True)
    title_text = Column(String, nullable=True)
    frame_image = Column(String, nullable=True)
    effect_animation = Column(String, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserLootBoxOpen(Base):
    __tablename__ = "user_loot_box_opens"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    loot_box_id = Column(Integer, ForeignKey("loot_boxes.id"), nullable=False)
    
    item_id = Column(Integer, ForeignKey("loot_items.id"), nullable=False)
    rarity_obtained = Column(LootRarity, nullable=False)
    
    opened_at = Column(DateTime, default=datetime.utcnow)
    source = Column(String)  # "daily_vip", "grinding", "purchase"

class UserLootItem(Base):
    __tablename__ = "user_loot_items"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("loot_items.id"), nullable=False)
    
    acquired_at = Column(DateTime, default=datetime.utcnow)
    is_equipped = Column(Boolean, default=False)
    is_transferable = Column(Boolean, default=True)  # False para items unicos
```

### 3.2 Logica de Servicio

```python
# services/loot_box_service.py

class LootBoxService:
    """Servicio para sistema de loot boxes eticos"""
    
    # Probabilidades base (ajustables por config)
    BASE_RARITY_WEIGHTS = {
        'common': 60,
        'uncommon': 30,
        'rare': 8,
        'legendary': 2
    }
    
    # Cooldowns
    DESTINY_BOX_COOLDOWN_HOURS = 24
    GRINDING_BOX_TRIGGERS = 50  # Besitos ganados para 1 box
    PREMIUM_PITY_SYSTEM = 50    # Intentos para guarantee rare
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        self.besito_service = BesitoService(self.db)
        self._owns_session = db is None
    
    def _get_db(self) -> Session:
        if self._owns_session:
            return SessionLocal()
        return self.db
    
    def _roll_rarity(self, box_type: LootBoxType, 
                     bad_luck_protection: int = 0) -> LootRarity:
        """
        Selecciona rareza usando weighted random con pity system.
        
        Args:
            box_type: Tipo de caja (afecta probabilidades)
            bad_luck_protection: Contador de intentos sin rare/legendary
        
        Returns:
            LootRarity seleccionado
        """
        weights = self.BASE_RARITY_WEIGHTS.copy()
        
        # Pity system: incrementa rare/legendary odds despues de N intentos
        if bad_luck_protection >= 30:
            weights['rare'] += 10
            weights['legendary'] += 2
        
        if bad_luck_protection >= 50:
            weights['rare'] += 20
            weights['legendary'] += 5
        
        # Roll
        roll = random.randint(1, 100)
        cumulative = 0
        
        for rarity, weight in weights.items():
            cumulative += weight
            if roll <= cumulative:
                return LootRarity[rarity.upper()]
        
        return LootRarity.COMMON  # Fallback
    
    def _select_item_by_rarity(self, rarity: LootRarity) -> Optional[LootItem]:
        """Selecciona item aleatorio de la rareza especificada"""
        db = self._get_db()
        
        items = db.query(LootItem).filter(
            LootItem.rarity == rarity,
            LootItem.is_active == True
        ).all()
        
        if not items:
            logger.warning(f"No items found for rarity {rarity}")
            return None
        
        return random.choice(items)
    
    def get_user_boxes_available(self, user_id: int) -> dict:
        """
        Obtiene cajas disponibles para un usuario.
        
        Returns:
            {
                'destiny_box': {'available': True/False, 'cooldown_ends': datetime},
                'grinding_progress': {'current': 45, 'needed': 50, 'boxes_earned': 3},
                'premium_boxes': {'available': 5, 'price': 100}
            }
        """
        db = self._get_db()
        
        # Destiny Box status
        last_destiny = db.query(UserLootBoxOpen).filter(
            UserLootBoxOpen.user_id == user_id,
            UserLootBoxOpen.source == 'daily_vip'
        ).order_by(UserLootBoxOpen.opened_at.desc()).first()
        
        destiny_available = True
        cooldown_ends = None
        
        if last_destiny:
            elapsed = datetime.utcnow() - last_destiny.opened_at
            if elapsed < timedelta(hours=self.DESTINY_BOX_COOLDOWN_HOURS):
                destiny_available = False
                cooldown_ends = last_destiny.opened_at + \
                    timedelta(hours=self.DESTINY_BOX_COOLDOWN_HOURS)
        
        # Grinding progress (besitos ganados esta semana)
        week_start = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
        weekly_earned = self._get_weekly_besitos_earned(user_id, week_start)
        grinding_progress = {
            'current': weekly_earned % self.GRINDING_BOX_TRIGGERS,
            'needed': self.GRINDING_BOX_TRIGGERS,
            'boxes_earned': weekly_earned // self.GRINDING_BOX_TRIGGERS,
            'max_boxes': 3 if not self._is_user_vip(user_id) else float('inf')
        }
        
        # Premium boxes (besitos necesarios)
        premium_box = self._get_premium_box_config()
        
        return {
            'destiny_box': {
                'available': destiny_available,
                'cooldown_ends': cooldown_ends
            },
            'grinding_progress': grinding_progress,
            'premium_boxes': {
                'available': premium_box.daily_limit if premium_box else 0,
                'price': premium_box.price_besitos if premium_box else 0
            }
        }
    
    def _get_weekly_besitos_earned(self, user_id: int, since: datetime) -> int:
        """Obtiene besitos ganados por el usuario desde cierta fecha"""
        db = self._get_db()
        
        result = db.query(func.sum(BesitoTransaction.amount)).filter(
            BesitoTransaction.user_id == user_id,
            BesitoTransaction.type == TransactionType.CREDIT,
            BesitoTransaction.created_at >= since
        ).scalar()
        
        return result or 0
    
    def _is_user_vip(self, user_id: int) -> bool:
        """Verifica si usuario es VIP"""
        vip_service = VIPService(self.db)
        return vip_service.is_user_vip(user_id)
    
    def _get_premium_box_config(self) -> Optional[LootBox]:
        """Obtiene config de caja premium"""
        db = self._get_db()
        return db.query(LootBox).filter(
            LootBox.box_type == LootBoxType.PREMIUM_BOX,
            LootBox.is_active == True
        ).first()
    
    def _get_bad_luck_protection(self, user_id: int, box_type: LootBoxType) -> int:
        """
        Obtiene contador de pity system para el usuario y tipo de caja.
        Cuenta intentos sin obtener rare o legendary.
        """
        db = self._get_db()
        
        last_rare_or_legendary = db.query(UserLootBoxOpen).filter(
            UserLootBoxOpen.user_id == user_id,
            UserLootBoxOpen.loot_box_id == box_type.value,
            UserLootBoxOpen.rarity_obtained.in_([LootRarity.RARE, LootRarity.LEGENDARY])
        ).order_by(UserLootBoxOpen.opened_at.desc()).first()
        
        if not last_rare_or_legendary:
            return 50  # Max pity
        
        count = db.query(UserLootBoxOpen).filter(
            UserLootBoxOpen.user_id == user_id,
            UserLootBoxOpen.loot_box_id == box_type.value,
            UserLootBoxOpen.opened_at > last_rare_or_legendary.opened_at
        ).count()
        
        return min(count, 50)  # Cap en 50
    
    def open_box(self, user_id: int, box_type: LootBoxType) -> dict:
        """
        Abre una loot box para el usuario.
        
        Returns:
            {
                'success': True/False,
                'item': LootItem,
                'rarity': LootRarity,
                'is_new': True/False,
                'message': str
            }
        """
        validation = self._validate_box_opening(user_id, box_type)
        if not validation['valid']:
            return {
                'success': False,
                'error': validation['error'],
                'message': validation['message']
            }
        
        db = self._get_db()
        
        pity = self._get_bad_luck_protection(user_id, box_type)
        rarity = self._roll_rarity(box_type, bad_luck_protection=pity)
        item = self._select_item_by_rarity(rarity)
        
        if not item:
            return {
                'success': False,
                'error': 'no_items',
                'message': 'No hay items disponibles en este momento.'
            }
        
        open_record = UserLootBoxOpen(
            user_id=user_id,
            loot_box_id=box_type.value,
            item_id=item.id,
            rarity_obtained=rarity,
            source=self._get_source_string(box_type)
        )
        db.add(open_record)
        
        delivered = self._deliver_item_reward(user_id, item)
        
        db.commit()
        
        message = self._build_open_message(item, rarity, delivered)
        
        logger.info(
            f"loot_box_service - open_box - {user_id} - "
            f"box:{box_type.value}, item:{item.name}, rarity:{rarity.value}"
        )
        
        return {
            'success': True,
            'item': item,
            'rarity': rarity,
            'is_new': self._is_item_new_for_user(user_id, item.id),
            'delivered': delivered,
            'message': message
        }
    
    def _validate_box_opening(self, user_id: int, box_type: LootBoxType) -> dict:
        """Valida si el usuario puede abrir este tipo de caja"""
        
        if box_type == LootBoxType.DESTINY_BOX:
            if not self._is_user_vip(user_id):
                return {
                    'valid': False,
                    'error': 'not_vip',
                    'message': 'Solo miembros VIP pueden abrir la Caja del Destino.'
                }
            
            status = self.get_user_boxes_available(user_id)
            if not status['destiny_box']['available']:
                return {
                    'valid': False,
                    'error': 'cooldown',
                    'message': f"Tu caja estara disponible en {self._format_cooldown(status['destiny_box']['cooldown_ends'])}"
                }
        
        elif box_type == LootBoxType.GRINDING_BOX:
            status = self.get_user_boxes_available(user_id)
            grinding = status['grinding_progress']
            
            if grinding['boxes_earned'] >= grinding['max_boxes']:
                return {
                    'valid': False,
                    'error': 'weekly_limit',
                    'message': 'Has alcanzado tu limite semanal de cajas de grinding.'
                }
            
            if grinding['current'] < grinding['needed']:
                return {
                    'valid': False,
                    'error': 'not_enough_progress',
                    'message': f"Necesitas {grinding['needed'] - grinding['current']} besitos mas para abrir una caja."
                }
        
        elif box_type == LootBoxType.PREMIUM_BOX:
            premium = self._get_premium_box_config()
            if not premium:
                return {'valid': False, 'error': 'not_available', 'message': 'Caja premium no disponible.'}
            
            if not self.besito_service.has_sufficient_balance(user_id, premium.price_besitos):
                return {
                    'valid': False,
                    'error': 'insufficient_balance',
                    'message': f"Necesitas {premium.price_besitos} besitos para abrir esta caja."
                }
        
        return {'valid': True}
    
    def _deliver_item_reward(self, user_id: int, item: LootItem) -> dict:
        """Entrega la recompensa del item al usuario"""
        delivered = {'type': None, 'amount': 0}
        
        if item.item_type == LootItemType.BESITOS and item.value_besitos:
            self.besito_service.credit_besitos(
                user_id=user_id,
                amount=item.value_besitos,
                source=TransactionSource.LOOT_BOX,
                description=f"Loot box reward: {item.name}"
            )
            delivered = {'type': 'besitos', 'amount': item.value_besitos}
        
        elif item.item_type == LootItemType.VIP_DAYS and item.value_vip_days:
            vip_service = VIPService(self.db)
            vip_service.extend_vip(user_id, item.value_vip_days)
            delivered = {'type': 'vip_days', 'amount': item.value_vip_days}
        
        return delivered
    
    def _build_open_message(self, item: LootItem, rarity: LootRarity, 
                            delivered: dict) -> str:
        """Construye el mensaje de resultado al abrir caja"""
        
        rarity_colors = {
            'common': 'gris',
            'uncommon': 'verde',
            'rare': 'azul',
            'legendary': 'dorado'
        }
        
        rarity_icons = {
            'common': '',
            'uncommon': '',
            'rare': '',
            'legendary': ''
        }
        
        header = self._select_template([
            "La oscuridad de la caja se desvanece...",
            "Un destello de luz emerge desde el interior...",
            "El destino ha hablado..."
        ])
        
        item_reveal = f"{rarity_icons[rarity.value]} **{item.name}**"
        
        if delivered['type'] == 'besitos':
            reward_text = f"Has ganado {delivered['amount']} besitos!"
        elif delivered['type'] == 'vip_days':
            reward_text = f"Has ganado {delivered['amount']} dias VIP!"
        else:
            reward_text = f"'{item.description}'"
        
        footer = self._select_template([
            "El destino es caprichoso, pero nunca cruel.",
            "Diana observa con aprobacion.",
            "Lucien asiente en silencio."
        ])
        
        return f"{header}\n\n{item_reveal}\n\n{reward_text}\n\n_{footer}_"
    
    def _is_item_new_for_user(self, user_id: int, item_id: int) -> bool:
        """Verifica si el usuario ya poseia este item"""
        db = self._get_db()
        existing = db.query(UserLootItem).filter(
            UserLootItem.user_id == user_id,
            UserLootItem.item_id == item_id
        ).first()
        return existing is None
    
    def _format_cooldown(self, cooldown_end: datetime) -> str:
        """Formatea el tiempo restante de cooldown"""
        remaining = cooldown_end - datetime.utcnow()
        hours = remaining.total_seconds() / 3600
        if hours >= 1:
            return f"{int(hours)} horas"
        minutes = remaining.total_seconds() / 60
        return f"{int(minutes)} minutos"
    
    def _get_source_string(self, box_type: LootBoxType) -> str:
        """Obtiene string de source para logging"""
        mapping = {
            LootBoxType.DESTINY_BOX: 'daily_vip',
            LootBoxType.GRINDING_BOX: 'grinding',
            LootBoxType.PREMIUM_BOX: 'purchase'
        }
        return mapping.get(box_type, 'unknown')
```

### 3.3 Handler FSM (simplificado)

```python
# handlers/loot_box_handler.py

class LootBoxHandler:
    """Handler para flujo de loot boxes - solo routing, sin logica"""
    
    MAIN_MENU_KEYBOARD = InlineKeyboardMarkup([
        [InlineKeyboardButton("Destiny Box (VIP)", callback_data="lb_destiny")],
        [InlineKeyboardButton("Grinding Box", callback_data="lb_grinding")],
        [InlineKeyboardButton("Premium Box (100 besitos)", callback_data="lb_premium")],
        [InlineKeyboardButton("Inventario", callback_data="lb_inventory")],
        [InlineKeyboardButton("Volver al Menu", callback_data="games_menu")]
    ])
    
    OPEN_KEYBOARD = InlineKeyboardMarkup([
        [InlineKeyboardButton("Abrir Caja", callback_data="lb_open")],
        [InlineKeyboardButton("Volver", callback_data="lb_menu")]
    ])
    
    async def show_menu(self, update: Update, context: CallbackContext):
        """Muestra menu principal de loot boxes"""
        user_id = update.effective_user.id
        
        status = self.loot_box_service.get_user_boxes_available(user_id)
        
        destiny_status = "Disponible" if status['destiny_box']['available'] else f"Cooldown: {status['destiny_box']['cooldown_ends']}"
        
        text = (
            "Loot Boxes de Lucien\n\n"
            f"Destiny Box (VIP): {destiny_status}\n"
            f"Grinding Progress: {status['grinding_progress']['current']}/{status['grinding_progress']['needed']}\n"
            f"Premium Boxes: {status['premium_boxes']['available']} disponibles\n\n"
            "Selecciona una caja para abrir."
        )
        
        await update.message.reply_text(text, reply_markup=self.MAIN_MENU_KEYBOARD)
    
    async def handle_callback(self, update: Update, context: CallbackContext):
        """Maneja todos los callbacks de loot boxes"""
        query = update.callback_query
        data = query.data
        
        user_id = query.from_user.id
        
        if data == "lb_menu":
            await self.show_menu(update, context)
            
        elif data == "lb_destiny":
            await self._handle_destiny_box(query, user_id)
            
        elif data == "lb_grinding":
            await self._handle_grinding_box(query, user_id)
            
        elif data == "lb_premium":
            await self._handle_premium_box(query, user_id)
            
        elif data == "lb_open":
            await self._handle_open(query, user_id, context)
    
    async def _handle_destiny_box(self, query, user_id):
        """Muestra preview de caja destiny"""
        status = self.loot_box_service.get_user_boxes_available(user_id)
        
        if not status['destiny_box']['available']:
            await query.answer("Caja en cooldown", show_alert=True)
            return
        
        text = (
            "Caja del Destino\n\n"
            "Una caja especial reservada para los mas devotos de Diana.\n"
            "Contiene items de rareza Common a Legendary.\n\n"
            "Solo disponible para miembros VIP."
        )
        
        await query.message.edit_text(text, reply_markup=self.OPEN_KEYBOARD)
    
    async def _handle_grinding_box(self, query, user_id):
        """Muestra preview de caja grinding"""
        status = self.loot_box_service.get_user_boxes_available(user_id)
        progress = status['grinding_progress']
        
        text = (
            "Caja de Grinding\n\n"
            f"Progreso: {progress['current']}/{progress['needed']} besitos\n"
            f"Cajas ganadas esta semana: {progress['boxes_earned']}/{progress['max_boxes']}\n\n"
            "Cada 50 besitos ganados = 1 caja gratis.\n"
            "Los miembros VIP tienen cajas ilimitadas."
        )
        
        await query.message.edit_text(text, reply_markup=self.OPEN_KEYBOARD)
    
    async def _handle_premium_box(self, query, user_id):
        """Muestra preview de caja premium"""
        status = self.loot_box_service.get_user_boxes_available(user_id)
        
        text = (
            "Caja Premium\n\n"
            f"Precio: {status['premium_boxes']['price']} besitos\n"
            f"Disponibles: {status['premium_boxes']['available']}\n\n"
            "Mejores probabilidades que las cajas gratuitas.\n"
            "Garantia: Al abrir 50 cajas, al menos 1 sera Rare o Legendary."
        )
        
        await query.message.edit_text(text, reply_markup=self.OPEN_KEYBOARD)
    
    async def _handle_open(self, query, user_id, context):
        """Procesa la apertura de caja"""
        box_type = context.user_data.get('current_box_type', LootBoxType.PREMIUM_BOX)
        
        result = self.loot_box_service.open_box(user_id, box_type)
        
        if not result['success']:
            await query.answer(result['message'], show_alert=True)
            return
        
        await query.message.edit_text(
            result['message'],
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Volver al Menu", callback_data="lb_menu")]
            ])
        )
        
        if box_type == LootBoxType.PREMIUM_BOX:
            premium = self.loot_box_service._get_premium_box_config()
            self.loot_box_service.besito_service.debit_besitos(
                user_id=user_id,
                amount=premium.price_besitos,
                source=TransactionSource.LOOT_BOX,
                description="Apertura de caja premium"
            )
```

### 3.4 Items de Ejemplo

```python
# Data inicial para items de loot boxes

LOOT_ITEMS_INITIAL = [
    # COMMON (60%)
    {"name": "Sello de Visitante", "rarity": "common", "type": "badge", "description": "Un sello basico que indica tu presencia."},
    {"name": "Titulo: Novato", "rarity": "common", "type": "title", "description": "Un titulo modesto para principiantes."},
    {"name": "Marco Basico", "rarity": "common", "type": "frame", "description": "Un marco simple pero elegante."},
    {"name": "10 Besitos", "rarity": "common", "type": "besitos", "value": 10},
    
    # UNCOMMON (30%)
    {"name": "Sello de Constancia", "rarity": "uncommon", "type": "badge", "description": "Representa tu dedicacion al salon."},
    {"name": "Titulo: Devoto", "rarity": "uncommon", "type": "title", "description": "Un titulo que honra tu devocion."},
    {"name": "Marco plateado", "rarity": "uncommon", "type": "frame", "description": "Un brillo sutil pero distintivo."},
    {"name": "25 Besitos", "rarity": "uncommon", "type": "besitos", "value": 25},
    
    # RARE (8%)
    {"name": "Insignia de la Luna", "rarity": "rare", "type": "badge", "description": "Solo aquellos que buscan la luz la encuentran."},
    {"name": "Titulo: Discipulo", "rarity": "rare", "type": "title", "description": "Has demostrado tu compromiso."},
    {"name": "Marco dorado", "rarity": "rare", "type": "frame", "description": "El oro habla por si mismo."},
    {"name": "Efecto: Destello", "rarity": "rare", "type": "effect", "description": "Un destello magico en tus mensajes."},
    {"name": "100 Besitos", "rarity": "rare", "type": "besitos", "value": 100},
    
    # LEGENDARY (2%)
    {"name": "Corona de Lucien", "rarity": "legendary", "type": "badge", "description": "La corona del maestro de ceremonias."},
    {"name": "Titulo: El Elegido", "rarity": "legendary", "type": "title", "description": "Un titulo reservado para pocos."},
    {"name": "3 Dias VIP", "rarity": "legendary", "type": "vip_days", "value": 3},
    {"name": "Acceso Anticipado", "rarity": "legendary", "type": "package_access", "description": "Acceso a contenido antes que nadie."},
]
```

---

## 4. Resumen de Recomendaciones

### Etica
- Usar modelo "Honest Gacha" con probabilidades publicas
- Siempre earnable via grinding, no solo comprable
- Sin timers agresivos o FOMO artificial
- Items con valor real (transferibles cuando sea posible)

### Reforzamiento
- VI (Variable Interval) para cajas diarias gratuitas
- Grinding boxes basadas en besitos ganados
- VR controlado con pity system transparente para compras
- Hibrido: VI + VR limitado = engagement sostenible sin addiction

### Implementacion
- Nuevos modelos: LootBox, LootItem, UserLootBoxOpen, UserLootItem
- Servicio: LootBoxService con logica de weighted random y pity system
- Handler: LootBoxHandler que solo enruta eventos
- Sin logica de negocio en handlers
- Max 50 lineas por funcion
- Logging en cada accion importante
