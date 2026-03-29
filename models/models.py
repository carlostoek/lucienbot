"""
Modelos de datos - Lucien Bot
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, BigInteger, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from models.database import Base
import enum
import secrets
import string


class ChannelType(str, enum.Enum):
    """Tipos de canal"""
    FREE = "free"
    VIP = "vip"


class TokenStatus(str, enum.Enum):
    """Estados de un token"""
    ACTIVE = "active"
    USED = "used"
    EXPIRED = "expired"


class UserRole(str, enum.Enum):
    """Roles de usuario"""
    ADMIN = "admin"
    USER = "user"


class User(Base):
    """Modelo de usuario"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    tokens_redeemed = relationship("Token", back_populates="redeemed_by")


class Channel(Base):
    """Modelo de canal"""
    __tablename__ = "channels"
    
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(BigInteger, unique=True, index=True, nullable=False)
    channel_name = Column(String(200), nullable=True)
    channel_type = Column(Enum(ChannelType), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Configuración específica para canal Free
    wait_time_minutes = Column(Integer, default=3)  # Tiempo de espera en minutos
    welcome_message = Column(Text, nullable=True)
    approval_message = Column(Text, nullable=True)
    
    # Relaciones
    subscriptions = relationship("Subscription", back_populates="channel")
    pending_requests = relationship("PendingRequest", back_populates="channel", cascade="all, delete-orphan")


class Tariff(Base):
    """Modelo de tarifa VIP"""
    __tablename__ = "tariffs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    duration_days = Column(Integer, nullable=False)
    price = Column(String(50), nullable=False)
    currency = Column(String(10), default="USD")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    tokens = relationship("Token", back_populates="tariff", cascade="all, delete-orphan")


class Token(Base):
    """Modelo de token de acceso VIP"""
    __tablename__ = "tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token_code = Column(String(64), unique=True, index=True, nullable=False)
    tariff_id = Column(Integer, ForeignKey("tariffs.id"), nullable=False)
    status = Column(Enum(TokenStatus), default=TokenStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    redeemed_at = Column(DateTime(timezone=True), nullable=True)
    redeemed_by_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=True)
    
    # Relaciones
    tariff = relationship("Tariff", back_populates="tokens")
    redeemed_by = relationship("User", back_populates="tokens_redeemed")
    subscriptions = relationship("Subscription", back_populates="token")
    
    @staticmethod
    def generate_token():
        """Genera un token único de 32 caracteres"""
        return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))


class Subscription(Base):
    """Modelo de suscripción VIP"""
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)
    token_id = Column(Integer, ForeignKey("tokens.id"), nullable=False)
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    end_date = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)
    reminder_sent = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    user = relationship("User", back_populates="subscriptions")
    channel = relationship("Channel", back_populates="subscriptions")
    token = relationship("Token", back_populates="subscriptions")


class PendingRequest(Base):
    """Modelo de solicitud pendiente de acceso al canal Free"""
    __tablename__ = "pending_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    status = Column(String(20), default="pending")  # pending, approved, cancelled
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    scheduled_approval_at = Column(DateTime(timezone=True), nullable=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relaciones
    channel = relationship("Channel", back_populates="pending_requests")


# ============================================================
# FASE 1: GAMIFICACIÓN - BESITOS, BROADCASTING, REGALO DIARIO
# ============================================================

class TransactionType(str, enum.Enum):
    """Tipos de transacción de besitos"""
    CREDIT = "credit"      # Entrada de besitos
    DEBIT = "debit"        # Salida de besitos


class TransactionSource(str, enum.Enum):
    """Fuentes de transacción de besitos"""
    REACTION = "reaction"          # Reacción a mensaje
    DAILY_GIFT = "daily_gift"      # Regalo diario
    MISSION = "mission"            # Recompensa por misión
    PURCHASE = "purchase"          # Compra en tienda
    ADMIN = "admin"                # Ajuste manual por admin


class BesitoBalance(Base):
    """Saldo de besitos por usuario"""
    __tablename__ = "besito_balances"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, unique=True, index=True, nullable=False)
    balance = Column(Integer, default=0, nullable=False)
    total_earned = Column(Integer, default=0, nullable=False)  # Total acumulado histórico
    total_spent = Column(Integer, default=0, nullable=False)   # Total gastado histórico
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    transactions = relationship("BesitoTransaction", back_populates="balance", cascade="all, delete-orphan")


