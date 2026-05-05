# Trivia Stats Dashboard — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir un dashboard de estadísticas de trivias y descuentos por racha para Custodios, extrayendo datos de los modelos existentes sin modificarlos.

**Architecture:** Tres capas — TriviaStatsService (lógica de queries y métricas), handler (interacción con Custodios), exports CSV. Todo consumo read-only de modelos existentes.

**Tech Stack:** Python, SQLAlchemy, Telegram Bot API (envío de CSVs como documentos).

---

## Verificaciones Previas (Spec Sección 9)

Ejecutar ANTES de empezar:

```bash
# 1. Verificar valores de game_type en GameRecord
python -c "
from models.database import SessionLocal
from models.models import GameRecord
db = SessionLocal()
vals = db.query(GameRecord.game_type).distinct().all()
print([v[0] for v in vals])
db.close()
"

# 2. Verificar estados de DiscountCodeStatus
python -c "
from models.models import DiscountCodeStatus
print([e.value for e in DiscountCodeStatus])
"

# 3. Verificar que discount_tiers es Text (JSON string)
python -c "
from models.models import TriviaPromotionConfig
import inspect
col = TriviaPromotionConfig.__table__.columns['discount_tiers']
print(col.type)
"
```

---

## Estructura de Archivos

```
services/trivia_stats_service.py   (nuevo)
handlers/trivia_stats_admin_handlers.py  (nuevo)
keyboards/inline_keyboards.py      (modificar: agregar keyboards de stats)
services/__init__.py               (modificar: exportar TriviaStatsService)
```

---

## Task 1: TriviaStatsService — Estructura Base + Promo Stats

**Files:**
- Create: `services/trivia_stats_service.py`
- Modify: `services/__init__.py`

- [ ] **Step 1: Escribir el servicio base (sin lógica aún)**

```python
"""
Trivia Stats Service - Dashboard de Estadísticas de Trivias

Gestiona métricas de promociones por racha, usuarios y rankings.
Solo lectura — no modifica ningún modelo existente.
"""
import csv
import tempfile
import logging
import json
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func
from models.models import (
    TriviaPromotionConfig,
    DiscountCode,
    DiscountCodeStatus,
    GameRecord,
    QuestionSet,
    User
)
from models.database import SessionLocal

logger = logging.getLogger(__name__)


class TriviaStatsService:
    """Servicio de estadísticas para el dashboard de trivias"""

    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        self._owns_session = db is None

    def _get_db(self) -> Session:
        if self.db is None:
            self.db = SessionLocal()
        return self.db

    def close(self):
        if self._owns_session and self.db:
            self.db.close()
            self.db = None

    # ==================== PROMO STATS ====================

    def get_promotion_stats(self, config_id: int) -> dict:
        """
        Obtiene métricas detalladas de UNA promoción.
        """
        db = self._get_db()
        config = db.query(TriviaPromotionConfig).filter(
            TriviaPromotionConfig.id == config_id
        ).first()
        if not config:
            logger.info(f"trivia_stats_service - get_promotion_stats - {config_id} - not_found")
            return {}

        codes = db.query(DiscountCode).filter(
            DiscountCode.config_id == config_id
        ).all()

        total = len(codes)
        by_status = {
            'active': sum(1 for c in codes if c.status == DiscountCodeStatus.ACTIVE),
            'used': sum(1 for c in codes if c.status == DiscountCodeStatus.USED),
            'cancelled': sum(1 for c in codes if c.status == DiscountCodeStatus.CANCELLED),
            'expired': sum(1 for c in codes if c.status == DiscountCodeStatus.EXPIRED),
        }

        # Parse tiers
        tiers = []
        if config.discount_tiers:
            try:
                tiers = json.loads(config.discount_tiers)
            except (json.JSONDecodeError, TypeError):
                tiers = [{'streak': config.required_streak, 'discount': config.discount_percentage}]
        else:
            tiers = [{'streak': config.required_streak, 'discount': config.discount_percentage}]

        # Question set name
        question_set_name = None
        if config.question_set_id:
            qs = db.query(QuestionSet).filter(QuestionSet.id == config.question_set_id).first()
            question_set_name = qs.name if qs else None

        # Time remaining
        from services.trivia_discount_service import TriviaDiscountService
        tds = TriviaDiscountService()
        duration_info = None
        if config.duration_minutes:
            remaining = tds.get_time_remaining_formatted(config_id)
            duration_info = remaining

        promo_name = config.promotion.name if config.promotion else config.custom_description or config.name

        result = {
            'id': config.id,
            'name': promo_name,
            'status': config.status,
            'total_codes': total,
            'codes_by_status': by_status,
            'claimed': config.codes_claimed,
            'available': max(0, config.max_codes - config.codes_claimed),
            'max_codes': config.max_codes,
            'used_percentage': round((by_status['used'] / config.max_codes * 100), 1) if config.max_codes > 0 else 0,
            'tiers': tiers,
            'question_set': question_set_name,
            'duration_remaining': duration_info,
            'start_date': config.start_date.isoformat() if config.start_date else None,
            'end_date': config.end_date.isoformat() if config.end_date else None,
        }

        logger.info(f"trivia_stats_service - get_promotion_stats - {config_id} - codes:{total}")
        return result

    def get_all_promotions_stats(self) -> list[dict]:
        """
        Obtiene métricas de TODAS las promociones (activas e inactivas).
        """
        db = self._get_db()
        configs = db.query(TriviaPromotionConfig).order_by(
            TriviaPromotionConfig.created_at.desc()
        ).all()

        results = []
        for config in configs:
            stats = self.get_promotion_stats(config.id)
            if stats:
                results.append(stats)

        logger.info(f"trivia_stats_service - get_all_promotions_stats - count:{len(results)}")
        return results
```

