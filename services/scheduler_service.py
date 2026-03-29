"""
Servicio Scheduler - Lucien Bot

Gestiona los temporizadores para aprobaciones automáticas y recordatorios.
"""
import asyncio
from datetime import datetime
from typing import Callable, List
from aiogram import Bot
from aiogram.types import ChatJoinRequest
from sqlalchemy.orm import Session
from models.database import SessionLocal
from models.models import ChannelType
from services.channel_service import ChannelService
from services.vip_service import VIPService
from services.user_service import UserService
from utils.lucien_voice import LucienVoice
import logging

logger = logging.getLogger(__name__)


class SchedulerService:
    """Servicio para tareas programadas"""
    
    def __init__(self, bot: Bot, check_interval: int = 30):
        self.bot = bot
        self.check_interval = check_interval  # segundos
        self.running = False
        self._task = None
    
    async def start(self):
        """Inicia el scheduler"""
        if not self.running:
            self.running = True
            self._task = asyncio.create_task(self._run_loop())
            logger.info("Scheduler iniciado")
    
    async def stop(self):
        """Detiene el scheduler"""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Scheduler detenido")
    
    async def _run_loop(self):
        """Loop principal del scheduler"""
        while self.running:
            try:
                await self._process_pending_requests()
                await self._process_expiring_subscriptions()
                await self._process_expired_subscriptions()
            except Exception as e:
                logger.error(f"Error en scheduler: {e}")
            
            await asyncio.sleep(self.check_interval)
    
    async def _process_pending_requests(self):
        """Procesa solicitudes pendientes listas para aprobar"""
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
        """Envía recordatorios de suscripciones por vencer"""
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
        """Procesa suscripciones vencidas"""
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


# Instancia global del scheduler
_scheduler_instance: SchedulerService = None


def get_scheduler(bot: Bot = None) -> SchedulerService:
    """Obtiene o crea la instancia del scheduler"""
    global _scheduler_instance
    if _scheduler_instance is None and bot is not None:
        _scheduler_instance = SchedulerService(bot)
    return _scheduler_instance
