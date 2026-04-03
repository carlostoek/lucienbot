import pytest
import csv
import os
from services.analytics_service import AnalyticsService
from models.models import (
    Subscription, BesitoTransaction, TransactionType, TransactionSource,
    BesitoBalance, User, UserRole
)
from datetime import datetime, timedelta


@pytest.mark.unit
class TestAnalyticsService:
    def test_get_dashboard_stats_keys(self, db_session):
        service = AnalyticsService(db_session)
        stats = service.get_dashboard_stats()
        assert set(stats.keys()) == {"total_users", "active_vip", "total_besitos", "expiring_soon", "new_today"}

    def test_get_dashboard_stats_total_besitos(self, db_session, sample_user, sample_admin):
        service = AnalyticsService(db_session)
        bb1 = BesitoBalance(user_id=sample_user.id, balance=100, total_earned=100, total_spent=0)
        bb2 = BesitoBalance(user_id=sample_admin.id, balance=200, total_earned=200, total_spent=0)
        db_session.add(bb1)
        db_session.add(bb2)
        db_session.commit()
        stats = service.get_dashboard_stats()
        assert stats["total_besitos"] == 300

    def test_get_dashboard_stats_expiring_soon(self, db_session, sample_user, sample_vip_channel, sample_token):
        service = AnalyticsService(db_session)
        sub = Subscription(
            user_id=sample_user.id,
            channel_id=sample_vip_channel.id,
            token_id=sample_token.id,
            end_date=datetime.utcnow() + timedelta(hours=12),
            is_active=True
        )
        db_session.add(sub)
        db_session.commit()
        stats = service.get_dashboard_stats()
        assert stats["expiring_soon"] >= 1

    def test_get_dashboard_stats_new_today(self, db_session):
        service = AnalyticsService(db_session)
        user = User(telegram_id=111222333, username="todayuser", role=UserRole.USER)
        db_session.add(user)
        db_session.commit()
        stats = service.get_dashboard_stats()
        assert stats["new_today"] >= 1

    def test_export_users_csv(self, db_session, sample_user):
        service = AnalyticsService(db_session)
        path = service.export_users_csv()
        assert path is not None
        assert os.path.exists(path)
        with open(path, "r", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert "telegram_id" in reader.fieldnames
            assert any(r["telegram_id"] == str(sample_user.telegram_id) for r in rows)

    def test_export_users_csv_no_users(self, db_session):
        service = AnalyticsService(db_session)
        # Delete all users directly
        db_session.query(User).delete()
        db_session.commit()
        assert service.export_users_csv() is None

    def test_export_activity_csv(self, db_session, sample_user):
        service = AnalyticsService(db_session)
        bb = BesitoBalance(user_id=sample_user.id, balance=10, total_earned=10, total_spent=0)
        db_session.add(bb)
        db_session.commit()
        tx = BesitoTransaction(
            user_id=sample_user.id,
            amount=10,
            type=TransactionType.CREDIT,
            source=TransactionSource.DAILY_GIFT
        )
        db_session.add(tx)
        db_session.commit()
        path = service.export_activity_csv()
        assert path is not None
        with open(path, "r", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert "amount" in reader.fieldnames
            # export_activity_csv writes tx.user_id which is the internal user id
            assert any(r["user_id"] == str(sample_user.id) for r in rows)

    def test_export_activity_csv_no_transactions(self, db_session):
        service = AnalyticsService(db_session)
        db_session.query(BesitoTransaction).delete()
        db_session.commit()
        assert service.export_activity_csv() is None