- [ ] **Step 2: Exportar en `services/__init__.py`**

Buscar la línea de exports y agregar:
```python
from services.trivia_stats_service import TriviaStatsService
```

- [ ] **Step 3: Verificar que el servicio se importa sin errores**

```bash
python -c "from services.trivia_stats_service import TriviaStatsService; print('OK')"
```

---

## Task 2: TriviaStatsService — User Stats

**Files:**
- Modify: `services/trivia_stats_service.py` (agregar métodos al final)

- [ ] **Step 1: Agregar método `get_user_trivia_stats`**

```python
    # ==================== USER STATS ====================

    def _calculate_max_streak(self, user_id: int, game_type: str) -> int:
        """
        Calcula la racha máxima observada en sesiones históricas.
        Una sesión = secuencia ininterrumpida de payout > 0.
        """
        db = self._get_db()
        records = db.query(GameRecord).filter(
            GameRecord.user_id == user_id,
            GameRecord.game_type == game_type
        ).order_by(GameRecord.played_at.asc()).all()

        max_streak = 0
        current_streak = 0
        for record in records:
            if record.payout > 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        return max_streak

    def get_user_trivia_stats(self, user_id: int) -> dict:
        """
        Obtiene métricas de trivia para UN usuario (todas sus partidas).
        """
        db = self._get_db()

        # User info
        user = db.query(User).filter(User.telegram_id == user_id).first()
        username = user.username if user else None
        first_name = user.first_name if user else None

        results = {}
        for game_type in ['trivia', 'trivia_vip']:
            records = db.query(GameRecord).filter(
                GameRecord.user_id == user_id,
                GameRecord.game_type == game_type
            ).all()

            total = len(records)
            correct = sum(1 for r in records if r.payout > 0)
            incorrect = total - correct
            rate = round((correct / total * 100), 1) if total > 0 else 0.0
            besitos = sum(r.payout for r in records)
            max_streak = self._calculate_max_streak(user_id, game_type)

            # Current streak (today)
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_records = db.query(GameRecord).filter(
                GameRecord.user_id == user_id,
                GameRecord.game_type == game_type,
                GameRecord.played_at >= today
            ).order_by(GameRecord.played_at.desc()).all()

            current_streak = 0
            for r in today_records:
                if r.payout > 0:
                    current_streak += 1
                else:
                    break

            # Codes
            codes = db.query(DiscountCode).filter(
                DiscountCode.user_id == user_id
            ).all()
            codes_earned = sum(1 for c in codes if c.status == DiscountCodeStatus.ACTIVE)
            codes_used = sum(1 for c in codes if c.status == DiscountCodeStatus.USED)

            results[game_type] = {
                'total_plays': total,
                'correct_answers': correct,
                'incorrect_answers': incorrect,
                'correctness_rate': rate,
                'current_streak': current_streak,
                'max_streak': max_streak,
                'besitos_earned': besitos,
                'codes_earned': codes_earned,
                'codes_used': codes_used,
            }

        logger.info(f"trivia_stats_service - get_user_trivia_stats - {user_id} - done")
        return {
            'user_id': user_id,
            'username': username,
            'first_name': first_name,
            'stats': results
        }
```

