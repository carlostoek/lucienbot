"""
Analytics Handlers - Lucien Bot

/admin commands for analytics dashboard and data export.
Only accessible to Custodios (admins).
"""
import io
from datetime import datetime
from aiogram import Router, Bot
from aiogram.types import Message, Document
from aiogram.filters import Command
from aiogram.filters import IsSenderContact
from config.settings import bot_config
from services.analytics_service import AnalyticsService
from utils.lucien_voice import LucienVoice
import logging

logger = logging.getLogger(__name__)
router = Router()


def is_admin(message: Message) -> bool:
    """Check if sender is an admin."""
    return message.from_user.id in bot_config.ADMIN_IDS


@router.message(Command("analytics"), IsSenderContact(is_admin))
async def cmd_analytics(message: Message, bot: Bot):
    """Show analytics dashboard to Custodios."""
    if not is_admin(message):
        return

    try:
        analytics = AnalyticsService()
        metrics = analytics.get_metrics()

        response = f"""🎩 <b>Informe de Diana — {datetime.now().strftime('%Y-%m-%d %H:%M')}</b>

<b>📊 Suscripciones VIP</b>
• Activas: <code>{metrics.total_active_subscriptions}</code>
• Nuevas hoy: <code>{metrics.new_subscriptions_today}</code>
• Por vencer (7 días): <code>{metrics.expiring_this_week}</code>

<b>💋 Gamificación (hoy)</b>
• Besitos enviados: <code>{metrics.total_besitos_sent_today}</code>

<b>🎯 Misiones (últimos 7 días)</b>
• Tasa de completado: <code>{metrics.mission_completion_rate_7d}%</code>

<b>👥 Canales</b>
• Free: <code>{metrics.total_free_channel_members}</code> canales activos
• VIP: <code>{metrics.total_vip_channel_members}</code> canales activos"""

        await message.answer(response, parse_mode="HTML")
        logger.info(f"Analytics dashboard sent to admin {message.from_user.id}")

    except Exception as e:
        logger.error(f"Error generating analytics: {e}")
        await message.answer(
            "🎩 <b>Lucien:</b>\n\n<i>Los registros han decidido guardar silencio por ahora. "
            "Intente de nuevo en un momento.</i>",
            parse_mode="HTML"
        )


@router.message(Command("export"), IsSenderContact(is_admin))
async def cmd_export(message: Message, bot: Bot):
    """Export user activity data as CSV to Custodios."""
    if not is_admin(message):
        return

    try:
        analytics = AnalyticsService()
        csv_buffer = analytics.export_activity_csv()

        # Send as document
        await bot.send_document(
            chat_id=message.from_user.id,
            document=Document(
                document=io.BytesIO(csv_buffer.read().encode("utf-8")),
                filename="lucien_activity_export.csv",
            ),
            caption="🎩 <b>Exportación de actividad — Lucien</b>\n\n"
                    "<i>Diana ha permitido el acceso a estos registros.</i>",
            parse_mode="HTML"
        )
        logger.info(f"Activity export sent to admin {message.from_user.id}")

    except Exception as e:
        logger.error(f"Error exporting analytics: {e}")
        await message.answer(
            "🎩 <b>Lucien:</b>\n\n<i>Los registros han decidido guardar silencio por ahora. "
            "Intente de nuevo en un momento.</i>",
            parse_mode="HTML"
        )
