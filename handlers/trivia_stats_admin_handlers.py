"""
Handlers de Admin - Estadísticas de Trivia

Dashboard completo para custodios: promos, usuarios, rankings y exportación CSV.
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.enums import ParseMode
from handlers.admin_handlers import is_admin
from services.trivia_stats_service import TriviaStatsService
import logging
import os

logger = logging.getLogger(__name__)
router = Router()


# ==================== KEYBOARD HELPER ====================

def trivia_stats_keyboard() -> InlineKeyboardMarkup:
    """Returns the keyboard for trivia stats admin menu."""
    keyboard = [
        [InlineKeyboardButton("📊 Dashboard", callback_data="trivia_stats_dashboard"),
         InlineKeyboardButton("🎁 Promociones", callback_data="trivia_stats_promotions")],
        [InlineKeyboardButton("👤 Usuarios", callback_data="trivia_stats_users"),
         InlineKeyboardButton("🏆 Rankings", callback_data="trivia_stats_rankings")],
        [InlineKeyboardButton("📥 Exportar Todo (CSV)", callback_data="trivia_stats_export")],
        [InlineKeyboardButton("« Menú Admin", callback_data="admin_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ==================== FORMAT HELPERS ====================

def _format_promo_message(stats: list) -> str:
    """Format promotion stats for display."""
    if not stats:
        return "🎩 <b>Lucien:</b>\n\nNo hay promociones registradas."

    lines = ["🎩 <b>Lucien:</b>\n\n<i>Las promociones de Diana bajo nuestra vigilancia...</i>\n\n"]

    for promo in stats:
        status_emoji = {
            "active": "🟢",
            "paused": "🟡",
            "expired": "🔴",
            "completed": "✅"
        }.get(promo.get("status", ""), "⚪")

        codes = promo.get("codes_by_status", {})
        active_codes = codes.get("active", 0)
        used_codes = codes.get("used", 0)

        lines.append(
            f"{status_emoji} <b>{promo.get('name', 'Sin nombre')}</b>\n"
            f"   📊 {promo.get('total_codes', 0)} códigos | "
            f"🟢 {active_codes} activos | "
            f"✅ {used_codes} usados\n"
            f"   📈 {promo.get('used_percentage', 0)}% canjeado"
        )

        if promo.get("question_set"):
            lines.append(f"   📚 Set: {promo['question_set']}")

        if promo.get("duration_remaining"):
            lines.append(f"   ⏱️ {promo['duration_remaining']}")

        lines.append("")

    return "\n".join(lines).strip()


def _format_ranking_table(entries: list, value_label: str) -> str:
    """Format a ranking table for display."""
    if not entries:
        return f"No hay datos para {value_label}."

    medals = ["🥇", "🥈", "🥉"]
    lines = []

    for entry in entries:
        rank = entry.get("rank", 0)
        medal = medals[rank - 1] if rank <= 3 else f"{rank}."
        username = entry.get("username") or entry.get("first_name") or "Anónimo"
        value = entry.get("value", 0)

        lines.append(f"{medal} {username}: <b>{value}</b> {value_label}")

    return "\n".join(lines)


# ==================== CALLBACK HANDLERS ====================

@router.callback_query(F.data == "admin_trivia_stats", lambda cb: is_admin(cb.from_user.id))
async def admin_trivia_stats_menu(callback: CallbackQuery):
    """Main trivia stats admin menu."""
    await callback.message.edit_text(
        "🎩 <b>Lucien:</b>\n\n"
        "<i>El arte de medir el conocimiento de los visitantes...</i>\n\n"
        "Seleccione una opción:",
        reply_markup=trivia_stats_keyboard(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.callback_query(F.data == "trivia_stats_dashboard", lambda cb: is_admin(cb.from_user.id))
async def trivia_stats_dashboard_callback(callback: CallbackQuery):
    """Show summary dashboard with key metrics."""
    service = TriviaStatsService()
    try:
        dashboard = service.get_full_dashboard()
        if not dashboard:
            await callback.message.edit_text(
                "🎩 <b>Lucien:</b>\n\nNo hay datos disponibles aún.",
                reply_markup=trivia_stats_keyboard(),
                parse_mode=ParseMode.HTML
            )
            await callback.answer()
            return

        users_summary = dashboard.get("users_summary", {})
        rankings = dashboard.get("rankings", {})
        promotions = dashboard.get("promotions", [])

        active_promos = sum(1 for p in promotions if p.get("status") == "active")
        total_promos = len(promotions)

        top_scorers = rankings.get("top_scorers", [])
        top_streaks = rankings.get("top_streaks", [])
        top_codes = rankings.get("top_codes", [])

        top_scorer_value = top_scorers[0].get("value", 0) if top_scorers else 0
        top_streak_value = top_streaks[0].get("value", 0) if top_streaks else 0
        top_code_value = top_codes[0].get("value", 0) if top_codes else 0

        text = (
            f"🎩 <b>Lucien:</b>\n\n"
            f"<i>Los números que Diana observa con satisfacción...</i>\n\n"
            f"📊 <b>Resumen del Reino:</b>\n\n"
            f"🎁 <b>Promociones:</b> {active_promos} activas / {total_promos} totales\n\n"
            f"👥 <b>Visitantes:</b>\n"
            f"   • Trivia estándar: {users_summary.get('total_trivia_users', 0)}\n"
            f"   • Trivia VIP: {users_summary.get('total_vip_trivia_users', 0)}\n\n"
            f"📈 <b>Métricas:</b>\n"
            f"   • Tasa promedio de acierto: {users_summary.get('avg_correctness_rate', 0)}%\n"
            f"   • Racha promedio: {users_summary.get('avg_streak', 0)}\n\n"
            f"🏆 <b>Top Records:</b>\n"
            f"   • Mayor racha: {top_streak_value}\n"
            f"   • Más códigos usados: {top_code_value}\n"
            f"   • Mayor puntuación: {top_scorer_value}"
        )

        await callback.message.edit_text(
            text,
            reply_markup=trivia_stats_keyboard(),
            parse_mode=ParseMode.HTML
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"trivia_stats_dashboard_callback error: {e}")
        await callback.answer("Error al cargar dashboard")
    finally:
        service.close()


@router.callback_query(F.data == "trivia_stats_promotions", lambda cb: is_admin(cb.from_user.id))
async def trivia_stats_promotions_callback(callback: CallbackQuery):
    """Show list of all promotions with metrics."""
    service = TriviaStatsService()
    try:
        promotions = service.get_all_promotions_stats()
        text = _format_promo_message(promotions)

        await callback.message.edit_text(
            text,
            reply_markup=trivia_stats_keyboard(),
            parse_mode=ParseMode.HTML
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"trivia_stats_promotions_callback error: {e}")
        await callback.answer("Error al cargar promociones")
    finally:
        service.close()


@router.callback_query(F.data == "trivia_stats_users", lambda cb: is_admin(cb.from_user.id))
async def trivia_stats_users_callback(callback: CallbackQuery):
    """Show top 10 users by correct answers."""
    service = TriviaStatsService()
    try:
        top_scorers = service.get_top_scorers(limit=10)
        medals = ["🥇", "🥈", "🥉"]

        if not top_scorers:
            text = "🎩 <b>Lucien:</b>\n\nNo hay datos de usuarios aún."
        else:
            lines = [
                "🎩 <b>Lucien:</b>\n\n"
                "<i>Los visitantes que más brillan en los exámenes de Diana...</i>\n\n"
                "🏆 <b>Top 10 Scorers (respuestas correctas):</b>\n\n"
            ]

            for entry in top_scorers:
                rank = entry.get("rank", 0)
                medal = medals[rank - 1] if rank <= 3 else f"{rank}."
                username = entry.get("username") or entry.get("first_name") or "Anónimo"
                value = entry.get("value", 0)
                lines.append(f"{medal} {username}: <b>{value}</b>")

            text = "\n".join(lines)

        await callback.message.edit_text(
            text,
            reply_markup=trivia_stats_keyboard(),
            parse_mode=ParseMode.HTML
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"trivia_stats_users_callback error: {e}")
        await callback.answer("Error al cargar usuarios")
    finally:
        service.close()


@router.callback_query(F.data == "trivia_stats_rankings", lambda cb: is_admin(cb.from_user.id))
async def trivia_stats_rankings_callback(callback: CallbackQuery):
    """Show all 3 rankings: scorers, streaks, codes."""
    service = TriviaStatsService()
    try:
        dashboard = service.get_full_dashboard()
        rankings = dashboard.get("rankings", {})

        top_scorers = rankings.get("top_scorers", [])
        top_streaks = rankings.get("top_streaks", [])
        top_codes = rankings.get("top_codes", [])

        text = (
            "🎩 <b>Lucien:</b>\n\n"
            "<i>Las jerarquías del conocimiento...</i>\n\n"
            "🥇 <b>Top Scorers (respuestas correctas):</b>\n"
            f"{_format_ranking_table(top_scorers, 'aciertos')}\n\n"
            "🔥 <b>Top Streaks (racha máxima):</b>\n"
            f"{_format_ranking_table(top_streaks, 'preguntas')}\n\n"
            "📦 <b>Top Codes (códigos usados):</b>\n"
            f"{_format_ranking_table(top_codes, 'códigos')}"
        )

        await callback.message.edit_text(
            text,
            reply_markup=trivia_stats_keyboard(),
            parse_mode=ParseMode.HTML
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"trivia_stats_rankings_callback error: {e}")
        await callback.answer("Error al cargar rankings")
    finally:
        service.close()


@router.callback_query(F.data == "trivia_stats_export", lambda cb: is_admin(cb.from_user.id))
async def trivia_stats_export_callback(callback: CallbackQuery):
    """Generate and send 3 CSV files."""
    service = TriviaStatsService()
    try:
        await callback.message.edit_text(
            "🎩 <b>Lucien:</b>\n\n"
            "<i>Preparando los pergaminos de Diana...</i>\n\n"
            "⏳ Generando exports CSV...",
            reply_markup=trivia_stats_keyboard(),
            parse_mode=ParseMode.HTML
        )

        files_sent = 0

        # Export promotions
        promos_path = service.export_promotions_csv()
        if promos_path:
            with open(promos_path, "rb") as f:
                await callback.message.reply_document(
                    document=f,
                    caption="📊 <b>Reporte de Promociones</b>",
                    parse_mode=ParseMode.HTML
                )
            os.unlink(promos_path)
            files_sent += 1

        # Export users stats
        users_path = service.export_users_stats_csv()
        if users_path:
            with open(users_path, "rb") as f:
                await callback.message.reply_document(
                    document=f,
                    caption="👥 <b>Estadísticas de Usuarios</b>",
                    parse_mode=ParseMode.HTML
                )
            os.unlink(users_path)
            files_sent += 1

        # Export rankings
        rankings_path = service.export_rankings_csv()
        if rankings_path:
            with open(rankings_path, "rb") as f:
                await callback.message.reply_document(
                    document=f,
                    caption="🏆 <b>Rankings Completos</b>",
                    parse_mode=ParseMode.HTML
                )
            os.unlink(rankings_path)
            files_sent += 1

        if files_sent == 0:
            await callback.message.edit_text(
                "🎩 <b>Lucien:</b>\n\nNo hay datos para exportar.",
                reply_markup=trivia_stats_keyboard(),
                parse_mode=ParseMode.HTML
            )
        else:
            await callback.message.edit_text(
                f"🎩 <b>Lucien:</b>\n\n"
                f"✅ <b>{files_sent}</b> archivos CSV generados y enviados.\n\n"
                "<i>Los pergaminos están en sus manos, Custodio.</i>",
                reply_markup=trivia_stats_keyboard(),
                parse_mode=ParseMode.HTML
            )

        await callback.answer()
    except Exception as e:
        logger.error(f"trivia_stats_export_callback error: {e}")
        await callback.answer("Error al generar exports")
    finally:
        service.close()


# ==================== ENTRY POINT COMMAND ====================

@router.message(Command("trivia_stats"))
async def trivia_stats_entry(message: Message):
    """Entry point command for /trivia_stats."""
    if not is_admin(message.from_user.id):
        await message.answer(
            "🎩 <b>Lucien:</b>\n\n"
            "<i>Este sanctario solo es accesible para los Custodios.</i>",
            parse_mode=ParseMode.HTML
        )
        return

    await message.answer(
        "🎩 <b>Lucien:</b>\n\n"
        "<i>El arte de medir el conocimiento de los visitantes...</i>\n\n"
        "Seleccione una opción:",
        reply_markup=trivia_stats_keyboard(),
        parse_mode=ParseMode.HTML
    )