---

## Task 3: TriviaStatsService — Rankings

**Files:**
- Modify: `services/trivia_stats_service.py`

- [ ] **Step 1: Agregar métodos de ranking**

```python
    # ==================== RANKINGS ====================

    def _build_user_rank_entry(self, user_id: int, value: float) -> dict:
        """Helper para construir entrada de ranking."""
        db = self._get_db()
        user = db.query(User).filter(User.telegram_id == user_id).first()
        return {
            'user_id': user_id,
            'username': user.username if user else None,
            'first_name': user.first_name if user else None,
            'value': value
        }

    def get_top_scorers(self, limit: int = 10) -> list[dict]:
        """Top usuarios por total de respuestas correctas (trivia + trivia_vip)."""
        db = self._get_db()
        results = db.query(
            GameRecord.user_id,
            func.count(GameRecord.id).label('total'),
            func.sum(GameRecord.payout).label('correct')
        ).filter(
            GameRecord.game_type.in_(['trivia', 'trivia_vip']),
            GameRecord.payout > 0
        ).group_by(GameRecord.user_id).order_by(
            func.count(GameRecord.id).desc()
        ).limit(limit).all()

        rankings = []
        for rank, row in enumerate(results, 1):
            entry = self._build_user_rank_entry(row.user_id, int(row.correct or 0))
            entry['rank'] = rank
            rankings.append(entry)

        logger.info(f"trivia_stats_service - get_top_scorers - limit:{limit} - count:{len(rankings)}")
        return rankings

    def get_top_streaks(self, limit: int = 10) -> list[dict]:
        """Top usuarios por racha máxima registrada (trivia + trivia_vip)."""
        db = self._get_db()

        # Necesitamos calcular max_streak por usuario
        # Primero: obtener todos los usuarios únicos
        user_ids = db.query(GameRecord.user_id).filter(
            GameRecord.game_type.in_(['trivia', 'trivia_vip'])
        ).distinct().all()
        user_ids = [u[0] for u in user_ids]

        streaks = []
        for uid in user_ids:
            max_s = self._calculate_max_streak(uid, 'trivia')
            max_sv = self._calculate_max_streak(uid, 'trivia_vip')
            streaks.append({'user_id': uid, 'max_streak': max(max_s, max_sv)})

        streaks.sort(key=lambda x: x['max_streak'], reverse=True)
        streaks = streaks[:limit]

        rankings = []
        for rank, row in enumerate(streaks, 1):
            entry = self._build_user_rank_entry(row['user_id'], row['max_streak'])
            entry['rank'] = rank
            rankings.append(entry)

        logger.info(f"trivia_stats_service - get_top_streaks - limit:{limit} - count:{len(rankings)}")
        return rankings

    def get_top_codes_redeemed(self, limit: int = 10) -> list[dict]:
        """Top usuarios por códigos USADOS."""
        db = self._get_db()
        results = db.query(
            DiscountCode.user_id,
            func.count(DiscountCode.id).label('used_count')
        ).filter(
            DiscountCode.status == DiscountCodeStatus.USED
        ).group_by(
            DiscountCode.user_id
        ).order_by(
            func.count(DiscountCode.id).desc()
        ).limit(limit).all()

        rankings = []
        for rank, row in enumerate(results, 1):
            entry = self._build_user_rank_entry(row.user_id, int(row.used_count))
            entry['rank'] = rank
            rankings.append(entry)

        logger.info(f"trivia_stats_service - get_top_codes_redeemed - limit:{limit} - count:{len(rankings)}")
        return rankings
```

