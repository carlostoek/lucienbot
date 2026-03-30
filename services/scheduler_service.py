"""
Servicio Scheduler - Lucien Bot

Usa APScheduler con SQLAlchemyJobStore para persistir jobs
entre reinicios del bot. Reemplaza el polling loop.
"""
import logging
import os
from datetime import datetime
from aiogram import Bot
from models.database import SessionLocal, engine
from models.models import ChannelType
from services.channel_service import ChannelService
from services.vip_service import VIPService
from services.user_service import UserService
from utils.lucien_voice import LucienVoice

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
    from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    AsyncIOScheduler = None

logger = logging.getLogger(__name__)


def _make_scheduler_config():
    """Build APScheduler config dict from env vars."""
    misfire = int(os.getenv("SCHEDULER_MISFIRE_SECONDS", "300"))
    return {
        "apscheduler.jobstores.default": SQLAlchemyJobStore(
            bind=engine,
            tablename="apscheduler_jobs",
        ),
        "apscheduler.jobstores.default.replace_existing": True,
        "apscheduler.executors.default": {
            "class": "apscheduler.executors.asyncio.AsyncIOExecutor",
        },
        "apscheduler.executors.default.misfire_grace_time": misfire,
    }


class SchedulerService:
    """
    Scheduler usando APScheduler con SQLAlchemyJobStore.

    Jobs survive bot restarts. Processes:
    - Pending channel requests (every 1 minute)
    - Expiring subscription reminders (every 5 minutes)
    - Expired subscriptions (every 1 minute)
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler: AsyncIOScheduler | None = None

        if not APSCHEDULER_AVAILABLE:
            logger.warning("APScheduler not installed. Scheduler disabled.")
            return

        config = _make_scheduler_config()
        self.scheduler = AsyncIOScheduler(config)

        # Register jobs
        self.scheduler.add_job(
            self._process_pending_requests,
            "interval",
            seconds=60,
            id="process_pending_requests",
            replace_existing=True,
            max_instances=1,
        )
        self.scheduler.add_job(
            self._process_expiring_subscriptions,
            "interval",
            seconds=300,  # 5 minutes
            id="process_expiring_subscriptions",
            replace_existing=True,
            max_instances=1,
        )
        self.scheduler.add_job(
            self._process_expired_subscriptions,
            "interval",
            seconds=60,
            id="process_expired_subscriptions",
            replace_existing=True,
            max_instances=1,
        )

        # Log job events
        self.scheduler.add_listener(
            self._job_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )

    def _job_listener(self, event):
        if event.exception:
            logger.error(f"Scheduler job {event.job_id} failed: {event.exception}")
        else:
            logger.debug(f"Scheduler job {event.job_id} completed")

    async def _process_pending_requests(self):
        """Procesa solicitudes pendientes listas para aprobar."""
        db = SessionLocal()
        try:
            channel_service = ChannelService(db)
            ready_requests = channel_service.get_ready_to_approve()

            for request in ready_requests:
                try:
                    channel = request.channel
                    if not channel or not channel.is_active:
                        continue

                    # Aprobar solicitud en Telegram
                    await self.bot.approve_chat_join_request(
                        chat_id=channel.channel_id,
                        user_id=request.user_id
                    )

                    # Actualizar estado en BD
                    request.status = "approved"
                    request.approved_at = datetime.utcnow()
                    db.commit()

                    # Notificar al usuario
                    await self.bot.send_message(
                        chat_id=request.user_id,
                        text=LucienVoice.free_access_approved(channel.channel_name),
                        parse_mode="HTML"
                    )

                    logger.info(f"Solicitud aprobada: user={request.user_id}, channel={channel.channel_id}")

                except Exception as e:
                    logger.error(f"Error aprobando solicitud {request.id}: {e}")
                    db.rollback()

        finally:
            db.close()

    async def _process_expiring_subscriptions(self):
        """Envía recordatorios de suscripciones por vencer."""
        db = SessionLocal()
        try:
            vip_service = VIPService(db)
            expiring = vip_service.get_expiring_subscriptions(hours=24)

            for subscription in expiring:
                try:
                    # Enviar recordatorio
                    await self.bot.send_message(
                        chat_id=subscription.user_id,
                        text=LucienVoice.vip_renewal_reminder(subscription.end_date),
                        parse_mode="HTML"
                    )

                    # Marcar como recordatorio enviado
                    subscription.reminder_sent = True
                    db.commit()

                    logger.info(f"Recordatorio enviado: subscription={subscription.id}")

                except Exception as e:
                    logger.error(f"Error enviando recordatorio {subscription.id}: {e}")
                    db.rollback()

        finally:
            db.close()

    async def _process_expired_subscriptions(self):
        """Procesa suscripciones vencidas."""
        db = SessionLocal()
        try:
            vip_service = VIPService(db)
            expired = vip_service.get_expired_subscriptions()

            for subscription in expired:
                try:
                    channel = subscription.channel
                    if not channel or not channel.is_active:
                        continue

                    # Expulsar usuario del canal VIP
                    await self.bot.ban_chat_member(
                        chat_id=channel.channel_id,
                        user_id=subscription.user_id
                    )

                    # Desbanear para permitir reingreso futuro
                    await self.bot.unban_chat_member(
                        chat_id=channel.channel_id,
                        user_id=subscription.user_id
                    )

                    # Desactivar suscripción
                    subscription.is_active = False
                    db.commit()

                    # Notificar al usuario
                    await self.bot.send_message(
                        chat_id=subscription.user_id,
                        text=LucienVoice.vip_expired(),
                        parse_mode="HTML"
                    )

                    logger.info(f"Suscripción expirada: subscription={subscription.id}")

                except Exception as e:
                    logger.error(f"Error expirando suscripción {subscription.id}: {e}")
                    db.rollback()

        finally:
            db.close()

    async def start(self):
        """Inicia el scheduler (APScheduler)."""
        if self.scheduler and not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler (APScheduler) iniciado")

    async def stop(self):
        """Detiene el scheduler."""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Scheduler (APScheduler) detenido")


_scheduler_instance: SchedulerService = None


def get_scheduler(bot: Bot = None) -> SchedulerService:
    """Obtiene o crea la instancia del scheduler."""
    global _scheduler_instance
    if _scheduler_instance is None and bot is not None:
        _scheduler_instance = SchedulerService(bot)
    return _scheduler_instance
