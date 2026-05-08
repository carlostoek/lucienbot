"""
Tests unitarios para modelos del sistema trivia discount.
"""
import pytest
from datetime import datetime, timedelta, timezone

from models.models import (
    TriviaPromotionConfig, Tier, DiscountCode, UserStreak,
    DiscountCodeStatus, GameResult, QuestionSet, Question,
    TriviaConfig
)
from services.trivia_discount_service import TriviaDiscountService


@pytest.mark.unit
class TestTriviaModels:
    """Tests para comportamiento de modelos trivia"""

    def test_trivia_promotion_config_is_new_model(self, db_session):
        """Verify TriviaPromotionConfig is separate from Promotion"""
        # Verificar que TriviaPromotionConfig es un modelo nuevo (no Promotion)
        promo = TriviaPromotionConfig(
            name="Test Trivia Promo",
            description="Trivia discount promotion",
            is_active=True,
            duration_days=7,
            auto_reset=True
        )
        db_session.add(promo)
        db_session.commit()
        db_session.refresh(promo)

        assert promo.id is not None
        assert promo.name == "Test Trivia Promo"
        assert promo.description == "Trivia discount promotion"
        assert promo.is_active is True
        assert promo.duration_days == 7
        assert promo.auto_reset is True

        # Verificar que tiene relación con tiers
        assert hasattr(promo, 'tiers')
        assert hasattr(promo, 'question_set_id')  # Relación con QuestionSet

        # Verificar que NO es Promotion
        assert not hasattr(promo, 'price_mxn')  # Promotion tiene price_mxn
        assert not hasattr(promo, 'package_id')  # Promotion tiene package_id

    def test_tier_independent_pool(self, db_session):
        """Verify Tier.codes_generated tracks independently"""
        service = TriviaDiscountService(db_session)

        # Crear promoción con múltiples tiers
        promotion = TriviaPromotionConfig(
            name="Multi-tier Promo",
            is_active=True,
            duration_days=7
        )
        db_session.add(promotion)
        db_session.commit()
        db_session.refresh(promotion)

        tier1 = Tier(
            promotion_config_id=promotion.id,
            tier_number=1,
            streak_threshold=3,
            discount_percentage=10,
            max_codes=5,
            codes_generated=0
        )
        tier2 = Tier(
            promotion_config_id=promotion.id,
            tier_number=2,
            streak_threshold=5,
            discount_percentage=20,
            max_codes=5,
            codes_generated=0
        )
        tier3 = Tier(
            promotion_config_id=promotion.id,
            tier_number=3,
            streak_threshold=7,
            discount_percentage=30,
            max_codes=5,
            codes_generated=0
        )
        db_session.add_all([tier1, tier2, tier3])
        db_session.commit()

        # Generar diferentes cantidades de códigos en cada tier
        for i in range(3):
            service.generate_code(tier1.id, user_id=1000 + i)
        for i in range(4):
            service.generate_code(tier2.id, user_id=2000 + i)
        for i in range(2):
            service.generate_code(tier3.id, user_id=3000 + i)

        # Refrescar tiers
        db_session.refresh(tier1)
        db_session.refresh(tier2)
        db_session.refresh(tier3)

        # Verificar contadores independientes
        assert tier1.codes_generated == 3
        assert tier2.codes_generated == 4
        assert tier3.codes_generated == 2

        # Verificar disponibilidad independiente
        assert (tier1.max_codes - tier1.codes_generated) == 2
        assert (tier2.max_codes - tier2.codes_generated) == 1
        assert (tier3.max_codes - tier3.codes_generated) == 3

    def test_discount_code_status_enum(self, db_session):
        """Verify all status values exist"""
        # AVAILABLE
        assert DiscountCodeStatus.AVAILABLE.value == "available"
        # CLAIMED
        assert DiscountCodeStatus.CLAIMED.value == "claimed"
        # USED
        assert DiscountCodeStatus.USED.value == "used"
        # CANCELLED
        assert DiscountCodeStatus.CANCELLED.value == "cancelled"
        # EXPIRED
        assert DiscountCodeStatus.EXPIRED.value == "expired"

        # Verificar que son strings para comparar con DB
        assert isinstance(DiscountCodeStatus.AVAILABLE.value, str)
        assert isinstance(DiscountCodeStatus.CLAIMED.value, str)
        assert isinstance(DiscountCodeStatus.USED.value, str)
        assert isinstance(DiscountCodeStatus.CANCELLED.value, str)
        assert isinstance(DiscountCodeStatus.EXPIRED.value, str)

    def test_user_streak_tracking(self, db_session):
        """UserStreak tracks current_streak correctly"""
        service = TriviaDiscountService(db_session)

        # Crear promoción
        promotion = TriviaPromotionConfig(
            name="Streak Test Promo",
            is_active=True,
            duration_days=7
        )
        db_session.add(promotion)
        db_session.commit()
        db_session.refresh(promotion)

        user_id = 99999

        # Crear streak inicial
        streak = service.create_streak(user_id=user_id, promotion_id=promotion.id)
        assert streak.current_streak == 0
        assert streak.is_active is True
        assert streak.active_tier_id is None

        # Incrementar streak varias veces
        for expected in range(1, 6):
            streak, _ = service.increment_streak(user_id=user_id)
            assert streak.current_streak == expected

        # Verificar que el streak está activo
        db_session.refresh(streak)
        assert streak.is_active is True
        assert streak.current_streak == 5

        # Invalidar streak
        service.invalidate_streak(user_id=user_id)
        db_session.refresh(streak)
        assert streak.is_active is False
        assert streak.current_streak == 5  # Valor se mantiene pero is_active=False

    def test_game_result_enum(self, db_session):
        """Verify GameResult enum values"""
        # WON
        assert GameResult.WON.value == "won"
        # LOST
        assert GameResult.LOST.value == "lost"
        # ABANDONED
        assert GameResult.ABANDONED.value == "abandoned"
        # EXPIRED
        assert GameResult.EXPIRED.value == "expired"

        assert isinstance(GameResult.WON.value, str)
        assert isinstance(GameResult.LOST.value, str)

    def test_tier_model_attributes(self, db_session):
        """Verify Tier model has correct attributes"""
        promotion = TriviaPromotionConfig(
            name="Test Promo",
            is_active=True,
            duration_days=7
        )
        db_session.add(promotion)
        db_session.commit()
        db_session.refresh(promotion)

        tier = Tier(
            promotion_config_id=promotion.id,
            tier_number=1,
            streak_threshold=5,
            discount_percentage=15,
            max_codes=20,
            codes_generated=0
        )
        db_session.add(tier)
        db_session.commit()
        db_session.refresh(tier)

        assert tier.tier_number == 1
        assert tier.streak_threshold == 5
        assert tier.discount_percentage == 15
        assert tier.max_codes == 20
        assert tier.codes_generated == 0

        # Verificar relación con discount_codes
        assert hasattr(tier, 'discount_codes')

    def test_discount_code_attributes(self, db_session):
        """Verify DiscountCode model has correct attributes"""
        promotion = TriviaPromotionConfig(
            name="Test Promo",
            is_active=True,
            duration_days=7
        )
        db_session.add(promotion)
        db_session.commit()
        db_session.refresh(promotion)

        tier = Tier(
            promotion_config_id=promotion.id,
            tier_number=1,
            streak_threshold=3,
            discount_percentage=10,
            max_codes=10,
            codes_generated=0
        )
        db_session.add(tier)
        db_session.commit()
        db_session.refresh(tier)

        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        code = DiscountCode(
            code="TRI-TEST123",
            tier_id=tier.id,
            user_id=12345,
            status=DiscountCodeStatus.AVAILABLE,
            expires_at=expires_at
        )
        db_session.add(code)
        db_session.commit()
        db_session.refresh(code)

        assert code.code == "TRI-TEST123"
        assert code.tier_id == tier.id
        assert code.user_id == 12345
        assert code.status == DiscountCodeStatus.AVAILABLE
        # Verificar fechas
        assert code.generated_at is not None
        assert code.claimed_at is None
        assert code.used_at is None
        # expires_at puede o no tener timezone dependiendo de la DB
        assert code.expires_at is not None
        # Comparar que expires_at es futuro (sin comparar timezone)
        assert code.expires_at > datetime.now(timezone.utc).replace(tzinfo=None)