---

## Task 4: TriviaStatsService — Exports CSV

**Files:**
- Modify: `services/trivia_stats_service.py`

- [ ] **Step 1: Agregar métodos de exportación**

```python
    # ==================== EXPORTS ====================

    def export_promotions_csv(self) -> str | None:
        """Genera CSV con métricas de todas las promociones."""
        db = self._get_db()
        promotions = self.get_all_promotions_stats()
        if not promotions:
            return None

        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline=""
        )
        try:
            writer = csv.DictWriter(tmp, fieldnames=[
                "id", "name", "status", "total_codes",
                "active", "used", "cancelled", "expired",
                "claimed", "available", "max_codes",
                "used_percentage", "question_set", "duration_remaining"
            ])
            writer.writeheader()

            for p in promotions:
                writer.writerow({
                    "id": p['id'],
                    "name": p['name'],
                    "status": p['status'],
                    "total_codes": p['total_codes'],
                    "active": p['codes_by_status']['active'],
                    "used": p['codes_by_status']['used'],
                    "cancelled": p['codes_by_status']['cancelled'],
                    "expired": p['codes_by_status']['expired'],
                    "claimed": p['claimed'],
                    "available": p['available'],
                    "max_codes": p['max_codes'],
                    "used_percentage": p['used_percentage'],
                    "question_set": p['question_set'] or "",
                    "duration_remaining": p['duration_remaining'] or ""
                })
            tmp.close()
            logger.info(f"trivia_stats_service - export_promotions_csv - generated")
            return tmp.name
        except Exception as e:
            logger.error(f"trivia_stats_service - export_promotions_csv - error:{e}")
            return None

    def export_users_stats_csv(self) -> str | None:
        """Genera CSV con métricas de usuarios (uno por game_type)."""
        db = self._get_db()
        # Obtener todos los usuarios que jugaron trivia
        user_ids = db.query(GameRecord.user_id).filter(
            GameRecord.game_type.in_(['trivia', 'trivia_vip'])
        ).distinct().all()
        user_ids = [u[0] for u in user_ids]

        if not user_ids:
            return None

        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline=""
        )
        try:
            writer = csv.DictWriter(tmp, fieldnames=[
                "telegram_id", "username", "first_name", "game_type",
                "total_plays", "correct", "incorrect", "rate",
                "current_streak", "max_streak", "besitos",
                "codes_earned", "codes_used"
            ])
            writer.writeheader()

            for uid in user_ids:
                user_stats = self.get_user_trivia_stats(uid)
                for game_type, stats in user_stats['stats'].items():
                    if stats['total_plays'] == 0:
                        continue
                    user = db.query(User).filter(User.telegram_id == uid).first()
                    writer.writerow({
                        "telegram_id": uid,
                        "username": user.username if user else "",
                        "first_name": user.first_name if user else "",
                        "game_type": game_type,
                        "total_plays": stats['total_plays'],
                        "correct": stats['correct_answers'],
                        "incorrect": stats['incorrect_answers'],
                        "rate": stats['correctness_rate'],
                        "current_streak": stats['current_streak'],
                        "max_streak": stats['max_streak'],
                        "besitos": stats['besitos_earned'],
                        "codes_earned": stats['codes_earned'],
                        "codes_used": stats['codes_used'],
                    })
            tmp.close()
            logger.info(f"trivia_stats_service - export_users_stats_csv - generated")
            return tmp.name
        except Exception as e:
            logger.error(f"trivia_stats_service - export_users_stats_csv - error:{e}")
            return None

    def export_rankings_csv(self) -> str | None:
        """Genera CSV con los tres rankings."""
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline=""
        )
        try:
            writer = csv.writer(tmp)

            # Block 1: top_scorers
            writer.writerow(["=== TOP SCORERS (respuestas correctas) ==="])
            writer.writerow(["rank", "user_id", "username", "first_name", "correct_answers"])
            for entry in self.get_top_scorers(limit=20):
                writer.writerow([
                    entry['rank'], entry['user_id'],
                    entry['username'] or "", entry['first_name'] or "",
                    entry['value']
                ])

            writer.writerow([])
            writer.writerow(["=== TOP STREAKS (racha máxima) ==="])
            writer.writerow(["rank", "user_id", "username", "first_name", "max_streak"])
            for entry in self.get_top_streaks(limit=20):
                writer.writerow([
                    entry['rank'], entry['user_id'],
                    entry['username'] or "", entry['first_name'] or "",
                    entry['value']
                ])

            writer.writerow([])
            writer.writerow(["=== TOP CODES (códigos usados) ==="])
            writer.writerow(["rank", "user_id", "username", "first_name", "codes_used"])
            for entry in self.get_top_codes_redeemed(limit=20):
                writer.writerow([
                    entry['rank'], entry['user_id'],
                    entry['username'] or "", entry['first_name'] or "",
                    entry['value']
                ])

            tmp.close()
            logger.info(f"trivia_stats_service - export_rankings_csv - generated")
            return tmp.name
        except Exception as e:
            logger.error(f"trivia_stats_service - export_rankings_csv - error:{e}")
            return None
```

