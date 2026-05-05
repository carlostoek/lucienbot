"""upgrade besitos and broadcast_reactions columns to BigInteger

Revision ID: 287e36271be4
Revises: 9fab8787057e
Create Date: 2026-04-03 01:04:44.829945

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '287e36271be4'
down_revision: Union[str, None] = '9fab8787057e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade INTEGER columns to BIGINT for besitos system.

    SQLite no soporta ALTER COLUMN TYPE directamente, por eso usamos
    el patrón de recrear tabla con los tipos correctos.
    """
    conn = op.get_bind()
    dialect = conn.dialect.name

    if dialect == 'sqlite':
        # =========================================================
        # besito_balances: cambiar balance, total_earned, total_spent
        # =========================================================
        op.execute("PRAGMA foreign_keys=OFF")

        # Crear tabla temporal con tipos correctos
        op.execute("""
            CREATE TABLE _besito_balances_new (
                id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                balance INTEGER NOT NULL,
                total_earned INTEGER NOT NULL,
                total_spent INTEGER NOT NULL,
                updated_at TIMESTAMP,
                created_at TIMESTAMP,
                PRIMARY KEY (id),
                UNIQUE (user_id)
            )
        """)

        # Copiar datos
        op.execute("""
            INSERT INTO _besito_balances_new (id, user_id, balance, total_earned, total_spent, updated_at, created_at)
            SELECT id, user_id, balance, total_earned, total_spent, updated_at, created_at FROM besito_balances
        """)

        # Reemplazar tabla
        op.execute("DROP TABLE besito_balances")
        op.execute("ALTER TABLE _besito_balances_new RENAME TO besito_balances")

        # Recrear índices
        op.execute("CREATE INDEX ix_besito_balances_id ON besito_balances (id)")
        op.execute("CREATE UNIQUE INDEX ix_besito_balances_user_id ON besito_balances (user_id)")

        # =========================================================
        # besito_transactions: cambiar amount
        # =========================================================
        op.execute("""
            CREATE TABLE _besito_transactions_new (
                id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                type VARCHAR(10) NOT NULL,
                source VARCHAR(20) NOT NULL,
                description VARCHAR(255),
                reference_id INTEGER,
                created_at TIMESTAMP,
                PRIMARY KEY (id),
                FOREIGN KEY (user_id) REFERENCES besito_balances (user_id)
            )
        """)

        op.execute("""
            INSERT INTO _besito_transactions_new (id, user_id, amount, type, source, description, reference_id, created_at)
            SELECT id, user_id, amount, type, source, description, reference_id, created_at FROM besito_transactions
        """)

        op.execute("DROP TABLE besito_transactions")
        op.execute("ALTER TABLE _besito_transactions_new RENAME TO besito_transactions")

        op.execute("CREATE INDEX ix_besito_transactions_id ON besito_transactions (id)")
        op.execute("CREATE INDEX ix_besito_transactions_user_id ON besito_transactions (user_id)")

        # =========================================================
        # broadcast_reactions: cambiar besitos_awarded
        # =========================================================
        op.execute("""
            CREATE TABLE _broadcast_reactions_new (
                id INTEGER NOT NULL,
                broadcast_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username VARCHAR(100),
                reaction_emoji_id INTEGER NOT NULL,
                besitos_awarded INTEGER NOT NULL,
                created_at TIMESTAMP,
                PRIMARY KEY (id),
                FOREIGN KEY (broadcast_id) REFERENCES broadcast_messages (id),
                FOREIGN KEY (reaction_emoji_id) REFERENCES reaction_emojis (id)
            )
        """)

        op.execute("""
            INSERT INTO _broadcast_reactions_new (id, broadcast_id, user_id, username, reaction_emoji_id, besitos_awarded, created_at)
            SELECT id, broadcast_id, user_id, username, reaction_emoji_id, besitos_awarded, created_at FROM broadcast_reactions
        """)

        op.execute("DROP TABLE broadcast_reactions")
        op.execute("ALTER TABLE _broadcast_reactions_new RENAME TO broadcast_reactions")

        op.execute("CREATE INDEX ix_broadcast_reactions_id ON broadcast_reactions (id)")
        op.execute("CREATE INDEX ix_broadcast_reactions_user_id ON broadcast_reactions (user_id)")
        op.execute("CREATE INDEX ix_broadcast_reactions_broadcast_id ON broadcast_reactions (broadcast_id)")

        op.execute("PRAGMA foreign_keys=ON")

    else:
        # PostgreSQL: usa alter_column estándar
        op.alter_column('besito_balances', 'balance',
                   existing_type=sa.INTEGER(),
                   type_=sa.BigInteger(),
                   existing_nullable=False)
        op.alter_column('besito_balances', 'total_earned',
                   existing_type=sa.INTEGER(),
                   type_=sa.BigInteger(),
                   existing_nullable=False)
        op.alter_column('besito_balances', 'total_spent',
                   existing_type=sa.INTEGER(),
                   type_=sa.BigInteger(),
                   existing_nullable=False)
        op.alter_column('besito_transactions', 'amount',
                   existing_type=sa.INTEGER(),
                   type_=sa.BigInteger(),
                   existing_nullable=False)
        op.alter_column('broadcast_reactions', 'besitos_awarded',
                   existing_type=sa.INTEGER(),
                   type_=sa.BigInteger(),
                   existing_nullable=False)


