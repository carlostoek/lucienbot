"""
TriviaAdminService - Administración del sistema de descuentos trivia

Gestiona operaciones de admin para el sistema trivia discount:
- Configuración global (TriviaConfig singleton)
- Promociones y sus estadísticas
- Códigos de descuento y exportación CSV
- Rachas de usuarios y registros de juego
"""
import csv
import io
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from models.models import (
    TriviaConfig,
    TriviaPromotionConfig,
    Tier,
    DiscountCode,
    DiscountCodeStatus,
    UserStreak,
    TriviaGameRecord,
    GameResult
)
from models.database import SessionLocal

logger = logging.getLogger(__name__)


class TriviaAdminService:
    """Servicio para administración de trivia discount system"""

    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()

    def close(self):
        """Cierra la sesión de base de datos"""
        if hasattr(self, 'db') and self.db:
            self.db.close()

    # ==================== CONFIGURACIÓN GLOBAL ====================

    def get_limits(self) -> TriviaConfig:
        """
        Obtiene la configuración global de trivia (singleton).
        Retorna el único registro de TriviaConfig o None si no existe.
        """
        config = self.db.query(TriviaConfig).first()
        logger.info("trivia_admin - get_limits - config_id:%s", config.id if config else None)
        return config

    def update_limits(self, data: dict) -> bool:
        """
        Actualiza la configuración global de trivia.
        Crea el registro si no existe (singleton).

        Args:
            data: dict con campos optionales:
                - free_daily_limit: int
                - vip_daily_limit: int
                - vip_exclusive_daily_limit: int
                - streak_timeout_minutes: int

        Returns:
            True si se actualizó correctamente, False si falló
        """
        try:
            config = self.get_limits()
            if not config:
                # Crear nuevo registro singleton
                config = TriviaConfig()
                self.db.add(config)

            # Actualizar campos presentes en data
            if 'free_daily_limit' in data:
                config.free_daily_limit = data['free_daily_limit']
            if 'vip_daily_limit' in data:
                config.vip_daily_limit = data['vip_daily_limit']
            if 'vip_exclusive_daily_limit' in data:
                config.vip_exclusive_daily_limit = data['vip_exclusive_daily_limit']
            if 'streak_timeout_minutes' in data:
                config.streak_timeout_minutes = data['streak_timeout_minutes']

            self.db.commit()
            logger.info("trivia_admin - update_limits - updated successfully")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error("trivia_admin - update_limits - error:%s", str(e))
            return False

    # ==================== PROMOCIONES ====================

    def get_all_promotions(self) -> List[TriviaPromotionConfig]:
        """
        Obtiene todas las configuraciones de promoción trivia.
        Incluye relaciones de tiers para stats rápidos.
        """
        promotions = self.db.query(TriviaPromotionConfig).all()
        logger.info("trivia_admin - get_all_promotions - count:%d", len(promotions))
        return promotions

    def get_promotion_stats(self, promotion_id: int) -> dict:
        """
        Obtiene estadísticas detalladas de una promoción.

        Returns:
            dict con:
                - total_codes: total de códigos generados
                - available_codes: códigos disponibles
                - claimed_codes: códigos reclamados
                - used_codes: códigos usados
                - by_tier: lista de stats por nivel:
                    [{tier_number, discount_percentage, max_codes,
                      codes_generated, available}...]
        """
        # Obtener promoción con tiers
        promotion = self.db.query(TriviaPromotionConfig).filter(
            TriviaPromotionConfig.id == promotion_id
        ).first()

        if not promotion:
            logger.warning("trivia_admin - get_promotion_stats - promotion_id:%d not found", promotion_id)
            return {
                'total_codes': 0,
                'available_codes': 0,
                'claimed_codes': 0,
                'used_codes': 0,
                'by_tier': []
            }

        # Contadores generales
        total_codes = 0
        available_codes = 0
        claimed_codes = 0
        used_codes = 0

        # Stats por tier
        by_tier = []

        for tier in promotion.tiers:
            # Contar códigos por estado
            codes = tier.discount_codes
            tier_total = len(codes)
            tier_available = sum(1 for c in codes if c.status == DiscountCodeStatus.AVAILABLE)
            tier_claimed = sum(1 for c in codes if c.status == DiscountCodeStatus.CLAIMED)
            tier_used = sum(1 for c in codes if c.status == DiscountCodeStatus.USED)

            total_codes += tier_total
            available_codes += tier_available
            claimed_codes += tier_claimed
            used_codes += tier_used

            by_tier.append({
                'tier_number': tier.tier_number,
                'discount_percentage': tier.discount_percentage,
                'max_codes': tier.max_codes,
                'codes_generated': tier_total,
                'available': tier_available
            })

        # Ordenar tiers por número
        by_tier.sort(key=lambda x: x['tier_number'])

        logger.info(
            "trivia_admin - get_promotion_stats - promotion_id:%d, "
            "total:%d, available:%d, claimed:%d, used:%d",
            promotion_id, total_codes, available_codes, claimed_codes, used_codes
        )

        return {
            'total_codes': total_codes,
            'available_codes': available_codes,
            'claimed_codes': claimed_codes,
            'used_codes': used_codes,
            'by_tier': by_tier
        }

    # ==================== CÓDIGOS ====================

    def get_all_codes(
        self,
        promotion_id: int,
        filters: dict = None
    ) -> List[DiscountCode]:
        """
        Obtiene códigos de折扣 de una promoción con filtros opcionales.

        Args:
            promotion_id: ID de la promoción
            filters: dict opcional con:
                - tier_id: int (filtrar por nivel específico)
                - status: DiscountCodeStatus (filtrar por estado)
                - user_id: int (filtrar por usuario)
                - code_prefix: str (buscar por prefijo de código)

        Returns:
            Lista de DiscountCode
        """
        if filters is None:
            filters = {}

        # Query base con join a tiers y promoción
        query = self.db.query(DiscountCode).join(Tier).join(TriviaPromotionConfig)

        # Filtrar por promoción
        query = query.filter(TriviaPromotionConfig.id == promotion_id)

        # Aplicar filtros
        if 'tier_id' in filters and filters['tier_id']:
            query = query.filter(DiscountCode.tier_id == filters['tier_id'])

        if 'status' in filters and filters['status']:
            query = query.filter(DiscountCode.status == filters['status'])

        if 'user_id' in filters and filters['user_id']:
            query = query.filter(DiscountCode.user_id == filters['user_id'])

        if 'code_prefix' in filters and filters['code_prefix']:
            query = query.filter(DiscountCode.code.startswith(filters['code_prefix']))

        codes = query.order_by(DiscountCode.generated_at.desc()).all()

        logger.info(
            "trivia_admin - get_all_codes - promotion_id:%d, filters:%s, count:%d",
            promotion_id, filters, len(codes)
        )

        return codes

    def export_codes_csv(self, promotion_id: int) -> str:
        """
        Exporta códigos de折扣 de una promoción a formato CSV.

        Returns:
            String con contenido CSV (listo para descargar)
        """
        codes = self.get_all_codes(promotion_id)

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            'ID',
            'Código',
            'Tier',
            'Usuario ID',
            'Estado',
            'Generado',
            'Reclamado',
            'Usado',
            'Expira'
        ])

        # Filas de datos
        for code in codes:
            writer.writerow([
                code.id,
                code.code,
                code.tier.tier_number if code.tier else '',
                code.user_id or '',
                code.status.value if code.status else '',
                code.generated_at.isoformat() if code.generated_at else '',
                code.claimed_at.isoformat() if code.claimed_at else '',
                code.used_at.isoformat() if code.used_at else '',
                code.expires_at.isoformat() if code.expires_at else ''
            ])

        csv_content = output.getvalue()
        output.close()

        logger.info(
            "trivia_admin - export_codes_csv - promotion_id:%d, rows:%d",
            promotion_id, len(codes)
        )

        return csv_content

    # ==================== RACHAS Y REGISTROS ====================

    def get_user_streaks(self, promotion_id: int) -> List[UserStreak]:
        """
        Obtiene todas las rachas activas de usuarios para una promoción.

        Args:
            promotion_id: ID de la configuración de promoción

        Returns:
            Lista de UserStreak ordenadas por racha actual (desc)
        """
        streaks = self.db.query(UserStreak).filter(
            UserStreak.promotion_config_id == promotion_id,
            UserStreak.is_active == True
        ).order_by(UserStreak.current_streak.desc()).all()

        logger.info(
            "trivia_admin - get_user_streaks - promotion_id:%d, count:%d",
            promotion_id, len(streaks)
        )

        return streaks

    def get_game_records(
        self,
        user_id: int,
        game_type: str = None
    ) -> List[TriviaGameRecord]:
        """
        Obtiene registros de trivia para un usuario.

        Args:
            user_id: ID del usuario en Telegram
            game_type: str opcional para filtrar por tipo de juego
                       ('trivia_discount', 'trivia_vip')

        Returns:
            Lista de TriviaGameRecord ordenados por fecha (desc)
        """
        query = self.db.query(TriviaGameRecord).filter(
            TriviaGameRecord.user_id == user_id
        )

        if game_type:
            query = query.filter(TriviaGameRecord.game_type == game_type)

        records = query.order_by(TriviaGameRecord.played_at.desc()).all()

        logger.info(
            "trivia_admin - get_game_records - user_id:%d, game_type:%s, count:%d",
            user_id, game_type, len(records)
        )

        return records

    def __del__(self):
        """Cierra la sesión al destruir el servicio"""
        self.close()