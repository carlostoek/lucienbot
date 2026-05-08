"""
Error Handler Middleware - Lucien Bot

Captura excepciones no manejadas en todos los handlers,
registra contexto completo, notifica a admins, y responde
al usuario con mensaje genérico en la voz de Lucien.
"""
import traceback
import sys
from typing import Any
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import TelegramObject, Update
from aiogram.enums import UpdateType
from config.settings import bot_config
import logging

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseMiddleware):
    """
    Middleware global de manejo de errores.

    Captura cualquier excepción no manejada en handlers, callback queries,
    messages, y otros eventos de Telegram. previene que el bot crashee
    y proporciona logging detallado para debugging.

    No maneja:
    - Rate limit errors (ya manejados por ThrottlingMiddleware)
    - Telegram API errors transitorios ( retries automáticos de aiogram)
    """

    def __init__(self, notify_admins: bool = True):
        self.notify_admins = notify_admins
        self._admins_notified_recently: set[int] = set()
        super().__init__()

    async def __call__(self, handler, event: TelegramObject, data: dict) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            await self._handle_exception(e, event, data)
            return None

    async def _handle_exception(
        self,
        exception: Exception,
        event: TelegramObject,
        data: dict
    ) -> None:
        """Procesa la excepción, loggea, notifica admins, responde al usuario."""

        # Extraer contexto del evento
        context = await self._extract_context(event, data)

        # Loggear con stack trace completo
        await self._log_exception(exception, context)

        # Responder al usuario con mensaje genérico
        await self._notify_user(event, context, data)

        # Notificar admins si es error crítico
        if self._is_critical_error(exception):
            await self._notify_admins(exception, context, data)

    async def _extract_context(self, event: TelegramObject, data: dict) -> dict:
        """Extrae información de contexto del evento para logging."""
        context = {
            "event_type": type(event).__name__,
            "update_type": None,
            "user_id": None,
            "chat_id": None,
            "message_id": None,
            "handler": None,
            "fsm_state": None,
        }

        # Extraer tipo de update
        if isinstance(event, Update):
            context["update_type"] = event.event_type if hasattr(event, 'event_type') else str(event)

        # Intentar extraer user y chat de diferentes fuentes
        user = data.get("event_from_user")
        if user:
            context["user_id"] = user.id

        # Para messages y callbacks
        if hasattr(event, "message") and event.message:
            msg = event.message
            context["chat_id"] = msg.chat.id if msg.chat else None
            context["message_id"] = msg.message_id
        elif hasattr(event, "from_user") and event.from_user:
            context["chat_id"] = event.from_user.id
            if hasattr(event, "message_id"):
                context["message_id"] = event.message_id

        # FSM state actual
        state = data.get("state")
        if state:
            try:
                fsm_state = await state.get_state() if hasattr(state, 'get_state') else None
                context["fsm_state"] = fsm_state
            except Exception:
                context["fsm_state"] = "unavailable"

        # Handler que estaba procesando
        handler = data.get("handler")
        if handler:
            context["handler"] = f"{handler.callback.__module__}.{handler.callback.__name__}"

        return context

    async def _log_exception(self, exception: Exception, context: dict) -> None:
        """Loggea la excepción con contexto completo."""

        # Formatear detalles del contexto
        context_str = " | ".join(
            f"{k}={v}" for k, v in context.items() if v is not None
        )

        # Log principal
        logger.error(
            f"Unhandled exception processing {context.get('update_type', 'unknown')} | "
            f"user_id={context.get('user_id')} | "
            f"chat_id={context.get('chat_id')} | "
            f"handler={context.get('handler')} | "
            f"fsm_state={context.get('fsm_state')} | "
            f"exception={exception.__class__.__name__}: {str(exception)}"
        )

        # Stack trace completo a un nivel más detallado
        tb_str = "".join(traceback.format_exception(
            type(exception), exception, exception.__traceback__
        ))
        logger.debug(f"Full traceback:\n{tb_str}")

        # Loguear línea del archivo donde ocurrió (primera línea del traceback)
        tb = exception.__traceback__
        if tb:
            filename = tb.tb_frame.f_code.co_filename
            lineno = tb.tb_lineno
            funcname = tb.tb_frame.f_code.co_name
            logger.error(
                f"Exception origin: {filename}:{lineno} in {funcname}"
            )

    async def _notify_user(self, event: TelegramObject, context: dict, data: dict) -> None:
        """Envía mensaje de error genérico al usuario en la voz de Lucien."""
        try:
            bot = None
            chat_id = context.get("chat_id")

            if not chat_id:
                logger.warning("Cannot notify user: no chat_id available")
                return

            # Obtener bot de data
            bot = data.get("bot")

            if not bot:
                logger.warning("Cannot notify user: no bot available in data")
                return

            # Mensaje genérico en la voz de Lucien
            error_message = (
                "🎩 <b>Lucien:</b>\n\n"
                "<i>Algo inesperado ha ocurrido en los archivos de Diana...</i>\n\n"
                "He registrado el incidente y se tomará medidas.\n\n"
                "<i>Por favor, intente de nuevo en unos momentos.</i>"
            )

            # Enviar solo si es callback query (tiene message para editar)
            if hasattr(event, "message") and event.message:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=event.message.message_id,
                    text=error_message,
                    parse_mode="HTML"
                )
            elif hasattr(event, "answer"):
                # Para callbacks, usar answer() con show_alert
                await event.answer(
                    "🎩 He registrado un error. Por favor, intenta de nuevo.",
                    show_alert=True
                )

        except Exception as e:
            logger.warning(f"Failed to notify user about error: {e}")

    async def _notify_admins(self, exception: Exception, context: dict, data: dict) -> None:
        """Notifica a admins sobre errores críticos."""
        if not self.notify_admins or not bot_config.ADMIN_IDS:
            return

        try:
            bot = data.get("bot")
            if not bot:
                return

            # Evitar spam: no notificar el mismo error múltiples veces
            error_signature = f"{exception.__class__.__name__}:{str(exception)[:50]}"
            if error_signature in self._admins_notified_recently:
                return

            self._admins_notified_recently.add(error_signature)

            admin_message = (
                "🚨 <b>Error Crítico en Lucien Bot</b>\n\n"
                f"<code>{exception.__class__.__name__}</code>: {str(exception)}\n\n"
                f"<b>Contexto:</b>\n"
                f"• User: <code>{context.get('user_id')}</code>\n"
                f"• Chat: <code>{context.get('chat_id')}</code>\n"
                f"• Handler: <code>{context.get('handler')}</code>\n"
                f"• FSM: <code>{context.get('fsm_state')}</code>\n\n"
                f"<b>Origen:</b>\n"
                f"<code>{traceback.format_exception(type(exception), exception, exception.__traceback__)[-1].strip()}</code>"
            )

            for admin_id in bot_config.ADMIN_IDS:
                try:
                    await bot.send_message(
                        chat_id=admin_id,
                        text=admin_message,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.warning(f"Failed to notify admin {admin_id}: {e}")

            # Limpiar after a delay (simple dedup window)
            import asyncio
            asyncio.get_event_loop().call_later(60, lambda: self._admins_notified_recently.discard(error_signature))

        except Exception as e:
            logger.warning(f"Failed to notify admins: {e}")

    def _is_critical_error(self, exception: Exception) -> bool:
        """Determina si el error es crítico y requiere notificación a admins."""

        # Errors que siempre son críticos
        critical_types = (
            ConnectionError,
            TimeoutError,
            OSError,  # Includes file/disk errors
        )

        if isinstance(exception, critical_types):
            return True

        # Database errors
        if "sqlalchemy" in str(type(exception)).lower():
            return True

        if "database" in str(exception).lower():
            return True

        # Errors de red externos
        if "redis" in str(exception).lower():
            return True

        # Errors de Telegram API
        if hasattr(exception, "status") and exception.status == 403:
            return False  # Bot bloqueado por usuario - no es crítico

        if hasattr(exception, "status") and exception.status >= 500:
            return True  # Errores de Telegram server

        return False