def downgrade() -> None:
    """Downgrade BIGINT columns back to INTEGER.

    SQLite: recrear tablas con tipos INTEGER.
    """
    conn = op.get_bind()
    dialect = conn.dialect.name

    if dialect == 'sqlite':
        op.execute("PRAGMA foreign_keys=OFF")

        # besito_balances
        op.execute("""
            CREATE TABLE _besito_balances_new (
                id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                balance INTEGER NOT NULL,
                total_earned INTEGER NOT NULL,
                total_spent INTEGER NOT NULL,
                updated_at TIMESTAMP,
                created_at TIMESTAMP,
                PRIMARY KEY (id),
                UNIQUE (user_id)
            )
        """)
        op.execute("""
            INSERT INTO _besito_balances_new (id, user_id, balance, total_earned, total_spent, updated_at, created_at)
            SELECT id, user_id, balance, total_earned, total_spent, updated_at, created_at FROM besito_balances
        """)
        op.execute("DROP TABLE besito_balances")
        op.execute("ALTER TABLE _besito_balances_new RENAME TO besito_balances")
        op.execute("CREATE INDEX ix_besito_balances_id ON besito_balances (id)")
        op.execute("CREATE UNIQUE INDEX ix_besito_balances_user_id ON besito_balances (user_id)")

        # besito_transactions
        op.execute("""
            CREATE TABLE _besito_transactions_new (
                id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                type VARCHAR(10) NOT NULL,
                source VARCHAR(20) NOT NULL,
                description VARCHAR(255),
                reference_id INTEGER,
                created_at TIMESTAMP,
                PRIMARY KEY (id),
                FOREIGN KEY (user_id) REFERENCES besito_balances (user_id)
            )
        """)
        op.execute("""
            INSERT INTO _besito_transactions_new (id, user_id, amount, type, source, description, reference_id, created_at)
            SELECT id, user_id, amount, type, source, description, reference_id, created_at FROM besito_transactions
        """)
        op.execute("DROP TABLE besito_transactions")
        op.execute("ALTER TABLE _besito_transactions_new RENAME TO besito_transactions")
        op.execute("CREATE INDEX ix_besito_transactions_id ON besito_transactions (id)")
        op.execute("CREATE INDEX ix_besito_transactions_user_id ON besito_transactions (user_id)")

        # broadcast_reactions
        op.execute("""
            CREATE TABLE _broadcast_reactions_new (
                id INTEGER NOT NULL,
                broadcast_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username VARCHAR(100),
                reaction_emoji_id INTEGER NOT NULL,
                besitos_awarded INTEGER NOT NULL,
                created_at TIMESTAMP,
                PRIMARY KEY (id),
                FOREIGN KEY (broadcast_id) REFERENCES broadcast_messages (id),
                FOREIGN KEY (reaction_emoji_id) REFERENCES reaction_emojis (id)
            )
        """)
        op.execute("""
            INSERT INTO _broadcast_reactions_new (id, broadcast_id, user_id, username, reaction_emoji_id, besitos_awarded, created_at)
            SELECT id, broadcast_id, user_id, username, reaction_emoji_id, besitos_awarded, created_at FROM broadcast_reactions
        """)
        op.execute("DROP TABLE broadcast_reactions")
        op.execute("ALTER TABLE _broadcast_reactions_new RENAME TO broadcast_reactions")
        op.execute("CREATE INDEX ix_broadcast_reactions_id ON broadcast_reactions (id)")
        op.execute("CREATE INDEX ix_broadcast_reactions_user_id ON broadcast_reactions (user_id)")
        op.execute("CREATE INDEX ix_broadcast_reactions_broadcast_id ON broadcast_reactions (broadcast_id)")

        op.execute("PRAGMA foreign_keys=ON")

    else:
        # PostgreSQL
        op.alter_column('broadcast_reactions', 'besitos_awarded',
                   existing_type=sa.BigInteger(),
                   type_=sa.INTEGER(),
                   existing_nullable=False)
        op.alter_column('besito_transactions', 'amount',
                   existing_type=sa.BigInteger(),
                   type_=sa.INTEGER(),
                   existing_nullable=False)
        op.alter_column('besito_balances', 'total_spent',
                   existing_type=sa.BigInteger(),
                   type_=sa.INTEGER(),
                   existing_nullable=False)
        op.alter_column('besito_balances', 'total_earned',
                   existing_type=sa.BigInteger(),
                   type_=sa.INTEGER(),
                   existing_nullable=False)
        op.alter_column('besito_balances', 'balance',
                   existing_type=sa.BigInteger(),
                   type_=sa.INTEGER(),
                   existing_nullable=False)