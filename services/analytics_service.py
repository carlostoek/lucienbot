"""
Analytics Service - Lucien Bot

Provides metrics and data export for Custodios.
Telegram commands only — no web service.
"""
import csv
import io
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional
from models.database import get_db_session
from models.models import Subscription, User, BesitoTransaction, UserMissionProgress, Channel, ChannelType

logger = logging.getLogger(__name__)


@dataclass
class AnalyticsMetrics:
    """Metrics snapshot for analytics dashboard."""
    total_active_subscriptions: int
    new_subscriptions_today: int
    expiring_this_week: int
    total_besitos_sent_today: int
    mission_completion_rate_7d: float  # percentage
    total_free_channel_members: int
    total_vip_channel_members: int


class AnalyticsService:
    """Service for analytics queries."""

    def get_metrics(self) -> AnalyticsMetrics:
        """Return current analytics metrics."""
        with get_db_session() as db:
            now = datetime.utcnow()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_end = today_start + timedelta(days=7)

            # Subscriptions
            total_active = db.query(Subscription).filter(
                Subscription.is_active == True
            ).count()

            new_today = db.query(Subscription).filter(
                Subscription.is_active == True,
                Subscription.start_date >= today_start
            ).count()

            expiring_week = db.query(Subscription).filter(
                Subscription.is_active == True,
                Subscription.end_date <= week_end,
                Subscription.end_date >= now
            ).count()

            # Besitos today (all transactions)
            besitos_today = db.query(BesitoTransaction).filter(
                BesitoTransaction.created_at >= today_start
            ).count()

            # Mission completion rate (last 7 days)
            week_ago = today_start - timedelta(days=7)
            completed = db.query(UserMissionProgress).filter(
                UserMissionProgress.completed_at >= week_ago,
                UserMissionProgress.is_completed == True
            ).count()
            total_started = db.query(UserMissionProgress).filter(
                UserMissionProgress.started_at >= week_ago
            ).count()
            mission_rate = (completed / total_started * 100) if total_started > 0 else 0.0

            # Channel members (use channel_type enum, not .type)
            free_channels = db.query(Channel).filter(
                Channel.channel_type == ChannelType.FREE,
                Channel.is_active == True
            ).all()
            vip_channels = db.query(Channel).filter(
                Channel.channel_type == ChannelType.VIP,
                Channel.is_active == True
            ).all()

            return AnalyticsMetrics(
                total_active_subscriptions=total_active,
                new_subscriptions_today=new_today,
                expiring_this_week=expiring_week,
                total_besitos_sent_today=besitos_today,
                mission_completion_rate_7d=round(mission_rate, 1),
                total_free_channel_members=len(free_channels),
                total_vip_channel_members=len(vip_channels),
            )

    def export_activity_csv(self) -> io.StringIO:
        """Export user activity as CSV for the last 30 days."""
        with get_db_session() as db:
            cutoff = datetime.utcnow() - timedelta(days=30)

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["user_id", "action", "timestamp", "metadata"])

            # Besito transactions
            transactions = db.query(BesitoTransaction).filter(
                BesitoTransaction.created_at >= cutoff
            ).all()
            for tx in transactions:
                writer.writerow([
                    tx.user_id,
                    f"besito_{tx.type.value}",
                    tx.created_at.isoformat(),
                    f"amount={tx.amount}|source={tx.source.value}"
                ])

            # Subscriptions created
            subs = db.query(Subscription).filter(
                Subscription.start_date >= cutoff
            ).all()
            for sub in subs:
                tariff_name = "unknown"
                if sub.token and sub.token.tariff:
                    tariff_name = sub.token.tariff.name
                writer.writerow([
                    sub.user_id,
                    "subscription_created",
                    sub.start_date.isoformat(),
                    f"tariff={tariff_name}"
                ])

            output.seek(0)
            return output
