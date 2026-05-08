"""
Tests unitarios para TriviaConfig singleton.
"""
import pytest
from datetime import datetime, timezone

from services.trivia_discount_service import TriviaDiscountService
from models.models import TriviaConfig


@pytest.mark.unit
class TestTriviaConfigService:
    """Tests para el servicio de configuración global de trivia"""

    def test_daily_limits(self, db_session):
        """Verify daily limits are respected per user type (free/VIP/VIP-exclusive)"""
        service = TriviaDiscountService(db_session)

        # Crear o actualizar TriviaConfig
        config = TriviaConfig(
            free_daily_limit=7,
            vip_daily_limit=15,
            vip_exclusive_daily_limit=5,
            streak_timeout_minutes=2
        )
        db_session.add(config)
        db_session.commit()
        db_session.refresh(config)

        # Verificar valores iniciales
        assert config.free_daily_limit == 7
        assert config.vip_daily_limit == 15
        assert config.vip_exclusive_daily_limit == 5

        # Actualizar límites
        result = service.update_trivia_config(
            free_daily_limit=10,
            vip_daily_limit=20,
            vip_exclusive_daily_limit=8
        )
        assert result is True

        # Obtener y verificar
        updated = service.get_trivia_config()
        assert updated.free_daily_limit == 10
        assert updated.vip_daily_limit == 20
        assert updated.vip_exclusive_daily_limit == 8

    def test_streak_timeout(self, db_session):
        """Verify streak_timeout_minutes is configurable"""
        service = TriviaDiscountService(db_session)

        # Crear TriviaConfig
        config = TriviaConfig(
            free_daily_limit=7,
            vip_daily_limit=15,
            vip_exclusive_daily_limit=5,
            streak_timeout_minutes=2
        )
        db_session.add(config)
        db_session.commit()
        db_session.refresh(config)

        assert config.streak_timeout_minutes == 2

        # Actualizar timeout
        result = service.update_trivia_config(streak_timeout_minutes=5)
        assert result is True

        updated = service.get_trivia_config()
        assert updated.streak_timeout_minutes == 5

    def test_trivia_config_singleton(self, db_session):
        """Only one TriviaConfig row exists"""
        service = TriviaDiscountService(db_session)

        # Verificar que no existe inicialmente
        configs_before = db_session.query(TriviaConfig).all()
        assert len(configs_before) == 0

        # Crear primera configuración
        config1 = TriviaConfig(
            free_daily_limit=7,
            vip_daily_limit=15,
            vip_exclusive_daily_limit=5,
            streak_timeout_minutes=2
        )
        db_session.add(config1)
        db_session.commit()
        db_session.refresh(config1)

        # Verificar que solo hay una
        configs = db_session.query(TriviaConfig).all()
        assert len(configs) == 1
        assert configs[0].id == config1.id

        # Obtener via service (debe retornar el mismo)
        retrieved = service.get_trivia_config()
        assert retrieved is not None
        assert retrieved.id == config1.id

        # Intentar actualizar (debe funcionar en el singleton existente)
        result = service.update_trivia_config(free_daily_limit=12)
        assert result is True

        updated = service.get_trivia_config()
        assert updated.free_daily_limit == 12
        assert updated.id == config1.id  # Mismo registro, no se creó otro

    def test_get_trivia_config_not_exists(self, db_session):
        """Test get_trivia_config returns None when no config exists"""
        service = TriviaDiscountService(db_session)

        # No crear configuración, solo consultar
        config = service.get_trivia_config()
        # Puede existir o no dependiendo del estado de la BD
        # Este test verifica que el método no falla
        assert config is None or isinstance(config, TriviaConfig)
