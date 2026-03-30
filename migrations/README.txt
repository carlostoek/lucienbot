Migraciones de esquema
======================

A partir de Phase 07.1, todas las migraciones de esquema se gestionan con Alembic.

Directorio: ../alembic/

Comandos principales:
  alembic revision --autogenerate -m "descripción"
  alembic upgrade head
  alembic history
  alembic current

Este directorio (migrations/) contiene migraciones standalone históricas.
El script add_invite_link_to_channels.py fue ejecutado manualmente y está archivado en archive/.
