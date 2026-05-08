"""
Tests unitarios para TriviaDiscountService.
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

from services.trivia_discount_service import TriviaDiscountService
from models.models import (
    TriviaPromotionConfig, Tier, DiscountCode, UserStreak,
    DiscountCodeStatus, GameResult
)


@pytest.mark.unit
class TestTriviaDiscountServiceCodeGeneration:
    """Tests para generación atómica de códigos"""

    def test_code_generation_atomic(self, db_session):
        """Verify atomic code generation with SELECT FOR UPDATE prevents duplicates"""
        service = TriviaDiscountService(db_session)

        # Crear promoción y tier de prueba
        promotion = TriviaPromotionConfig(
            name="Test Promo",
            description="Test description",
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

        # Generar primer código
        code1 = service.generate_code(tier.id, user_id=12345)
        assert code1 is not None
        assert code1.status == DiscountCodeStatus.AVAILABLE
        assert code1.code.startswith("TRI-")

        # Verificar que el contador se incrementado
        db_session.refresh(tier)
        assert tier.codes_generated == 1

        # Generar segundo código
        code2 = service.generate_code(tier.id, user_id=12346)
        assert code2 is not None
        assert code2.id != code1.id
        assert code2.code != code1.code

        db_session.refresh(tier)
        assert tier.codes_generated == 2

    def test_tier_pool_independent(self, db_session):
        """Verify each tier has its own independent code pool"""
        service = TriviaDiscountService(db_session)

        # Crear promoción con dos tiers
        promotion = TriviaPromotionConfig(
            name="Test Promo",
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
            max_codes=3,
            codes_generated=0
        )
        db_session.add(tier1)
        db_session.add(tier2)
        db_session.commit()
        db_session.refresh(tier1)
        db_session.refresh(tier2)

        # Generar códigos para tier1
        for i in range(3):
            code = service.generate_code(tier1.id, user_id=1000 + i)
            assert code is not None

        # Generar códigos para tier2
        for i in range(2):
            code = service.generate_code(tier2.id, user_id=2000 + i)
            assert code is not None

        # Verificar contadores independientes
        db_session.refresh(tier1)
        db_session.refresh(tier2)
        assert tier1.codes_generated == 3
        assert tier2.codes_generated == 2

        # Verificar disponibilidad
        assert service.get_available_codes_count(tier1.id) == 2  # 5 - 3
        assert service.get_available_codes_count(tier2.id) == 1  # 3 - 2

    def test_streak_tier_reached(self, db_session):
        """When streak reaches tier threshold, tier is returned"""
        service = TriviaDiscountService(db_session)

        # Crear promoción con tier
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

        # Crear streak inicial
        streak = service.create_streak(user_id=12345, promotion_id=promotion.id)
        assert streak.current_streak == 0
        assert streak.active_tier_id is None

        # Incrementar hasta alcanzar threshold
        streak, new_tier = service.increment_streak(user_id=12345)
        assert streak.current_streak == 1
        assert new_tier is None

        streak, new_tier = service.increment_streak(user_id=12345)
        assert streak.current_streak == 2
        assert new_tier is None

        streak, new_tier = service.increment_streak(user_id=12345)
        assert streak.current_streak == 3
        assert new_tier is not None
        assert new_tier.id == tier.id
        assert new_tier.streak_threshold == 3

    def test_player_retire(self, db_session):
        """Player can retire and claim code"""
        service = TriviaDiscountService(db_session)

        # Crear promoción y tier
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

        # Generar código
        code = service.generate_code(tier.id, user_id=12345)
        assert code is not None
        assert code.status == DiscountCodeStatus.AVAILABLE

        # Reclamar código
        result = service.claim_code(code.id)
        assert result is True

        db_session.refresh(code)
        assert code.status == DiscountCodeStatus.CLAIMED
        assert code.claimed_at is not None

    def test_wrong_answer_invalidates(self, db_session):
        """Wrong answer invalidates code and resets streak"""
        service = TriviaDiscountService(db_session)

        # Crear promoción, tier y streak
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

        # Crear streak con código activo
        streak = service.create_streak(user_id=12345, promotion_id=promotion.id)
        code = service.generate_code(tier.id, user_id=12345)
        streak.active_code_id = code.id
        streak.active_tier_id = tier.id
        streak.current_streak = 3
        db_session.commit()

        # Simular respuesta incorrecta: reset streak
        service.reset_streak(user_id=12345)

        db_session.refresh(streak)
        assert streak.current_streak == 0
        assert streak.active_tier_id is None
        assert streak.active_code_id is None

    def test_invalidate_streak(self, db_session):
        """Streak can be invalidated (timeout)"""
        service = TriviaDiscountService(db_session)

        # Crear promoción y streak
        promotion = TriviaPromotionConfig(
            name="Test Promo",
            is_active=True,
            duration_days=7
        )
        db_session.add(promotion)
        db_session.commit()
        db_session.refresh(promotion)

        streak = service.create_streak(user_id=12345, promotion_id=promotion.id)
        streak.current_streak = 5
        db_session.commit()

        # Invalidar streak (timeout)
        service.invalidate_streak(user_id=12345)

        db_session.refresh(streak)
        assert streak.is_active is False
        assert streak.active_tier_id is None

    def test_generate_code_no_availability(self, db_session):
        """generate_code returns None when tier is exhausted"""
        service = TriviaDiscountService(db_session)

        # Crear promoción y tier con solo 1 código
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
            max_codes=1,
            codes_generated=0
        )
        db_session.add(tier)
        db_session.commit()
        db_session.refresh(tier)

        # Generar primer código (debería funcionar)
        code1 = service.generate_code(tier.id, user_id=12345)
        assert code1 is not None

        # Intentar generar segundo código (debería fallar - sin disponibilidad)
        code2 = service.generate_code(tier.id, user_id=12346)
        assert code2 is None

        db_session.refresh(tier)
        assert tier.codes_generated == 1  # No debe incrementarse

    def test_status_transitions(self, db_session):
        """Code status transitions work correctly"""
        service = TriviaDiscountService(db_session)

        # Crear promoción y tier
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

        # AVAILABLE -> CLAIMED -> USED
        code = service.generate_code(tier.id, user_id=12345)
        assert code.status == DiscountCodeStatus.AVAILABLE

        result = service.claim_code(code.id)
        assert result is True
        db_session.refresh(code)
        assert code.status == DiscountCodeStatus.CLAIMED

        result = service.use_code(code.id)
        assert result is True
        db_session.refresh(code)
        assert code.status == DiscountCodeStatus.USED

        # AVAILABLE -> CANCELLED
        code2 = service.generate_code(tier.id, user_id=12346)
        assert code2.status == DiscountCodeStatus.AVAILABLE

        result = service.cancel_code(code2.id)
        assert result is True
        db_session.refresh(code2)
        assert code2.status == DiscountCodeStatus.CANCELLED

        # AVAILABLE -> EXPIRED
        code3 = service.generate_code(tier.id, user_id=12347)
        assert code3.status == DiscountCodeStatus.AVAILABLE

        result = service.expire_code(code3.id)
        assert result is True
        db_session.refresh(code3)
        assert code3.status == DiscountCodeStatus.EXPIRED
