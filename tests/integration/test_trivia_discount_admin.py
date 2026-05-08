"""
Tests de integración para el flujo admin del sistema trivia discount.

Verifica:
- Creación de promociones con múltiples tiers
- Creación de promociones con fechas fijas y duración relativa
- Visualización de estadísticas
- Pausar/reanudar promociones
- Exportación de códigos a CSV

参考: services/trivia_admin_service.py, services/trivia_discount_service.py
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, AsyncMock

from services.trivia_admin_service import TriviaAdminService
from services.trivia_discount_service import TriviaDiscountService
from services.game_service import GameService
from models.models import (
    TriviaPromotionConfig,
    TriviaConfig,
    Tier,
    QuestionSet,
    Question,
    DiscountCode,
    DiscountCodeStatus,
    UserStreak,
    User,
    UserRole
)


@pytest.fixture
def trivia_config(db_session):
    """Crea configuración global de trivia (singleton)."""
    config = TriviaConfig(
        free_daily_limit=5,
        vip_daily_limit=10,
        vip_exclusive_daily_limit=3,
        streak_timeout_minutes=2
    )
    db_session.add(config)
    db_session.commit()
    db_session.refresh(config)
    return config


@pytest.fixture
def question_set(db_session):
    """Crea un set de preguntas de prueba."""
    qset = QuestionSet(
        name="Test Question Set",
        description="Preguntas de prueba",
        is_active=True
    )
    db_session.add(qset)
    db_session.commit()

    # Agregar preguntas
    questions = [
        Question(
            question_set_id=qset.id,
            question_text="¿Cuál es la capital de Francia?",
            option_a="Londres",
            option_b="París",
            option_c="Berlín",
            option_d="Madrid",
            correct_option="B",
            difficulty="easy"
        ),
        Question(
            question_set_id=qset.id,
            question_text="¿2 + 2?",
            option_a="3",
            option_b="4",
            option_c="5",
            option_d="6",
            correct_option="B",
            difficulty="easy"
        ),
        Question(
            question_set_id=qset.id,
            question_text="¿Color del cielo?",
            option_a="Rojo",
            option_b="Verde",
            option_c="Azul",
            option_d="Amarillo",
            correct_option="C",
            difficulty="easy"
        ),
    ]
    for q in questions:
        db_session.add(q)
    db_session.commit()
    db_session.refresh(qset)
    return qset


@pytest.fixture
def admin_user(db_session):
    """Crea usuario admin de prueba."""
    user = User(
        telegram_id=999999999,
        username="adminuser",
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def player_user(db_session):
    """Crea usuario player de prueba."""
    user = User(
        telegram_id=111222333,
        username="playeruser",
        first_name="Player",
        last_name="User",
        role=UserRole.USER
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def promotion_with_tiers(db_session, question_set):
    """Crea promoción con 3 tiers de prueba."""
    # Crear promoción
    promotion = TriviaPromotionConfig(
        name="Test Promo",
        description="Promo de prueba",
        is_active=True,
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=7),
        duration_days=7,
        auto_reset=True,
        question_set_id=question_set.id
    )
    db_session.add(promotion)
    db_session.commit()
    db_session.refresh(promotion)

    # Crear 3 tiers
    tiers_data = [
        {'tier_number': 1, 'streak_threshold': 3, 'discount_percentage': 10, 'max_codes': 5},
        {'tier_number': 2, 'streak_threshold': 5, 'discount_percentage': 20, 'max_codes': 3},
        {'tier_number': 3, 'streak_threshold': 7, 'discount_percentage': 30, 'max_codes': 2},
    ]
    created_tiers = []
    for td in tiers_data:
        tier = Tier(
            promotion_config_id=promotion.id,
            tier_number=td['tier_number'],
            streak_threshold=td['streak_threshold'],
            discount_percentage=td['discount_percentage'],
            max_codes=td['max_codes'],
            codes_generated=0
        )
        db_session.add(tier)
        created_tiers.append(tier)
    db_session.commit()

    return promotion, created_tiers


@pytest.mark.integration
class TestTriviaDiscountAdminCreation:
    """Tests para creación de promociones trivia."""

    def test_admin_create_promotion_with_tiers(self, db_session, question_set):
        """
        Admin puede crear promoción con 3 tiers, cada uno con diferente cantidad de códigos.

        Verifica que:
        - La promoción se crea correctamente
        - Los 3 tiers se crean con los parámetros especificados
        - Los códigos generados comienzan en 0
        """
        admin_service = TriviaAdminService(db_session)
        discount_service = TriviaDiscountService(db_session)

        # Crear promoción
        config = discount_service.create_promotion_config({
            'name': 'Promo Admin Test',
            'description': 'Promo de prueba con 3 tiers',
            'is_active': True,
            'question_set_id': question_set.id
        })
        assert config is not None
        assert config.id is not None

        # Crear tiers manualmente (como lo haría el admin handler)
        tier1 = Tier(
            promotion_config_id=config.id,
            tier_number=1,
            streak_threshold=3,
            discount_percentage=10,
            max_codes=10,
            codes_generated=0
        )
        tier2 = Tier(
            promotion_config_id=config.id,
            tier_number=2,
            streak_threshold=5,
            discount_percentage=20,
            max_codes=5,
            codes_generated=0
        )
        tier3 = Tier(
            promotion_config_id=config.id,
            tier_number=3,
            streak_threshold=7,
            discount_percentage=30,
            max_codes=2,
            codes_generated=0
        )
        db_session.add_all([tier1, tier2, tier3])
        db_session.commit()

        # Verificar que los tiers se crearon
        tiers = discount_service.get_tiers_by_promotion(config.id)
        assert len(tiers) == 3

        # Verificar parámetros de cada tier
        tiers_sorted = sorted(tiers, key=lambda t: t.tier_number)
        assert tiers_sorted[0].max_codes == 10
        assert tiers_sorted[1].max_codes == 5
        assert tiers_sorted[2].max_codes == 2

        # Verificar códigos disponibles
        assert discount_service.get_available_codes_count(tiers_sorted[0].id) == 10
        assert discount_service.get_available_codes_count(tiers_sorted[1].id) == 5
        assert discount_service.get_available_codes_count(tiers_sorted[2].id) == 2

        print(f"✓ Promo creada con 3 tiers: codes disponibles {10}, {5}, {2}")

    def test_admin_create_promotion_fixed_dates(self, db_session, question_set):
        """
        Admin crea promoción con fechas fijas (start_date y end_date).

        Verifica que:
        - start_date y end_date se guardan correctamente
        - duration_days se ignora cuando hay fechas fijas
        """
        discount_service = TriviaDiscountService(db_session)

        start = datetime.now(timezone.utc) + timedelta(days=1)
        end = datetime.now(timezone.utc) + timedelta(days=14)

        config = discount_service.create_promotion_config({
            'name': 'Promo Fechas Fijas',
            'description': 'Promo con fechas fijas',
            'is_active': True,
            'start_date': start,
            'end_date': end,
            'duration_days': 30,  # debe ignorarse
            'question_set_id': question_set.id
        })

        assert config is not None
        # Compare dates only to avoid timezone comparison issues
        assert config.start_date.date() == start.date()
        assert config.end_date.date() == end.date()
        assert config.duration_days == 30  # se guarda pero no se usa si hay fechas

        print(f"✓ Promo con fechas fijas: {start.date()} a {end.date()}")

    def test_admin_create_promotion_relative_duration(self, db_session, question_set):
        """
        Admin crea promoción con duración relativa (sin fechas fijas).

        Verifica que:
        - start_date y end_date son None
        - duration_days define la duración
        - auto_reset está habilitado
        """
        discount_service = TriviaDiscountService(db_session)

        config = discount_service.create_promotion_config({
            'name': 'Promo Duracion Relativa',
            'description': 'Promo sin fechas fijas',
            'is_active': True,
            'start_date': None,
            'end_date': None,
            'duration_days': 5,
            'auto_reset': True,
            'question_set_id': question_set.id
        })

        assert config is not None
        assert config.start_date is None
        assert config.end_date is None
        assert config.duration_days == 5
        assert config.auto_reset is True

        print(f"✓ Promo con duracion relativa: {config.duration_days} dias")


@pytest.mark.integration
class TestTriviaDiscountAdminStats:
    """Tests para estadísticas y gestión de promociones."""

    def test_admin_view_promotion_stats(self, db_session, promotion_with_tiers):
        """
        Admin puede ver estadísticas mostrando códigos por tier.

        Verifica que:
        - Stats retornan total de códigos
        - Stats muestran códigos disponibles por tier
        - Stats incluyen distribución por tier
        """
        admin_service = TriviaAdminService(db_session)
        promotion, tiers = promotion_with_tiers

        stats = admin_service.get_promotion_stats(promotion.id)

        assert stats['total_codes'] == 0  # aún no hay códigos generados
        assert stats['available_codes'] == 0
        assert stats['by_tier'] is not None
        assert len(stats['by_tier']) == 3

        # Verificar estructura de by_tier
        tier_stats = sorted(stats['by_tier'], key=lambda x: x['tier_number'])
        assert tier_stats[0]['max_codes'] == 5
        assert tier_stats[1]['max_codes'] == 3
        assert tier_stats[2]['max_codes'] == 2

        # Generar algunos códigos para verificar stats actualizadas
        discount_service = TriviaDiscountService(db_session)
        for _ in range(3):
            discount_service.generate_code(tiers[0].id, 111222333)

        stats_updated = admin_service.get_promotion_stats(promotion.id)
        assert stats_updated['total_codes'] == 3
        assert stats_updated['available_codes'] == 3

        print(f"✓ Stats vistas: total={stats_updated['total_codes']}, disponibles={stats_updated['available_codes']}")
        for ts in stats_updated['by_tier']:
            print(f"  Tier {ts['tier_number']}: {ts['codes_generated']}/{ts['max_codes']} generados")

    def test_admin_pause_resume_promotion(self, db_session, question_set):
        """
        Admin puede pausar y reanudar una promoción.

        Verifica que:
        - pause_promotion() desactiva is_active
        - resume_promotion() reactiva is_active
        - get_promotion_config() refleja el cambio
        """
        discount_service = TriviaDiscountService(db_session)

        # Crear promoción activa
        config = discount_service.create_promotion_config({
            'name': 'Promo Pause Test',
            'description': 'Test pause/resume',
            'is_active': True,
            'question_set_id': question_set.id
        })
        assert config.is_active is True

        # Pausar
        result = discount_service.pause_promotion(config.id)
        assert result is True

        db_session.refresh(config)
        assert config.is_active is False

        # Verificar que no aparece como activa
        active_promos = discount_service.get_active_promotions()
        assert not any(p.id == config.id for p in active_promos)

        # Reanudar
        result = discount_service.resume_promotion(config.id)
        assert result is True

        db_session.refresh(config)
        assert config.is_active is True

        # Verificar que aparece como activa
        active_promos = discount_service.get_active_promotions()
        assert any(p.id == config.id for p in active_promos)

        print(f"✓ Pause/Resume funciona correctamente")

    def test_admin_export_codes_csv(self, db_session, promotion_with_tiers, player_user):
        """
        Exportación produce CSV válido con estructura correcta.

        Verifica que:
        - CSV contiene header correcto
        - Filas contienen datos de códigos
        - Formato CSV es parseable
        """
        admin_service = TriviaAdminService(db_session)
        discount_service = TriviaDiscountService(db_session)
        promotion, tiers = promotion_with_tiers

        # Generar algunos códigos
        code1 = discount_service.generate_code(tiers[0].id, player_user.telegram_id)
        code2 = discount_service.generate_code(tiers[1].id, player_user.telegram_id)

        # Exportar
        csv_content = admin_service.export_codes_csv(promotion.id)

        # Verificar estructura del CSV
        lines = csv_content.strip().split('\n')
        assert len(lines) >= 2  # header + al menos 2 códigos

        # Verificar header
        header = lines[0]
        assert 'Código' in header
        assert 'Tier' in header
        assert 'Estado' in header

        # Verificar que hay datos
        data_lines = lines[1:]
        assert len(data_lines) == 2

        # Verificar parseo básico (cada línea tiene el número de campos correcto)
        import csv
        import io
        reader = csv.reader(io.StringIO(csv_content))
        rows = list(reader)
        assert len(rows) >= 2  # header + datos

        print(f"✓ CSV exportado: {len(rows)-1} códigos, header: {rows[0][:3]}")

        # Limpiar
        discount_service.cancel_code(code1.id)
        discount_service.cancel_code(code2.id)


@pytest.mark.integration
class TestTriviaDiscountAdminLimits:
    """Tests para configuración de límites."""

    def test_update_and_get_limits(self, db_session, trivia_config):
        """Admin puede actualizar y obtener límites globales."""
        admin_service = TriviaAdminService(db_session)

        # Actualizar límites
        result = admin_service.update_limits({
            'free_daily_limit': 10,
            'vip_daily_limit': 20,
            'streak_timeout_minutes': 5
        })
        assert result is True

        # Obtener y verificar
        limits = admin_service.get_limits()
        assert limits.free_daily_limit == 10
        assert limits.vip_daily_limit == 20
        assert limits.streak_timeout_minutes == 5

        print(f"✓ Límites actualizados: free={limits.free_daily_limit}, vip={limits.vip_daily_limit}")