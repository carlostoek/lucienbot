import pytest
from services.daily_gift_service import DailyGiftService
from models.models import DailyGiftConfig, DailyGiftClaim


@pytest.mark.unit
class TestDailyGiftService:
    def test_stub(self, db_session):
        pass