class BesitoTransaction(Base):
    """Historial de transacciones de besitos"""
    __tablename__ = "besito_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("besito_balances.user_id"), nullable=False, index=True)
    amount = Column(Integer, nullable=False)  # Positivo para crédito, negativo para débito
    type = Column(Enum(TransactionType), nullable=False)
    source = Column(Enum(TransactionSource), nullable=False)
    description = Column(String(255), nullable=True)  # Descripción del movimiento
    reference_id = Column(Integer, nullable=True)  # ID de referencia (misión, compra, etc.)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    balance = relationship("BesitoBalance", back_populates="transactions")


class ReactionEmoji(Base):
    """Configuración de emojis de reacción y sus valores"""
    __tablename__ = "reaction_emojis"
    
    id = Column(Integer, primary_key=True, index=True)
    emoji = Column(String(10), unique=True, nullable=False)  # El emoji mismo (💋, ❤️, etc.)
    name = Column(String(50), nullable=True)  # Nombre descriptivo
    besito_value = Column(Integer, default=1, nullable=False)  # Cuántos besitos otorga
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    broadcast_reactions = relationship("BroadcastReaction", back_populates="reaction_emoji")


class BroadcastMessage(Base):
    """Mensajes de broadcasting con reacciones"""
    __tablename__ = "broadcast_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(BigInteger, nullable=False, index=True)  # ID del mensaje en Telegram
    channel_id = Column(BigInteger, ForeignKey("channels.channel_id"), nullable=False)
    admin_id = Column(BigInteger, nullable=False)  # Quién envió el mensaje
    text = Column(Text, nullable=True)  # Texto del mensaje
    has_attachment = Column(Boolean, default=False)  # Si tiene foto/archivo adjunto
    attachment_type = Column(String(50), nullable=True)  # photo, video, document, etc.
    attachment_file_id = Column(String(500), nullable=True)  # ID del archivo en Telegram
    has_reactions = Column(Boolean, default=False)  # Si tiene botones de reacción
    is_protected = Column(Boolean, default=False)  # Protección contra copia/reenvío
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    reactions = relationship("BroadcastReaction", back_populates="broadcast", cascade="all, delete-orphan")


class BroadcastReaction(Base):
    """Reacciones de usuarios a mensajes de broadcast"""
    __tablename__ = "broadcast_reactions"
    
    id = Column(Integer, primary_key=True, index=True)
    broadcast_id = Column(Integer, ForeignKey("broadcast_messages.id"), nullable=False, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    reaction_emoji_id = Column(Integer, ForeignKey("reaction_emojis.id"), nullable=False)
    besitos_awarded = Column(Integer, nullable=False)  # Cuántos besitos se otorgaron
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    broadcast = relationship("BroadcastMessage", back_populates="reactions")
    reaction_emoji = relationship("ReactionEmoji", back_populates="broadcast_reactions")
    
    # Constraint único: un usuario solo puede reaccionar una vez por mensaje
    __table_args__ = (
        # No se puede usar UniqueConstraint directamente con SQLAlchemy 1.4/2.0 de esta forma
        # Se manejará a nivel de aplicación
    )


class DailyGiftConfig(Base):
    """Configuración del regalo diario"""
    __tablename__ = "daily_gift_config"
    
    id = Column(Integer, primary_key=True, index=True)
    besito_amount = Column(Integer, default=10, nullable=False)  # Cantidad de besitos
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(BigInteger, nullable=True)  # Admin que actualizó


class DailyGiftClaim(Base):
    """Registros de reclamos de regalo diario"""
    __tablename__ = "daily_gift_claims"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    besitos_received = Column(Integer, nullable=False)
    claimed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Para facilitar consultas de "último reclamo"
    __table_args__ = (
        # Índice compuesto para consultas eficientes
    )
