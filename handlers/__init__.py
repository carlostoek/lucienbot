from .common_handlers import router as common_router
from .admin_handlers import router as admin_router
from .channel_handlers import router as channel_router
from .vip_handlers import router as vip_router
from .free_channel_handlers import router as free_channel_router
# Fase 1 - Gamificación
from .gamification_user_handlers import router as gamification_user_router
from .gamification_admin_handlers import router as gamification_admin_router
from .broadcast_handlers import router as broadcast_router

__all__ = [
    'common_router',
    'admin_router',
    'channel_router',
    'vip_router',
    'free_channel_router',
    # Fase 1 - Gamificación
    'gamification_user_router',
    'gamification_admin_router',
    'broadcast_router'
]
