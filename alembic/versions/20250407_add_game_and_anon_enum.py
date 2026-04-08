"""Add GAME and ANONYMOUS_MESSAGE to transaction_source enum

Revision ID: 20250407_add_game_and_anon_enum
Revises: 20250407_add_unique_to_broadcast_reactions
Create Date: 2026-04-07 12:00:00.000000

---
PROBLEM THIS SOLVES:
- GAME and ANONYMOUS_MESSAGE values were used in production but never
  properly migrated via Alembic. They existed because someone ran
  manual ALTER TYPE commands in PostgreSQL.
- Fresh alembic upgrade head on a new database would FAIL when
  inserting transactions with source GAME or ANONYMOUS_MESSAGE.
- The previous migration 20250406_add_trivia_to_transaction_source_enum
  listed these values in EXISTING_VALUES but they were never added.

ENUM VALUES STATUS (complete):
- REACTION: baseline (e8de5494e5b6)
- DAILY_GIFT: baseline
- MISSION: baseline
- PURCHASE: baseline
- ADMIN: baseline
- ANONYMOUS_MESSAGE: this migration
- GAME: this migration
- TRIVIA: 20250406_add_trivia_to_transaction_source_enum
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250407_add_game_and_anon_enum'
down_revision: Union[str, None] = '20250407_add_unique_to_broadcast_reactions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Enum name constant
ENUM_NAME = 'transactionsource'
TABLE_NAME = 'besito_transactions'
COLUMN_NAME = 'source'

# New values to add (must be uppercase for PostgreSQL)
NEW_VALUES = ['ANONYMOUS_MESSAGE', 'GAME']


def upgrade() -> None:
    """Add ANONYMOUS_MESSAGE and GAME values to transactionsource enum.

    These values were used in production but never properly migrated.
    Uses IF NOT EXISTS to make it idempotent (safe to re-run).

    ANONYMOUS_MESSAGE: Mensaje anónimo VIP enviado a Diana
    GAME: Victoria en minijuegos (dados)
    """
    dialect = op.get_context().dialect.name

    if dialect == 'postgresql':
        for value in NEW_VALUES:
            op.execute(f"ALTER TYPE {ENUM_NAME} ADD VALUE IF NOT EXISTS '{value}'")
    else:
        # SQLite: No action needed - enums are stored as TEXT
        # The application layer handles enum validation via SQLAlchemy
        pass


def downgrade() -> None:
    """Remove GAME and ANONYMOUS_MESSAGE values.

    PostgreSQL does NOT support removing enum values. This is a fundamental
    limitation of PostgreSQL enums - once added, they cannot be dropped.

    This downgrade will fail if any rows use these values.
    Manual intervention required: update/remove affected rows first.
    """
    dialect = op.get_context().dialect.name

    if dialect == 'postgresql':
        for value in NEW_VALUES:
            result = op.get_bind().execute(
                sa.text(f"""
                    SELECT COUNT(*) FROM {TABLE_NAME}
                    WHERE {COLUMN_NAME} = :value
                """),
                {"value": value}
            ).scalar()

            if result > 0:
                raise RuntimeError(
                    f"Cannot downgrade: {result} transaction(s) exist with "
                    f"source='{value}'. Update or delete these records first, "
                    f"then re-run alembic downgrade."
                )

        # Even if no rows use the values, PostgreSQL doesn't support DROP VALUE
        # The enum will retain these values as allowed (but unused)
        raise NotImplementedError(
            "PostgreSQL does not support removing enum values. "
            "The enum will keep ANONYMOUS_MESSAGE and GAME as allowed values "
            "even after this downgrade. This is a PostgreSQL limitation."
        )
    else:
        # SQLite: No action needed
        pass
