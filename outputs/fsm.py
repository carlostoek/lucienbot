"""
FSM para Sistema de Racha Diaria - Lucien Bot

Estados y transiciones para el flujo de reclamar racha diaria.
"""
from aiogram.fsm.state import State, StatesGroup


class DailyStreakStates(StatesGroup):
    """Estados para el flujo de racha diaria"""
    checking_streak = State()      # Verificando estado de racha
    streak_active = State()        # Usuario tiene racha activa, mostrando estado
    streak_claiming = State()      # Procesando reclamo de racha
    streak_lost = State()          # Racha perdida, mostrando opción de reiniciar
    grace_period = State()          # Dentro de ventana de gracia de 48h


# ==================== CONSTANTES DE GRACIA ====================

GRACE_PERIOD_HOURS = 48           # Ventana de gracia: 48 horas
MIN_HOURS_BETWEEN_CLAIMS = 20     # Mínimo para considerar "en racha"
BONUS_PER_STREAK_DAY = 5          # Besitos extra por cada día de racha
MAX_BONUS = 50                    # Tope máximo de bonus por racha
