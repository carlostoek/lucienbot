"""
Chat Action Middleware - Lucien Bot

Envía automáticamente la indicación "escribiendo..." mientras se procesan
mensajes y callbacks, mejorando la experiencia de usuario.
"""
from aiogram.utils.chat_action import ChatActionMiddleware as BaseChatActionMiddleware, ChatActionSender
from aiogram.types import CallbackQuery
import logging

logger = logging.getLogger(__name__)


class ChatActionMiddleware(BaseChatActionMiddleware):
    """
    Middleware que envía "typing" automáticamente mientras se procesa el handler.

    Heredado de aiogram.utils.chat_action.ChatActionMiddleware:
    - initial_sleep: segundos antes de enviar la primera indicación (default 0.5)
    - action: acción a enviar (default "typing")
    - interval: intervalo de repetición en segundos (default 5.0)

    Extendido para soportar también CallbackQuery (botones).
    """

    def __init__(self):
        super().__init__()
        logger.debug("[chat_action] ChatActionMiddleware inicializado")

    async def __call__(self, handler, event, data):
        """
        Handle both Message and CallbackQuery events.
        For CallbackQuery, we send 'typing' to the user's chat.
        """
        from aiogram.types import Message

        if isinstance(event, Message):
            return await super().__call__(handler, event, data)

        # Handle CallbackQuery - extract chat_id from the message
        if isinstance(event, CallbackQuery):
            bot = data["bot"]
            message = event.message
            if message:
                chat_id = message.chat.id
                message_thread_id = message.message_thread_id if message.is_topic_message else None
            else:
                # Fallback: use from_user.id (no group context)
                chat_id = event.from_user.id
                message_thread_id = None

            async with ChatActionSender(
                bot=bot,
                chat_id=chat_id,
                action="typing",
                message_thread_id=message_thread_id,
            ):
                return await handler(event, data)

        # For any other event type, just pass through
        return await handler(event, data)