---

## Task 5: TriviaStatsService — Dashboard Completo

**Files:**
- Modify: `services/trivia_stats_service.py`

- [ ] **Step 1: Agregar `get_full_dashboard`**

```python
    # ==================== DASHBOARD ====================

    def get_full_dashboard(self) -> dict:
        """
        Obtiene el dashboard completo: promos + resumen usuarios + rankings.
        """
        promotions = self.get_all_promotions_stats()

        # Resumen de usuarios (agregado)
        db = self._get_db()
        user_ids = db.query(GameRecord.user_id).filter(
            GameRecord.game_type.in_(['trivia', 'trivia_vip'])
        ).distinct().all()
        user_ids = [u[0] for u in user_ids]

        total_trivia_users = 0
        total_vip_trivia_users = 0
        total_rate = 0.0
        total_streak = 0

        for uid in user_ids:
            user_stats = self.get_user_trivia_stats(uid)
            trivia_stats = user_stats['stats'].get('trivia', {})
            vip_stats = user_stats['stats'].get('trivia_vip', {})

            if trivia_stats['total_plays'] > 0:
                total_trivia_users += 1
                total_rate += trivia_stats['correctness_rate']
                total_streak += trivia_stats['max_streak']

            if vip_stats['total_plays'] > 0:
                total_vip_trivia_users += 1

        count = max(1, total_trivia_users)
        avg_rate = round(total_rate / count, 1)
        avg_streak = round(total_streak / count, 1)

        rankings = {
            'top_scorers': self.get_top_scorers(limit=10),
            'top_streaks': self.get_top_streaks(limit=10),
            'top_codes': self.get_top_codes_redeemed(limit=10),
        }

        result = {
            'generated_at': datetime.utcnow().isoformat(),
            'promotions': promotions,
            'users_summary': {
                'total_trivia_users': total_trivia_users,
                'total_vip_trivia_users': total_vip_trivia_users,
                'avg_correctness_rate': avg_rate,
                'avg_streak': avg_streak,
            },
            'rankings': rankings
        }

        logger.info(f"trivia_stats_service - get_full_dashboard - promos:{len(promotions)}")
        return result
```

---

## Task 6: Handler de Admin

**Files:**
- Create: `handlers/trivia_stats_admin_handlers.py`
- Modify: `keyboards/inline_keyboards.py` (agregar keyboards de stats)

- [ ] **Step 1: Crear el handler**

