import pytest
from services.store_service import StoreService
from models.models import StoreProduct, CartItem, Order, OrderStatus, Package


@pytest.mark.unit
class TestStoreService:
    def test_stub(self, db_session):
        pass


@pytest.mark.unit
class TestRaceConditions:
    def test_stub(self, db_session):
        pass
