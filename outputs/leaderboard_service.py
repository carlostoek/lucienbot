"""
LeaderboardService - Servicio de Gamificación para Leaderboards

Gestiona clasificaciones de usuarios basadas en besitos acumulados.
Pertenece al dominio de Gamificación.

Autor: Lucien Bot
Fecha: 2026-05-05
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from models.models import BesitoBalance, BesitoTransaction, TransactionSource
from models.database import SessionLocal
import logging

logger = logging.getLogger(__name__)


class LeaderboardService:
    """Servicio para gestión de leaderboards y clasificaciones"""

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

    # ==================== TOP USERS ====================

    def get_top_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene el top de usuarios con más besitos.

        Args:
            limit: Número máximo de usuarios a devolver (default 10)

        Returns:
            Lista de dicts con user_id, balance, total_earned, rank
        """
        db = self._get_db()

        results = db.query(
            BesitoBalance.user_id,
            BesitoBalance.balance,
            BesitoBalance.total_earned
        ).order_by(desc(BesitoBalance.balance)).limit(limit).all()

        leaderboard = []
        for rank, row in enumerate(results, start=1):
            leaderboard.append({
                'rank': rank,
                'user_id': row.user_id,
                'balance': row.balance,
                'total_earned': row.total_earned
            })
            logger.info(
                f"Leaderboard: usuario {row.user_id} rank {rank} con {row.balance} besitos",
                extra={'user_id': row.user_id, 'rank': rank}
            )

        return leaderboard

    # ==================== USER RANK ====================

    def get_user_rank(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene la posición de un usuario en el leaderboard.

        Args:
            user_id: ID del usuario

        Returns:
            Dict con rank, balance, total_earned o None si no existe
        """
        db = self._get_db()

        # Subquery para contar usuarios con mayor balance
        rank_subquery = db.query(
            func.count(BesitoBalance.user_id)
        ).filter(
            BesitoBalance.balance > db.query(
                BesitoBalance.balance
            ).filter(BesitoBalance.user_id == user_id).scalar_subquery()
        ).scalar_subquery()

        balance = db.query(BesitoBalance).filter(
            BesitoBalance.user_id == user_id
        ).first()

        if not balance:
            logger.info(f"User {user_id} no encontrado en leaderboard")
            return None

        rank = rank_subquery + 1

        logger.info(
            f"User rank consultado: {user_id} está en posición {rank}",
            extra={'user_id': user_id, 'rank': rank}
        )

        return {
            'rank': rank,
            'user_id': user_id,
            'balance': balance.balance,
            'total_earned': balance.total_earned
        }

    # ==================== UPDATE SCORE ====================

    def update_score(self, user_id: int, amount: int, source: TransactionSource,
                     description: str = None) -> bool:
        """
        Actualiza el score (besitos) de un usuario.

        Args:
            user_id: ID del usuario
            amount: Cantidad a agregar (positiva) o quitar (negativa)
            source: Fuente de la transacción
            description: Descripción opcional

        Returns:
            True si se actualizó correctamente
        """
        db = self._get_db()

        try:
            # Obtener o crear balance con lock
            balance = db.query(BesitoBalance).filter(
                BesitoBalance.user_id == user_id
            ).with_for_update().first()

            if not balance:
                balance = BesitoBalance(
                    user_id=user_id,
                    balance=0,
                    total_earned=0,
                    total_spent=0
                )
                db.add(balance)
                db.flush()

            # Actualizar según signo del amount
            if amount >= 0:
                balance.balance += amount
                balance.total_earned += amount
            else:
                if balance.balance < abs(amount):
                    logger.warning(f"Saldo insuficiente para user {user_id}")
                    return False
                balance.balance += amount  # amount es negativo
                balance.total_spent += abs(amount)

            # Registrar transacción
            transaction = BesitoTransaction(
                user_id=user_id,
                amount=amount,
                type=TransactionSource.CREDIT if amount >= 0 else TransactionSource.DEBIT,
                source=source,
                description=description
            )
            db.add(transaction)
            db.commit()

            logger.info(
                f"Score actualizado: user {user_id} {'+' if amount >= 0 else ''}{amount} besitos",
                extra={'user_id': user_id, 'amount': amount, 'source': source.value}
            )
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Error actualizando score para user {user_id}: {e}")
            return False

    # ==================== NEARBY RANKS ====================

    def get_users_around_rank(self, user_id: int, range_: int = 2) -> List[Dict[str, Any]]:
        """
        Obtiene usuarios cercanos a la posición del usuario.

        Args:
            user_id: ID del usuario
            range_: Número de usuarios antes y después (default 2)

        Returns:
            Lista de dicts con rank, user_id, balance
        """
        user_rank_info = self.get_user_rank(user_id)
        if not user_rank_info:
            return []

        db = self._get_db()
        rank = user_rank_info['rank']

        # Obtener usuarios desde (rank - range_) hasta (rank + range_)
        offset = max(0, rank - range_ - 1)
        limit = range_ * 2 + 1

        results = db.query(
            BesitoBalance.user_id,
            BesitoBalance.balance
        ).order_by(desc(BesitoBalance.balance)).offset(offset).limit(limit).all()

        leaderboard = []
        for i, row in enumerate(results):
            actual_rank = offset + i + 1
            leaderboard.append({
                'rank': actual_rank,
                'user_id': row.user_id,
                'balance': row.balance,
                'is_current_user': row.user_id == user_id
            })

        return leaderboard