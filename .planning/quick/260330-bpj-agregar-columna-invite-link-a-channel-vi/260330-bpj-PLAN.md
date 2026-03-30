---
phase: 07-vip-invite-links
plan: "01"
type: execute
wave: 1
depends_on: []
files_modified:
  - migrations/add_invite_link_to_channels.py
autonomous: true
requirements:
  - VIP-07

must_haves:
  truths:
    - "La columna invite_link existe en la tabla channels"
    - "El script de migracion es idempotente y compatible con SQLite y PostgreSQL"
    - "Todos los cambios de Phase 7 estan en un solo commit"
  artifacts:
    - path: "migrations/add_invite_link_to_channels.py"
      provides: "Script de migracion para agregar columna invite_link"
      min_lines: 30
  key_links:
    - from: "models/models.py"
      to: "migrations/add_invite_link_to_channels.py"
      via: "ALTER TABLE channels ADD COLUMN invite_link"
      pattern: "invite_link = Column.*String.*500"
    - from: "handlers/common_handlers.py"
      to: "services/vip_service.py"
      via: "vip_service.get_vip_channel()"
      pattern: "vip_channel.invite_link"
---

<objective>
Crear script de migracion Python que agrega la columna `invite_link` a la tabla `channels`, compatible con SQLite (desarrollo) y PostgreSQL (produccion en Railway). Luego hacer commit de todos los cambios pendientes.
</objective>

<context>
@models/models.py
@models/database.py
@handlers/common_handlers.py
@services/vip_service.py
@.planning/STATE.md

El modelo `Channel` en `models/models.py:68` ya tiene definido el campo:
```python
invite_link = Column(String(500), nullable=True)
```

La base de datos puede ser SQLite (`sqlite:///lucien_bot.db`) o PostgreSQL (via `DATABASE_URL` en Railway).
El motor se crea en `models/database.py:10-13` usando `bot_config.DATABASE_URL`.
El handler `handlers/common_handlers.py:71` usa `vip_channel.invite_link` como fallback cuando falla `create_chat_invite_link`.
El service `services/vip_service.py:242-247` tiene el metodo `get_vip_channel()` que retorna el canal VIP activo.

Cambios ya staged listos para commit:
- `handlers/common_handlers.py` — genera invite link con `create_chat_invite_link(member_limit=1)`
- `models/models.py` — agrega campo `invite_link` al modelo Channel
- `services/vip_service.py` — agrega metodo `get_vip_channel()`
</context>

<tasks>

<task type="auto">
  <name>Task 1: Crear directorio migrations/ y script de migracion</name>
  <files>migrations/add_invite_link_to_channels.py</files>
  <action>
Crear el directorio `migrations/` en la raiz del proyecto y el archivo `migrations/add_invite_link_to_channels.py`.

El script debe:

1. Cargar variables de entorno desde `.env` (usando `dotenv`)
2. Importar SQLAlchemy `create_engine` y detectar el dialecto desde `DATABASE_URL`
3. Obtener la lista de columnas existentes de la tabla `channels` (usando `inspect(engine).get_columns('channels')`)
4. Verificar si la columna `invite_link` ya existe para ser idempotente (no fallar si ya se ejecuto antes)
5. Si no existe, ejecutar ALTER TABLE:
   - **SQLite**: `ALTER TABLE channels ADD COLUMN invite_link VARCHAR(500)`
   - **PostgreSQL**: `ALTER TABLE channels ADD COLUMN invite_link VARCHAR(500)`
6. Usar conexiones nativas con `engine.connect()` y `text()` para ejecutar el SQL raw
7. Imprimir log claro del resultado (columna agregada / ya existia)

Notas:
- Usar `from sqlalchemy import text, inspect` para el SQL puro
- Usar batch mode para SQLite: `with engine.begin() as conn:` o `with engine.connect() as conn:`
- El script debe poder ejecutarse multiple veces sin errores (idempotente)
- No usar Alembic ni SQLAlchemy migration APIs — script standalone directo
</action>
  <verify>python migrations/add_invite_link_to_channels.py
# Debe imprimir: "Columna invite_link agregada exitosamente" o "La columna invite_link ya existe"
</verify>
  <done>Script existe en migrations/add_invite_link_to_channels.py y se ejecuta sin errores en SQLite local</done>
</task>

<task type="auto">
  <name>Task 2: Ejecutar migracion y hacer commit de todos los cambios</name>
  <files>migrations/add_invite_link_to_channels.py, handlers/common_handlers.py, models/models.py, services/vip_service.py</files>
  <action>
2a. Ejecutar la migracion:
   python migrations/add_invite_link_to_channels.py

2b. Hacer git add de todos los archivos modificados:
   git add handlers/common_handlers.py models/models.py services/vip_service.py migrations/add_invite_link_to_channels.py

2c. Crear commit con mensaje descriptivo:
   Mensaje: "feat(vip): add dynamic invite links for VIP access (VIP-07)"
   Sub-items:
   - Modelo Channel: agregar campo invite_link
   - VIPService: agregar metodo get_vip_channel()
   - Handler /start: generar invite link de un solo uso con create_chat_invite_link(member_limit=1), fallback a invite_link guardado
   - Migracion: script Python para agregar columna invite_link a channels

2d. Verificar que el commit se creo correctamente con git log.
</action>
  <verify>git log -1 --stat
# Debe mostrar todos los archivos en el commit
</verify>
  <done>Commit creado con los 4 archivos: migration script + 3 staged changes</done>
</task>

</tasks>

<verification>
- Script de migracion existe y es idempotente
- Migracion se ejecuta sin errores en SQLite local
- Todos los archivos pendientes (handler, model, service, migration) estan en un solo commit
</verification>

<success_criteria>
- `migrations/add_invite_link_to_channels.py` existe y es ejecutable
- `python migrations/add_invite_link_to_channels.py` corre sin errores
- `git log -1` muestra commit con los 4 archivos (migration + handler + model + service)
</success_criteria>

<output>
Al completar, crear `.planning/quick/260330-bpj-agregar-columna-invite-link-a-channel-vi/260330-bpj-SUMMARY.md`
</output>
