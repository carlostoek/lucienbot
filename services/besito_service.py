"""
Servicio de Besitos - Lucien Bot

Gestiona la moneda virtual (besitos) del sistema de gamificación.
"""
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from models.models import (
    BesitoBalance, BesitoTransaction, 
    TransactionType, TransactionSource
)
from models.database import SessionLocal
import logging

logger = logging.getLogger(__name__)


class BesitoService:
    """Servicio para gestión de besitos (moneda virtual)"""
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
    
    # ==================== GESTIÓN DE SALDO ====================
    
    def get_or_create_balance(self, user_id: int) -> BesitoBalance:
        """Obtiene o crea el saldo de un usuario"""
        balance = self.db.query(BesitoBalance).filter(
            BesitoBalance.user_id == user_id
        ).first()
        
        if not balance:
            balance = BesitoBalance(
                user_id=user_id,
                balance=0,
                total_earned=0,
                total_spent=0
            )
            self.db.add(balance)
            self.db.commit()
            self.db.refresh(balance)
            logger.info(f"Nuevo saldo creado para usuario {user_id}")
        
        return balance
    
    def get_balance(self, user_id: int) -> int:
        """Obtiene el saldo actual de un usuario"""
        balance = self.get_or_create_balance(user_id)
        return balance.balance
    
    def get_balance_with_stats(self, user_id: int) -> dict:
        """Obtiene el saldo con estadísticas"""
        balance = self.get_or_create_balance(user_id)
        return {
            'balance': balance.balance,
            'total_earned': balance.total_earned,
            'total_spent': balance.total_spent
        }
    
    # ==================== TRANSACCIONES ====================
    
    def credit_besitos(self, user_id: int, amount: int, source: TransactionSource,
                       description: str = None, reference_id: int = None) -> bool:
        """
        Acredita besitos a un usuario.
        
        Args:
            user_id: ID del usuario
            amount: Cantidad a acreditar (debe ser positiva)
            source: Fuente de la transacción
            description: Descripción opcional
            reference_id: ID de referencia (misión, compra, etc.)
        
        Returns:
            True si se acreditó correctamente
        """
        if amount <= 0:
            logger.error(f"Cantidad inválida para crédito: {amount}")
            return False
        
        try:
            balance = self.get_or_create_balance(user_id)
            
            # Actualizar saldo
            balance.balance += amount
            balance.total_earned += amount
            
            # Crear transacción
            transaction = BesitoTransaction(
                user_id=user_id,
                amount=amount,
                type=TransactionType.CREDIT,
                source=source,
                description=description,
                reference_id=reference_id
            )
            self.db.add(transaction)
            self.db.commit()
            
            logger.info(f"Acreditados {amount} besitos a usuario {user_id} - {source.value}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error acreditando besitos: {e}")
            return False
    
    def debit_besitos(self, user_id: int, amount: int, source: TransactionSource,
                      description: str = None, reference_id: int = None) -> bool:
        """
        Debita besitos de un usuario.
        
        Args:
            user_id: ID del usuario
            amount: Cantidad a debitar (debe ser positiva)
            source: Fuente de la transacción
            description: Descripción opcional
            reference_id: ID de referencia
        
        Returns:
            True si se debitó correctamente
        """
        if amount <= 0:
            logger.error(f"Cantidad inválida para débito: {amount}")
            return False
        
        try:
            balance = self.get_or_create_balance(user_id)
            
            # Verificar saldo suficiente
            if balance.balance < amount:
                logger.warning(f"Saldo insuficiente para usuario {user_id}: {balance.balance} < {amount}")
                return False
            
            # Actualizar saldo
            balance.balance -= amount
            balance.total_spent += amount
            
            # Crear transacción (cantidad negativa para débitos)
            transaction = BesitoTransaction(
                user_id=user_id,
                amount=-amount,
                type=TransactionType.DEBIT,
                source=source,
                description=description,
                reference_id=reference_id
            )
            self.db.add(transaction)
            self.db.commit()
            
            logger.info(f"Debitados {amount} besitos de usuario {user_id} - {source.value}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error debitando besitos: {e}")
            return False
    
    def has_sufficient_balance(self, user_id: int, amount: int) -> bool:
        """Verifica si un usuario tiene saldo suficiente"""
        balance = self.get_balance(user_id)
        return balance >= amount
    
    # ==================== HISTORIAL ====================
    
    def get_transaction_history(self, user_id: int, limit: int = 20) -> List[BesitoTransaction]:
        """Obtiene el historial de transacciones de un usuario"""
        return self.db.query(BesitoTransaction).filter(
            BesitoTransaction.user_id == user_id
        ).order_by(desc(BesitoTransaction.created_at)).limit(limit).all()
    
    def get_transactions_by_source(self, user_id: int, source: TransactionSource, 
                                   limit: int = 20) -> List[BesitoTransaction]:
        """Obtiene transacciones filtradas por fuente"""
        return self.db.query(BesitoTransaction).filter(
            BesitoTransaction.user_id == user_id,
            BesitoTransaction.source == source
        ).order_by(desc(BesitoTransaction.created_at)).limit(limit).all()
    
    # ==================== ESTADÍSTICAS ====================
    
    def get_top_users(self, limit: int = 10) -> List[BesitoBalance]:
        """Obtiene los usuarios con más besitos"""
        return self.db.query(BesitoBalance).order_by(
            desc(BesitoBalance.balance)
        ).limit(limit).all()
    
    def get_total_besitos_in_circulation(self) -> int:
        """Obtiene el total de besitos en circulación"""
        result = self.db.query(BesitoBalance).all()
        return sum(b.balance for b in result)
    
    def __del__(self):
        """Cierra la sesión de base de datos"""
        if hasattr(self, 'db'):
            self.db.close()
