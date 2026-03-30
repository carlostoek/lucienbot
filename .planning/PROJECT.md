# Lucien Bot

## What This Is

Telegram bot gamificado para la comunidad de Señorita Kinky (Diana Hernández). Gestiona suscripciones VIP, canales de contenido, un sistema de gamificación con besitos, misiones, tienda virtual, promociones y narrativa interactiva con arquetipos de personajes.

## Core Value

Crear una experiencia premium y gamificada que incentiva el compromiso de la comunidad con Diana a través de un sistema de recompensas, acceso exclusivo VIP y narrativa inmersiva.

## Requirements

### Validated

- ✓ **Sistema VIP completo** — Tokens, tarifas, suscripciones, expiración automática — Fase 3
- ✓ **Gestión de canales** — Canal Free con aprobación automática y canal VIP con acceso por suscripción — Fase 2
- ✓ **Gamificación (Besitos)** — Sistema de besitos, hugs, regalos diarios, balances — Fase 4
- ✓ **Sistema de Misiones** — Misiones activas, seguimiento de progreso, recompensas — Fase 5
- ✓ **Tienda Virtual** — Paquetes de besitos, compra, entrega de contenido — Fase 6
- ✓ **Promociones** — Códigos promocionales con límites y descuentos — Fase 6
- ✓ **Sistema de Narrativa** — Historias interactivas con arquetipos, opciones de usuario — Fase 6
- ✓ **Panel de Administración** — Custodios pueden gestionar todos los dominios — Fases 3-6
- ✓ **Migraciones Alembic** — Sistema de migraciones de esquema con Alembic, baseline migration, Railway integration — Fase 07.1
- ✓ **Infraestructura de Testing** — Tests unitarios e integración con pytest, cobertura 70%, fixtures completos — Fase 8
- ✓ **Race Condition Protection** — SELECT FOR UPDATE en token redemption y operaciones de balance — Fase 8
- ✓ **Session Management** — Context managers reemplazan __del__, startup check para suscripciones expiradas — Fase 8
- ✓ **Rate Limiting (SEC-01)** — In-memory sliding window rate limiter, blocks after 5 actions per 60s — Fase 9
- ✓ **FSM Persistente (SEC-02)** — RedisStorage con graceful MemoryStorage fallback — Fase 9
- ✓ **Backup Automatizado (BACK-01)** — Script para SQLite y PostgreSQL con retention cleanup — Fase 9

### Active

- [ ] **VIP Invite Links Dinámicos** — Generar links de invitación de un solo uso para el canal VIP en lugar de links estáticos — mejora de Fase 6

### Out of Scope

- **App móvil nativa** — El bot es la plataforma principal, no hay planes de app
- **Multi-idioma** — Todos los mensajes en español únicamente
- **Copias de seguridad automáticas** — ✓ Resuelto en Fase 9 (scripts/backup_db.py)
- **Webhooks** — Long polling es suficiente para la escala actual

## Context

**Comunidad:** Señorita Kinky (Diana Hernández) — creadora de contenido
**Usuarios:** Miembros de la comunidad que pagan por acceso VIP y participan en gamificación
**Custodios (Admins):** Equipo de Diana que gestiona el bot

**Stack:** aiogram 3.4.1 + SQLAlchemy 2.0 + SQLite (production: PostgreSQL via Railway)
**Despliegue:** Railway con PostgreSQL
**Arquitectura:** handlers → services → models (capas estrictas, sin lógica en handlers)

**Tech debt conocido:**
- ~~Sin tests automatizados~~ — ✓ Resuelto en Fase 8 (80+ tests, 70% cobertura)
- Archivos de handlers grandes (>900 líneas)
- ~~Gestión de sesiones DB via `__del__`~~ — ✓ Resuelto en Fase 8 (context managers)
- MemoryStorage para FSM (estado perdido en reinicios)

**Seguridad conocida:**
- No rate limiting implementado
- ~~Tokens VIP con race condition potencial~~ — ✓ Resuelto en Fase 8 (SELECT FOR UPDATE)
- ~~Scheduler con polling cada 30s~~ — ✓ Parcialmente mitigado en Fase 8 (startup check para expiraciones)

## Constraints

- **Tech stack**: Python 3.12+, aiogram 3.x, SQLAlchemy 2.0 — no cambiar sin razón
- **Arquitectura**: Capas handlers/services/models estrictas — sin lógica de negocio en handlers
- **Voz de Lucien**: Siempre en 3ra persona, elegante y misterioso, "Diana" como figura central
- **DB**: SQLite local / PostgreSQL en Railway — compatible SQLAlchemy
- **Tests**: ~80 tests, 70% cobertura services/ — pytest + pytest-asyncio

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| aiogram 3.x (no v4) | v4 en desarrollo, rompería todo | ✓ Good |
| SQLite → PostgreSQL en Railway | SQLite no escala con writes concurrentes | ✓ Good |
| RedisStorage for FSM persistence | Redis already needed for production, RedisStorage available in aiogram | ✓ Good |
| In-memory sliding window rate limiter | No external deps needed for single-instance deployment | ✓ Good |
| Invite links estáticos para VIP | Simplicidad operativa | ⚠️ Revisit (limitación: un link compartido = varios usan) |
| Scheduler con polling 30s | Simple de implementar | ⚠️ Revisit (puede perder expiraciones) |
| python-dotenv para config | Simple, sin dependencias extra | ✓ Good |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-30 after initialization from codebase analysis*
