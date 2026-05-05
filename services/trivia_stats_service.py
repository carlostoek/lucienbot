"""
Trivia Stats Service - Estadísticas de Promociones y Usuarios de Trivia

Proporciona métricas detalladas para promociones de trivia y usuarios.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import func
from models.models import (
    TriviaPromotionConfig,
    DiscountCode,
    DiscountCodeStatus,
    GameRecord,
    QuestionSet,
    User
)
from models.database import SessionLocal

logger = logging.getLogger(__name__)


class TriviaStatsService:
    """Servicio para estadísticas de promociones y usuarios de trivia"""

    def __init__(self, db: Session = None):
        """Inicializa el servicio con sesión opcional"""
        self._db = db
        self._owns_session = db is None

    def _get_db(self) -> Session:
        """Obtiene o crea sesión de base de datos"""
        if self._db is not None:
            return self._db
        return SessionLocal()

    def close(self):
        """Cierra la sesión si el servicio la posee"""
        if self._owns_session and self._db is not None:
            self._db.close()
            self._db = None

    def get_promotion_stats(self, config_id: int) -> dict:
        """Obtiene métricas para UNA promoción"""
        db = self._get_db()
        try:
            config = db.query(TriviaPromotionConfig).filter(
                TriviaPromotionConfig.id == config_id
            ).first()

            if not config:
                logger.info(f"trivia_stats_service - get_promotion_stats - {config_id} - not found")
                return {}

            # Contar códigos por status
            codes_by_status = {}
            for status in DiscountCodeStatus:
                count = db.query(DiscountCode).filter(
                    DiscountCode.config_id == config_id,
                    DiscountCode.status == status
                ).count()
                codes_by_status[status.value] = count

            total_codes = sum(codes_by_status.values())

            # Nombre de la promoción
            promo_name = config.promotion.name if config.promotion else config.custom_description or config.name

            # Question set name
            question_set_name = None
            if config.question_set_id:
                question_set = db.query(QuestionSet).filter(
                    QuestionSet.id == config.question_set_id
                ).first()
                if question_set:
                    question_set_name = question_set.name

            # Parse discount tiers
            tiers = []
            if config.discount_tiers:
                try:
                    tiers = json.loads(config.discount_tiers)
                except json.JSONDecodeError:
                    # Fallback to legacy fields
                    tiers = []
            elif config.required_streak and config.discount_percentage:
                # Legacy fallback
                tiers = [{
                    "streak": config.required_streak,
                    "discount": config.discount_percentage
                }]

            # Duration remaining
            duration_remaining = None
            if config.duration_minutes:
                from services.trivia_discount_service import TriviaDiscountService
                discount_service = TriviaDiscountService()
                duration_remaining = discount_service.get_time_remaining_formatted(config_id)
                discount_service.close()

            # Formatear fechas
            start_date_str = None
            end_date_str = None
            if config.start_date:
                start_date_str = config.start_date.isoformat()
            if config.end_date:
                end_date_str = config.end_date.isoformat()

            # Calcular porcentaje usado
            used_percentage = 0.0
            if config.max_codes > 0:
                used_codes = codes_by_status.get(DiscountCodeStatus.USED.value, 0)
                used_percentage = round((used_codes / config.max_codes * 100), 1)

            result = {
                "id": config.id,
                "name": promo_name,
                "status": config.status,
                "total_codes": total_codes,
                "codes_by_status": codes_by_status,
                "claimed": config.codes_claimed,
                "available": max(0, config.max_codes - config.codes_claimed),
                "max_codes": config.max_codes,
                "used_percentage": used_percentage,
                "tiers": tiers,
                "question_set": question_set_name,
                "duration_remaining": duration_remaining,
                "start_date": start_date_str,
                "end_date": end_date_str
            }

            logger.info(f"trivia_stats_service - get_promotion_stats - {config_id} - found: {total_codes} codes")
            return result
        except Exception as e:
            logger.error(f"trivia_stats_service - get_promotion_stats - {config_id} - error: {e}")
            return {}

    def get_all_promotions_stats(self) -> List[dict]:
        """Obtiene métricas para TODAS las promociones ordenadas por created_at DESC"""
        db = self._get_db()
        try:
            configs = db.query(TriviaPromotionConfig).order_by(
                TriviaPromotionConfig.created_at.desc()
            ).all()

            results = []
            for config in configs:
                stats = self.get_promotion_stats(config.id)
                if stats:
                    results.append(stats)

            logger.info(f"trivia_stats_service - get_all_promotions_stats - total: {len(results)} promotions")
            return results
        except Exception as e:
            logger.error(f"trivia_stats_service - get_all_promotions_stats - error: {e}")
            return []
