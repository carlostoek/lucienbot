"""
Servicio de Racha Diaria - Lucien Bot

Gestiona el sistema de racha diaria con ventana de gracia de 48 horas.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from models.database import SessionLocal
from models.models import TransactionSource
from services.besito_service import BesitoService
import logging

logger = logging.getLogger(__name__)


class DailyStreakService:
    """Servicio para gestión de racha diaria"""

    # Constantes de ventana de gracia
    GRACE_PERIOD_HOURS = 48
    MIN_HOURS_BETWEEN_CLAIMS = 20
    BONUS_PER_STREAK_DAY = 5
    MAX_BONUS = 50

    def __init__(self, db: Session = None):
        self.db = db
        self._owns_session = db is None

    def _get_db(self) -> Session:
        if self.db is None:
            self.db = SessionLocal()
        return self.db

    def close(self):
        if self._owns_session and self.db:
            self.db.close()
            self.db = None

    def __del__(self):
        self.close()

    def _get_besito_service(self) -> BesitoService:
        return BesitoService(self._get_db())

    # ==================== MODELO DE RACHA ====================
    # Requiere: modelo User con campos streak (int) y last_checkin (datetime)
    # Si no existe, usar BesitoBalance/DailyGiftClaim como proxy

    def _get_streak_data(self, user_id: int) -> Dict[str, Any]:
        """
        Obtiene datos de racha del usuario.
        Usa BesitoBalance como proxy si User no tiene streak.
        """
        from models.models import BesitoBalance, DailyGiftClaim
        from sqlalchemy import desc

        db = self._get_db()

        # Intentar obtener de BesitoBalance (proxy)
        balance = db.query(BesitoBalance).filter_by(user_id=user_id).first()

        # Último reclamo de DailyGift para calcular racha
        last_claim = db.query(DailyGiftClaim).filter(
            DailyGiftClaim.user_id == user_id
        ).order_by(desc(DailyGiftClaim.claimed_at)).first()

        # Calcular streak basado en historial de reclamos
        streak = 0
        last_checkin = None

        if last_claim:
            last_checkin = last_claim.claimed_at
            # Calcular días consecutivos
            claims = db.query(DailyGiftClaim).filter(
                DailyGiftClaim.user_id == user_id
            ).order_by(desc(DailyGiftClaim.claimed_at)).all()

            if claims:
                # streak_days = streak del usuario
                streak = getattr(balance, 'streak', 0) if balance else 0

        return {
            'streak': streak or 0,
            'last_checkin': last_checkin,
            'user_id': user_id
        }

    def _calculate_grace_status(self, last_checkin: Optional[datetime]) -> Dict[str, Any]:
        """
        Calcula estado de ventana de gracia.
        Returns: {status, hours_since, can_claim, message}
        """
        if last_checkin is None:
            return {
                'status': 'new_user',
                'hours_since': None,
                'can_claim': True,
                'message': 'Racha nueva - comienza hoy'
            }

        now = datetime.utcnow()
        # Normalizar a naive datetime para comparación
        lc = last_checkin.replace(tzinfo=None) if last_checkin.tzinfo else last_checkin
        hours_since = (now - lc).total_seconds() / 3600

        if hours_since < self.MIN_HOURS_BETWEEN_CLAIMS:
            return {
                'status': 'already_claimed',
                'hours_since': hours_since,
                'can_claim': False,
                'message': f'Aún no ha pasado el tiempo mínimo ({self.MIN_HOURS_BETWEEN_CLAIMS}h)'
            }

        if hours_since <= self.GRACE_PERIOD_HOURS:
            return {
                'status': 'grace_period',
                'hours_since': hours_since,
                'can_claim': True,
                'message': f'Ventana de gracia activa ({int(hours_since)}h desde último)'
            }

        return {
            'status': 'streak_lost',
            'hours_since': hours_since,
            'can_claim': True,  # Puede reclamar pero streak se reinicia
            'message': f'Racha rota - habían pasado {int(hours_since)}h'
        }

    # ==================== PROCESAMIENTO DE RECLAMO ====================

    def get_streak_status(self, user_id: int) -> Dict[str, Any]:
        """
        Obtiene estado actual de racha para mostrar al usuario.
        Returns: {streak, grace_status, can_claim, message, bonus_preview}
        """
        data = self._get_streak_data(user_id)
        grace = self._calculate_grace_status(data['last_checkin'])

        bonus_preview = min(data['streak'] * self.BONUS_PER_STREAK_DAY, self.MAX_BONUS)

        return {
            'streak': data['streak'],
            'grace_status': grace['status'],
            'hours_since': grace['hours_since'],
            'can_claim': grace['can_claim'],
            'message': grace['message'],
            'bonus_preview': bonus_preview
        }

    def claim_daily_streak(self, user_id: int) -> Dict[str, Any]:
        """
        Procesa el reclamo de racha diaria con ventana de gracia.

        Returns:
            dict con keys:
            - status: 'success' | 'already_claimed' | 'streak_lost' | 'grace_claimed'
            - message: str descriptivo
            - bonus: int besitos ganados
            - new_streak: int nueva racha
            - streak_was_lost: bool indica si perdió racha anterior
            - lost_streak: int racha perdida (si apply)
        """
        data = self._get_streak_data(user_id)
        grace = self._calculate_grace_status(data['last_checkin'])

        # Caso 1: Ya reclamó hoy (< 20h)
        if grace['status'] == 'already_claimed':
            return {
                'status': 'already_claimed',
                'message': f'Ya reclamaste tu racha hoy. Espera {int(self.MIN_HOURS_BETWEEN_CLAIMS - grace["hours_since"])}h más.',
                'bonus': 0,
                'new_streak': data['streak'],
                'streak_was_lost': False,
                'lost_streak': 0
            }

        # Calcular bonus
        current_streak = data['streak']

        # Caso 2: Ventana de gracia (20-48h) - mantiene streak
        if grace['status'] == 'grace_period':
            new_streak = current_streak + 1
            bonus = min(new_streak * self.BONUS_PER_STREAK_DAY, self.MAX_BONUS)

            # Registrar reclamo y acreditar
            self._record_claim(user_id, bonus, 'grace_period')

            logger.info(
                f"daily_streak_service - claim_daily_streak - "
                f"{user_id} - grace_claimed - streak:{new_streak}, bonus:{bonus}"
            )

            return {
                'status': 'grace_claimed',
                'message': f'🔥 Racha mantenida: {new_streak} días (+{bonus} besitos)',
                'bonus': bonus,
                'new_streak': new_streak,
                'streak_was_lost': False,
                'lost_streak': 0
            }

        # Caso 3: Streak rota (>48h) - reinicia
        if grace['status'] == 'streak_lost':
            lost_streak = current_streak
            new_streak = 1
            bonus = self.BONUS_PER_STREAK_DAY  # 5 besitos por nuevo inicio

            self._record_claim(user_id, bonus, 'streak_reset')

            logger.info(
                f"daily_streak_service - claim_daily_streak - "
                f"{user_id} - streak_lost:{lost_streak} - starting_new:{new_streak}"
            )

            return {
                'status': 'streak_lost',
                'message': f'💔 Racha perdida ({lost_streak} días). Empezando de nuevo con +{bonus} besitos.',
                'bonus': bonus,
                'new_streak': new_streak,
                'streak_was_lost': True,
                'lost_streak': lost_streak
            }

        # Caso 4: Nuevo usuario
        new_streak = 1
        bonus = self.BONUS_PER_STREAK_DAY

        self._record_claim(user_id, bonus, 'new_user')

        return {
            'status': 'new_user',
            'message': f'🔥 ¡Bienvenido! Comienza tu racha con +{bonus} besitos.',
            'bonus': bonus,
            'new_streak': new_streak,
            'streak_was_lost': False,
            'lost_streak': 0
        }

    def _record_claim(self, user_id: int, bonus: int, claim_type: str) -> None:
        """Registra el reclamo de racha y actualiza streak"""
        from models.models import BesitoBalance, BesitoTransaction, DailyGiftClaim

        db = self._get_db()
        besito_service = self._get_besito_service()

        try:
            # Registrar DailyGiftClaim (independiente de streak)
            claim = DailyGiftClaim(
                user_id=user_id,
                besitos_received=bonus
            )
            db.add(claim)

            # Acreditar besitos
            besito_service.credit_besitos(
                user_id=user_id,
                amount=bonus,
                source=TransactionSource.DAILY_GIFT,
                description=f'Racha diaria ({claim_type})'
            )

            db.commit()

        except Exception as e:
            db.rollback()
            logger.error(f"daily_streak_service - _record_claim - {user_id} - error: {e}")
            raise

    # ==================== CONSULTA DE ESTADÍSTICAS ====================

    def get_streak_history(self, user_id: int, limit: int = 30) -> list:
        """Obtiene historial de reclamos de racha"""
        from models.models import DailyGiftClaim

        return self._get_db().query(DailyGiftClaim).filter(
            DailyGiftClaim.user_id == user_id
        ).order_by(DailyGiftClaim.claimed_at.desc()).limit(limit).all()
