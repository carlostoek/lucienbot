"""
Servicio de Leaderboard - Lucien Bot

Gestiona las clasificaciones (leaderboards) basadas en besitos acumulados.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, text
from models.models import BesitoBalance, User
from models.database import SessionLocal
import logging

logger = logging.getLogger(__name__)


class LeaderboardService:
    """Servicio para leaderboards de gamificacion"""

    DEFAULT_LIMIT = 10
    MAX_LIMIT = 100

    def __init__(self, db: Session = None):
        self.db = db
        self._owns_session = db is None

    def _get_db(self) -> Session:
        """Obtiene la sesion de base de datos activa."""
        if self.db is None:
            self.db = SessionLocal()
        return self.db

    def close(self):
        """Cierra la sesion de base de datos si fue creada por este servicio."""
        if self._owns_session and self.db:
            self.db.close()
            self.db = None

    def get_top_users(self, limit: int = DEFAULT_LIMIT, scope: str = "global") -> List[Dict[str, Any]]:
        """
        Obtiene el top N de usuarios por besitos.

        Args:
            limit: Numero de usuarios a devolver (default 10, max 100)
            scope: 'global' o 'weekly' (futuro: 'monthly')

        Returns:
            Lista de diccionarios con user_id, username, balance, rank
        """
        if limit <= 0:
            limit = self.DEFAULT_LIMIT
        if limit > self.MAX_LIMIT:
            limit = self.MAX_LIMIT

        db = self._get_db()

        # Query: usuarios con saldo > 0, ordenados por balance descendente
        query = (
            db.query(BesitoBalance, User)
            .join(User, BesitoBalance.user_id == User.telegram_id, isouter=True)
            .filter(BesitoBalance.balance > 0)
            .order_by(desc(BesitoBalance.balance))
            .limit(limit)
        )

        results = query.all()

        leaderboard = []
        for rank, (balance, user) in enumerate(results, start=1):
            leaderboard.append({
                "rank": rank,
                "user_id": balance.user_id,
                "username": user.username if user else None,
                "first_name": user.first_name if user else None,
                "balance": balance.balance,
                "total_earned": balance.total_earned,
            })

        logger.info(f"leaderboard_service - get_top_users - scope:{scope}, limit:{limit}, count:{len(leaderboard)}")
        return leaderboard

    def get_user_rank(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene el ranking actual de un usuario.

        Args:
            user_id: ID de Telegram del usuario

        Returns:
            Diccionarios con rank, balance, total_above, total_below, o None si no tiene saldo
        """
        db = self._get_db()

        # Obtener el balance del usuario
        balance = db.query(BesitoBalance).filter(
            BesitoBalance.user_id == user_id
        ).first()

        if not balance:
            logger.debug(f"leaderboard_service - get_user_rank - user:{user_id} - no balance found")
            return None

        # Contar usuarios con balance mayor
        count_above = db.query(func.count(BesitoBalance.user_id)).filter(
            BesitoBalance.balance > balance.balance
        ).scalar()

        rank = count_above + 1

        # Contar total de usuarios con balance > 0
        total_active = db.query(func.count(BesitoBalance.user_id)).filter(
            BesitoBalance.balance > 0
        ).scalar()

        result = {
            "rank": rank,
            "user_id": user_id,
            "balance": balance.balance,
            "total_earned": balance.total_earned,
            "total_active_users": total_active,
        }

        logger.info(f"leaderboard_service - get_user_rank - user:{user_id}, rank:{rank}/{total_active}")
        return result

    def update_score(self, user_id: int, delta: int, reason: str = None) -> bool:
        """
        Actualiza el puntaje de un usuario en el leaderboard.
        Wrapper sobre BesitoService para mantener compatibilidad.

        Args:
            user_id: ID de Telegram del usuario
            delta: Cambio en el puntaje (positivo = credito, negativo = debito)
            reason: Descripcion de la causa del cambio

        Returns:
            True si se actualizo correctamente
        """
        from models.models import TransactionSource
        from services.besito_service import BesitoService

        if delta == 0:
            return True

        besito_service = BesitoService(self.db)
        try:
            if delta > 0:
                source = TransactionSource.ADMIN
                success = besito_service.credit_besitos(
                    user_id=user_id,
                    amount=delta,
                    source=source,
                    description=reason or "Leaderboard score adjustment"
                )
            else:
                source = TransactionSource.ADMIN
                success = besito_service.debit_besitos(
                    user_id=user_id,
                    amount=abs(delta),
                    source=source,
                    description=reason or "Leaderboard score adjustment"
                )

            logger.info(f"leaderboard_service - update_score - user:{user_id}, delta:{delta}, success:{success}")
            return success
        finally:
            besito_service.close()

    def get_user_position_around(self, user_id: int, radius: int = 2) -> Optional[Dict[str, Any]]:
        """
        Obtiene el ranking del usuario junto con los usuarios inmediatamente
        arriba y abajo en el leaderboard.

        Args:
            user_id: ID de Telegram del usuario
            radius: Cuantos usuarios mostrar antes y despues (default 2)

        Returns:
            Diccionario con 'user' (ranking del usuario) y 'surrounding' (lista)
            o None si el usuario no tiene saldo
        """
        user_rank = self.get_user_rank(user_id)
        if not user_rank:
            return None

        rank = user_rank["rank"]
        limit = radius * 2 + 1
        offset = max(0, rank - radius - 1)

        db = self._get_db()
        query = (
            db.query(BesitoBalance, User)
            .join(User, BesitoBalance.user_id == User.telegram_id, isouter=True)
            .filter(BesitoBalance.balance > 0)
            .order_by(desc(BesitoBalance.balance))
            .limit(limit)
            .offset(offset)
        )

        results = query.all()

        surrounding = []
        for i, (balance, user) in enumerate(results):
            surrounding.append({
                "rank": offset + i + 1,
                "user_id": balance.user_id,
                "username": user.username if user else None,
                "first_name": user.first_name if user else None,
                "balance": balance.balance,
                "is_current_user": balance.user_id == user_id,
            })

        return {
            "user": user_rank,
            "surrounding": surrounding,
        }