"""
TriviaDiscountService - Sistema de descuentos por trivia

Lógica de negocio para el sistema de descuentos trivia.
COMPLETAMENTE SEPARADO del PromotionService comercial.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc
from models.models import (
    TriviaPromotionConfig, Tier, DiscountCode, UserStreak,
    TriviaGameRecord, QuestionSet, Question, TriviaConfig,
    DiscountCodeStatus, GameResult
)
from models.database import SessionLocal
import secrets
import logging

logger = logging.getLogger(__name__)


class TriviaDiscountService:
    """Servicio para gestión de descuentos trivia"""

    def __init__(self, db: Session = None):
        self.db = db
        self._owns_session = db is None

    def _get_db(self) -> Session:
        """Obtiene la sesión de base de datos activa."""
        if self.db is None:
            self.db = SessionLocal()
        return self.db

    def close(self):
        """Cierra la sesión de base de datos si fue creada por este servicio."""
        if self._owns_session and self.db:
            self.db.close()
            self.db = None

    # ==================== PROMOTION CONFIG ====================

    def create_promotion_config(self, data: dict) -> Optional[TriviaPromotionConfig]:
        """Crea una nueva configuración de promoción trivia"""
        db = self._get_db()
        config = TriviaPromotionConfig(
            name=data.get('name'),
            description=data.get('description'),
            is_active=data.get('is_active', True),
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            duration_days=data.get('duration_days', 7),
            auto_reset=data.get('auto_reset', True),
            question_set_id=data.get('question_set_id')
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        logger.info(f"TriviaPromotionConfig creada: {config.id} - {config.name}")
        return config

    def get_promotion_config(self, config_id: int) -> Optional[TriviaPromotionConfig]:
        """Obtiene una configuración de promoción por ID"""
        db = self._get_db()
        return db.query(TriviaPromotionConfig).filter(
            TriviaPromotionConfig.id == config_id
        ).first()

    def get_active_promotions(self) -> List[TriviaPromotionConfig]:
        """Obtiene todas las promociones activas"""
        db = self._get_db()
        now = datetime.now(timezone.utc)
        return db.query(TriviaPromotionConfig).filter(
            TriviaPromotionConfig.is_active == True,
            (TriviaPromotionConfig.start_date == None) | (TriviaPromotionConfig.start_date <= now),
            (TriviaPromotionConfig.end_date == None) | (TriviaPromotionConfig.end_date >= now)
        ).all()

    def update_promotion_config(self, config_id: int, data: dict) -> bool:
        """Actualiza una configuración de promoción"""
        db = self._get_db()
        config = self.get_promotion_config(config_id)
        if not config:
            return False

        allowed_fields = [
            'name', 'description', 'is_active', 'start_date',
            'end_date', 'duration_days', 'auto_reset', 'question_set_id'
        ]
        for field, value in data.items():
            if field in allowed_fields and hasattr(config, field):
                setattr(config, field, value)

        db.commit()
        logger.info(f"TriviaPromotionConfig {config_id} actualizada")
        return True

    def delete_promotion_config(self, config_id: int) -> bool:
        """Elimina una configuración de promoción"""
        db = self._get_db()
        config = db.query(TriviaPromotionConfig).filter(
            TriviaPromotionConfig.id == config_id
        ).first()
        if not config:
            return False

        db.delete(config)
        db.commit()
        logger.info(f"TriviaPromotionConfig {config_id} eliminada")
        return True

    def pause_promotion(self, config_id: int) -> bool:
        """Pausa una promoción"""
        db = self._get_db()
        config = self.get_promotion_config(config_id)
        if not config:
            return False

        config.is_active = False
        db.commit()
        logger.info(f"TriviaPromotionConfig {config_id} pausada")
        return True

    def resume_promotion(self, config_id: int) -> bool:
        """Reanuda una promoción"""
        db = self._get_db()
        config = self.get_promotion_config(config_id)
        if not config:
            return False

        config.is_active = True
        db.commit()
        logger.info(f"TriviaPromotionConfig {config_id} reanudada")
        return True

    # ==================== TIERS ====================

    def get_tier(self, tier_id: int) -> Optional[Tier]:
        """Obtiene un tier por ID"""
        db = self._get_db()
        return db.query(Tier).filter(Tier.id == tier_id).first()

    def get_tiers_by_promotion(self, promotion_id: int) -> List[Tier]:
        """Obtiene todos los tiers de una promoción"""
        db = self._get_db()
        return db.query(Tier).filter(
            Tier.promotion_config_id == promotion_id
        ).order_by(Tier.streak_threshold).all()

    def get_available_codes_count(self, tier_id: int) -> int:
        """Retorna la cantidad de códigos disponibles (max - generated)"""
        db = self._get_db()
        tier = self.get_tier(tier_id)
        if not tier:
            return 0
        return max(0, tier.max_codes - tier.codes_generated)

    def add_codes_to_tier(self, tier_id: int, count: int) -> bool:
        """Agrega códigos disponibles a un tier (incrementa max_codes)"""
        db = self._get_db()
        tier = self.get_tier(tier_id)
        if not tier:
            return False

        tier.max_codes += count
        db.commit()
        logger.info(f"Tier {tier_id}: agregados {count} códigos (max_codes={tier.max_codes})")
        return True

    # ==================== CODE GENERATION (ATOMIC) ====================

    def generate_code(self, tier_id: int, user_id: int) -> Optional[DiscountCode]:
        """
        Genera un código de descuento de forma atómica.
        Usa SELECT FOR UPDATE para prevenir generación concurrente.
        Retorna None si no hay códigos disponibles.
        """
        db = self._get_db()

        # Bloquear el tier para prevenir generación concurrente
        tier = db.query(Tier).filter(Tier.id == tier_id).with_for_update().first()
        if not tier:
            logger.warning(f"generate_code: Tier {tier_id} no encontrado")
            return None

        # Verificar disponibilidad
        available = tier.max_codes - tier.codes_generated
        if available <= 0:
            logger.info(f"generate_code: Sin códigos disponibles para tier {tier_id}")
            return None

        # Generar código único
        code_str = f"TRI-{secrets.token_hex(3).upper()}"
        while db.query(DiscountCode).filter(DiscountCode.code == code_str).first():
            code_str = f"TRI-{secrets.token_hex(3).upper()}"

        # Calcular fecha de expiración (30 días)
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)

        # Crear el código
        code = DiscountCode(
            code=code_str,
            tier_id=tier_id,
            user_id=user_id,
            status=DiscountCodeStatus.AVAILABLE,
            expires_at=expires_at
        )
        db.add(code)

        # Incrementar contador atómicamente
        tier.codes_generated += 1

        db.commit()
        db.refresh(code)

        logger.info(f"Código generado: {code_str} para usuario {user_id}, tier {tier_id}")
        return code

    def claim_code(self, code_id: int) -> bool:
        """Marca un código como reclamado (claimed)"""
        db = self._get_db()
        code = db.query(DiscountCode).filter(DiscountCode.id == code_id).first()
        if not code or code.status != DiscountCodeStatus.AVAILABLE:
            return False

        code.status = DiscountCodeStatus.CLAIMED
        code.claimed_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(f"Código {code_id} reclamado")
        return True

    def use_code(self, code_id: int) -> bool:
        """Marca un código como usado"""
        db = self._get_db()
        code = db.query(DiscountCode).filter(DiscountCode.id == code_id).first()
        if not code or code.status not in (DiscountCodeStatus.AVAILABLE, DiscountCodeStatus.CLAIMED):
            return False

        code.status = DiscountCodeStatus.USED
        code.used_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(f"Código {code_id} usado")
        return True

    def cancel_code(self, code_id: int) -> bool:
        """Cancela un código de descuento"""
        db = self._get_db()
        code = db.query(DiscountCode).filter(DiscountCode.id == code_id).first()
        if not code:
            return False

        code.status = DiscountCodeStatus.CANCELLED
        db.commit()

        logger.info(f"Código {code_id} cancelado")
        return True

    def expire_code(self, code_id: int) -> bool:
        """Marca un código como expirado"""
        db = self._get_db()
        code = db.query(DiscountCode).filter(DiscountCode.id == code_id).first()
        if not code:
            return False

        code.status = DiscountCodeStatus.EXPIRED
        db.commit()

        logger.info(f"Código {code_id} expirado")
        return True

    def get_user_active_code(self, user_id: int) -> Optional[DiscountCode]:
        """Obtiene el código activo de un usuario (claimed pero no usado)"""
        db = self._get_db()
        return db.query(DiscountCode).filter(
            DiscountCode.user_id == user_id,
            DiscountCode.status == DiscountCodeStatus.CLAIMED
        ).first()

    def get_codes_by_tier(self, tier_id: int, filters: dict = None) -> List[DiscountCode]:
        """Obtiene códigos de un tier con filtros opcionales"""
        db = self._get_db()
        query = db.query(DiscountCode).filter(DiscountCode.tier_id == tier_id)

        if filters:
            if 'status' in filters:
                query = query.filter(DiscountCode.status == filters['status'])
            if 'user_id' in filters:
                query = query.filter(DiscountCode.user_id == filters['user_id'])
            if 'expired_only' in filters and filters['expired_only']:
                query = query.filter(DiscountCode.expires_at < datetime.now(timezone.utc))
            if 'limit' in filters:
                query = query.limit(filters['limit'])
            if 'offset' in filters:
                query = query.offset(filters['offset'])

        return query.order_by(desc(DiscountCode.generated_at)).all()

    # ==================== STREAKS ====================

    def get_user_streak(self, user_id: int) -> Optional[UserStreak]:
        """Obtiene la racha activa de un usuario"""
        db = self._get_db()
        return db.query(UserStreak).filter(
            UserStreak.user_id == user_id,
            UserStreak.is_active == True
        ).first()

    def create_streak(self, user_id: int, promotion_id: int) -> UserStreak:
        """Crea una nueva racha para un usuario"""
        db = self._get_db()
        streak = UserStreak(
            user_id=user_id,
            promotion_config_id=promotion_id,
            current_streak=0,
            is_active=True,
            streak_started_at=datetime.now(timezone.utc)
        )
        db.add(streak)
        db.commit()
        db.refresh(streak)

        logger.info(f"Streak creado para usuario {user_id}, promoción {promotion_id}")
        return streak

    def increment_streak(self, user_id: int) -> Tuple[UserStreak, Optional[Tier]]:
        """
        Incrementa la racha de un usuario.
        Retorna (streak, tier) donde tier es el nuevo tier alcanzado (si cambió).
        """
        db = self._get_db()
        streak = self.get_user_streak(user_id)
        if not streak:
            return None, None

        streak.current_streak += 1
        streak.last_answered_at = datetime.now(timezone.utc)

        # Buscar si alcanzó nuevo tier
        new_tier = None
        if streak.promotion_config_id:
            tiers = self.get_tiers_by_promotion(streak.promotion_config_id)
            for tier in tiers:
                if streak.current_streak >= tier.streak_threshold:
                    if streak.active_tier_id != tier.id:
                        new_tier = tier
                        streak.active_tier_id = tier.id

        db.commit()
        db.refresh(streak)

        logger.info(f"Streak usuario {user_id} incrementado a {streak.current_streak}")
        return streak, new_tier

    def invalidate_streak(self, user_id: int) -> None:
        """
        Invalida la racha (llamado por APScheduler cuando expira el timeout).
        """
        db = self._get_db()
        streak = self.get_user_streak(user_id)
        if not streak:
            return

        streak.is_active = False
        streak.active_tier_id = None
        db.commit()

        logger.info(f"Streak invalidado para usuario {user_id}")

    def reset_streak(self, user_id: int) -> None:
        """Resetea la racha de un usuario a cero"""
        db = self._get_db()
        streak = self.get_user_streak(user_id)
        if not streak:
            return

        streak.current_streak = 0
        streak.active_tier_id = None
        streak.active_code_id = None
        streak.streak_started_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(f"Streak reseteado para usuario {user_id}")

    # ==================== GAME RECORDS ====================

    def create_game_record(
        self,
        user_id: int,
        game_type: str,
        result: GameResult,
        promotion_config_id: int = None,
        discount_code_id: int = None,
        questions_answered: int = 0,
        correct_answers: int = 0,
        final_streak: int = 0
    ) -> TriviaGameRecord:
        """Crea un registro de partida trivia"""
        db = self._get_db()
        record = TriviaGameRecord(
            user_id=user_id,
            promotion_config_id=promotion_config_id,
            discount_code_id=discount_code_id,
            game_type=game_type,
            questions_answered=questions_answered,
            correct_answers=correct_answers,
            final_streak=final_streak,
            result=result
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        logger.info(f"TriviaGameRecord creado: usuario {user_id}, resultado {result}")
        return record

    def get_user_game_records(
        self,
        user_id: int,
        limit: int = 20
    ) -> List[TriviaGameRecord]:
        """Obtiene los registros de trivia de un usuario"""
        db = self._get_db()
        return db.query(TriviaGameRecord).filter(
            TriviaGameRecord.user_id == user_id
        ).order_by(desc(TriviaGameRecord.played_at)).limit(limit).all()

    # ==================== QUESTION SETS ====================

    def get_question_set(self, set_id: int) -> Optional[QuestionSet]:
        """Obtiene un set de preguntas por ID"""
        db = self._get_db()
        return db.query(QuestionSet).filter(QuestionSet.id == set_id).first()

    def get_all_question_sets(self, active_only: bool = True) -> List[QuestionSet]:
        """Obtiene todos los sets de preguntas"""
        db = self._get_db()
        query = db.query(QuestionSet)
        if active_only:
            query = query.filter(QuestionSet.is_active == True)
        return query.order_by(desc(QuestionSet.created_at)).all()

    def get_questions_by_set(self, set_id: int) -> List[Question]:
        """Obtiene las preguntas de un set"""
        db = self._get_db()
        return db.query(Question).filter(
            Question.question_set_id == set_id
        ).all()

    # ==================== TRIVIA CONFIG ====================

    def get_trivia_config(self) -> Optional[TriviaConfig]:
        """Obtiene la configuración global de trivia (singleton)"""
        db = self._get_db()
        return db.query(TriviaConfig).first()

    def update_trivia_config(self, **kwargs) -> bool:
        """Actualiza la configuración global de trivia"""
        db = self._get_db()
        config = self.get_trivia_config()
        if not config:
            return False

        allowed_fields = [
            'free_daily_limit', 'vip_daily_limit',
            'vip_exclusive_daily_limit', 'streak_timeout_minutes'
        ]
        for field, value in kwargs.items():
            if field in allowed_fields and hasattr(config, field):
                setattr(config, field, value)

        db.commit()
        logger.info("TriviaConfig actualizada")
        return True

    # ==================== STATS ====================

    def get_promotion_stats(self, promotion_id: int) -> dict:
        """Obtiene estadísticas de una promoción"""
        db = self._get_db()

        tiers = self.get_tiers_by_promotion(promotion_id)
        total_codes = 0
        total_generated = 0
        tier_stats = []

        for tier in tiers:
            total_codes += tier.max_codes
            total_generated += tier.codes_generated
            tier_stats.append({
                'tier_id': tier.id,
                'tier_number': tier.tier_number,
                'streak_threshold': tier.streak_threshold,
                'discount_percentage': tier.discount_percentage,
                'max_codes': tier.max_codes,
                'codes_generated': tier.codes_generated,
                'available': max(0, tier.max_codes - tier.codes_generated)
            })

        return {
            'promotion_id': promotion_id,
            'total_codes': total_codes,
            'total_generated': total_generated,
            'total_available': max(0, total_codes - total_generated),
            'tiers': tier_stats
        }