```python
"""
Handlers de Estadísticas de Trivia para Custodios.

Solo lectura — consulta métricas y genera exports CSV.
"""
import logging
import os
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from services.trivia_stats_service import TriviaStatsService
from handlers.admin_decorators import admin_only

logger = logging.getLogger(__name__)

# ==================== KEYBOARD ====================

def trivia_stats_keyboard() -> InlineKeyboardMarkup:
    """Keyboard principal del dashboard de stats."""
    keyboard = [
        [
            InlineKeyboardButton("📊 Dashboard", callback_data="trivia_stats_dashboard"),
            InlineKeyboardButton("🎁 Promociones", callback_data="trivia_stats_promotions"),
        ],
        [
            InlineKeyboardButton("👤 Usuarios", callback_data="trivia_stats_users"),
            InlineKeyboardButton("🏆 Rankings", callback_data="trivia_stats_rankings"),
        ],
        [
            InlineKeyboardButton("📥 Exportar Todo (CSV)", callback_data="trivia_stats_export"),
        ],
        [
            InlineKeyboardButton("« Menú Admin", callback_data="admin_menu"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def _format_number(n: float) -> str:
    """Formatea número para mostrar (coma como separador de miles)."""
    return f"{n:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _format_promo_message(stats: dict) -> str:
    """Formatea métricas de una promoción para mensaje."""
    status_emoji = {
        'active': '🟢',
        'paused': '🟡',
        'expired': '🔴',
        'completed': '✅',
    }.get(stats['status'], '⚪')

    tiers_str = ", ".join(
        f"{t['streak']}→{t['discount']}%" for t in stats['tiers']
    )

    msg = f"""
{status_emoji} <b>{stats['name']}</b>

📦 Códigos: {stats['total_codes']} / {stats['max_codes']}
  🟢 Activos: {stats['codes_by_status']['active']}
  ✅ Usados: {stats['codes_by_status']['used']}
  ❌ Cancelados: {stats['codes_by_status']['cancelled']}
  ⏰ Expirados: {stats['codes_by_status']['expired']}

💰 Descuento: {tiers_str}
📊 Usage: {stats['used_percentage']}%
{f'⏳ Expira: {stats["duration_remaining"]}' if stats.get('duration_remaining') else f'📅 Hasta: {stats["end_date"] or "sin fecha"}'}
{f'📚 Tema: {stats["question_set"]}' if stats.get('question_set') else ''}
"""
    return msg.strip()


def _format_user_stats(stats: dict) -> str:
    """Formatea métricas de usuario para mensaje."""
    trivia = stats['stats'].get('trivia', {})
    vip = stats['stats'].get('trivia_vip', {})

    name = f"@{stats['username']}" if stats['username'] else stats['first_name'] or str(stats['user_id'])

    lines = [f"👤 <b>{name}</b>"]

    if trivia['total_plays'] > 0:
        lines.append(f"  ❓ Trivia: {trivia['correct_answers']}/{trivia['total_plays']} ({trivia['correctness_rate']}%) | "
                    f"🔥 máx {trivia['max_streak']} | 💋 {trivia['besitos_earned']}")
    if vip['total_plays'] > 0:
        lines.append(f"  🎩 VIP: {vip['correct_answers']}/{vip['total_plays']} ({vip['correctness_rate']}%) | "
                    f"🔥 máx {vip['max_streak']} | 💋 {vip['besitos_earned']}")

    codes = trivia['codes_earned'] + vip['codes_earned']
    codes_used = trivia['codes_used'] + vip['codes_used']
    if codes > 0 or codes_used > 0:
        lines.append(f"  🎫 Códigos: {codes} activos, {codes_used} usados")

    return "\n".join(lines)


def _format_ranking_table(entries: list[dict], value_label: str) -> str:
    """Formatea tabla de ranking."""
    if not entries:
        return "Sin datos aún."

    lines = [f"<b>🏆 {value_label}</b>", ""]
    for entry in entries:
        name = f"@{entry['username']}" if entry['username'] else entry['first_name'] or str(entry['user_id'])
        medal = "🥇" if entry['rank'] == 1 else "🥈" if entry['rank'] == 2 else "🥉" if entry['rank'] == 3 else f" {entry['rank']}."
        lines.append(f"{medal} {name}: <b>{entry['value']}</b>")

    return "\n".join(lines)


# ==================== HANDLERS ====================

async def trivia_stats_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point: muestra el menú principal del dashboard."""
    service = TriviaStatsService()
    try:
        keyboard = trivia_stats_keyboard()
        await update.message.reply_text(
            "📊 <b>Dashboard de Trivias</b>\n\n"
            "Selecciona una sección para ver las métricas:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    finally:
        service.close()


@admin_only
async def trivia_stats_dashboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback: resumen general del dashboard."""
    service = TriviaStatsService()
    try:
        data = service.get_full_dashboard()
        summary = data['users_summary']

        promos_active = sum(1 for p in data['promotions'] if p['status'] == 'active')
        promos_total = len(data['promotions'])

        msg = f"""📊 <b>Dashboard de Trivias</b>

🕐 Generado: {data['generated_at'][:19]}

<b>📦 Promociones:</b>
  {promos_active} activas de {promos_total} totales

<b>👥 Usuarios:</b>
  ❓ Trivia: {summary['total_trivia_users']} usuarios únicos
  🎩 VIP: {summary['total_vip_trivia_users']} usuarios únicos
  📈 Tasa promedio: {summary['avg_correctness_rate']}%
  🔥 Racha promedio: {summary['avg_streak']}

<b>🏆 Rankings (Top 10):</b>
  🥇 Top scorer: {data['rankings']['top_scorers'][0]['value'] if data['rankings']['top_scorers'] else 'N/A'} correctas
  🔥 Top streak: {data['rankings']['top_streaks'][0]['value'] if data['rankings']['top_streaks'] else 'N/A'}
  🎫 Top códigos: {data['rankings']['top_codes'][0]['value'] if data['rankings']['top_codes'] else 'N/A'} usados
"""
        await update.callback_query.edit_message_text(
            msg.strip(),
            reply_markup=trivia_stats_keyboard(),
            parse_mode="HTML"
        )
    finally:
        service.close()


@admin_only
async def trivia_stats_promotions_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback: lista de promociones con métricas."""
    service = TriviaStatsService()
    try:
        promos = service.get_all_promotions_stats()
        if not promos:
            await update.callback_query.edit_message_text(
                "No hay promociones configuradas.",
                reply_markup=trivia_stats_keyboard()
            )
            return

        lines = ["📦 <b>Promociones por Racha</b>\n"]
        for p in promos:
            lines.append(_format_promo_message(p))
            lines.append("───────────")

        text = "\n".join(lines)[:4096]
        await update.callback_query.edit_message_text(
            text,
            reply_markup=trivia_stats_keyboard(),
            parse_mode="HTML"
        )
    finally:
        service.close()


@admin_only
async def trivia_stats_users_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback: top usuarios por correctas + besitos + códigos."""
    service = TriviaStatsService()
    try:
        db = service._get_db()
        from models.models import GameRecord
        user_ids = db.query(GameRecord.user_id).filter(
            GameRecord.game_type.in_(['trivia', 'trivia_vip'])
        ).distinct().all()
        user_ids = [u[0] for u in user_ids]
        db.close()

        # Top 10 por correctas
        top_scorers = service.get_top_scorers(limit=10)
        lines = ["👤 <b>Top Usuarios — Trivia</b>\n"]

        for entry in top_scorers:
            name = f"@{entry['username']}" if entry['username'] else entry['first_name'] or str(entry['user_id'])
            medal = "🥇" if entry['rank'] == 1 else "🥈" if entry['rank'] == 2 else "🥉" if entry['rank'] == 3 else f" {entry['rank']}."
            lines.append(f"{medal} {name}: <b>{entry['value']}</b> correctas")

            # Agregar besitos y códigos del usuario
            user_stats = service.get_user_trivia_stats(entry['user_id'])
            for gt in ['trivia', 'trivia_vip']:
                s = user_stats['stats'].get(gt, {})
                if s['total_plays'] > 0:
                    lines.append(f"      {s['besitos_earned']} 💋 | {s['codes_used']} 🎫 | {s['correctness_rate']}% rate")

        text = "\n".join(lines)[:4096]
        await update.callback_query.edit_message_text(
            text,
            reply_markup=trivia_stats_keyboard(),
            parse_mode="HTML"
        )
    finally:
        service.close()


@admin_only
async def trivia_stats_rankings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback: rankings separados."""
    service = TriviaStatsService()
    try:
        data = service.get_full_dashboard()
        rankings = data['rankings']

        msg = _format_ranking_table(rankings['top_scorers'], "Top Scorers (correctas)")
        msg += "\n\n" + _format_ranking_table(rankings['top_streaks'], "Top Streaks (racha máxima)")
        msg += "\n\n" + _format_ranking_table(rankings['top_codes'], "Top Códigos (usados)")

        await update.callback_query.edit_message_text(
            msg[:4096],
            reply_markup=trivia_stats_keyboard(),
            parse_mode="HTML"
        )
    finally:
        service.close()


@admin_only
async def trivia_stats_export_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback: genera y envía los tres CSVs."""
    service = TriviaStatsService()
    try:
        await update.callback_query.edit_message_text(
            "📥 Generando exports CSV...",
            reply_markup=trivia_stats_keyboard()
        )

        promos_path = service.export_promotions_csv()
        users_path = service.export_users_stats_csv()
        rankings_path = service.export_rankings_csv()

        await update.callback_query.message.reply_text("✅ Exports generados:")

        if promos_path:
            with open(promos_path, 'rb') as f:
                await update.callback_query.message.reply_document(
                    document=f,
                    filename="trivia_promotions.csv",
                    caption="📦 Promociones"
                )
            os.unlink(promos_path)

        if users_path:
            with open(users_path, 'rb') as f:
                await update.callback_query.message.reply_document(
                    document=f,
                    filename="trivia_users.csv",
                    caption="👤 Métricas de Usuarios"
                )
            os.unlink(users_path)

        if rankings_path:
            with open(rankings_path, 'rb') as f:
                await update.callback_query.message.reply_document(
                    document=f,
                    filename="trivia_rankings.csv",
                    caption="🏆 Rankings"
                )
            os.unlink(rankings_path)

        if not promos_path and not users_path and not rankings_path:
            await update.callback_query.message.reply_text("⚠️ No hay datos para exportar.")

        await update.callback_query.message.reply_text(
            "📊 Dashboard de Trivias",
            reply_markup=trivia_stats_keyboard()
        )
    finally:
        service.close()
```

- [ ] **Step 2: Registrar los callbacks en `handlers/__init__.py`** (o donde se registran callbacks — verificar primero)

Buscar cómo se registran los demás callbacks admin y agregar los cinco nuevos.

---

## Task 7: Registrar Command y Callback Data

**Files:**
- Modify: `bot.py` o el archivo donde se registran los commands y callbacks

- [ ] **Step 1: Agregar command `/trivia_stats`**

Buscar dónde están los commands de admin (ej: `/stats`, `/admin`) y agregar `/trivia_stats`.

- [ ] **Step 2: Agregar los callback data handlers**

Los cinco callbacks registrados en la ruta de callbacks de admin:
- `trivia_stats_dashboard`
- `trivia_stats_promotions`
- `trivia_stats_users`
- `trivia_stats_rankings`
- `trivia_stats_export`

---

## Spec Coverage Checklist

- [x] Promo stats por config (`get_promotion_stats`, `get_all_promotions_stats`)
- [x] User stats por tipo juego (`get_user_trivia_stats`)
- [x] Rankings (`get_top_scorers`, `get_top_streaks`, `get_top_codes_redeemed`)
- [x] Dashboard completo (`get_full_dashboard`)
- [x] Exports CSV (`export_promotions_csv`, `export_users_stats_csv`, `export_rankings_csv`)
- [x] Handler admin con keyboard
- [x] Command entry (`/trivia_stats`)

**Gaps:** None.

**Placeholder scan:** None found — todos los métodos tienen implementación completa.

---

## Ejecución

Plan completo guardado en `docs/superpowers/plans/2026-05-05-trivia-stats-dashboard.md`.

**¿Cómo quieres ejecutarlo?**

1. **Subagent-Driven (recomendado)** — Un subagent por task, revisión entre tasks
2. **Inline Execution** — Ejecutar tasks en esta sesión usando executing-plans, con checkpoints
