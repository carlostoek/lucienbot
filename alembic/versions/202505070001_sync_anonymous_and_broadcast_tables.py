"""Sync anonymous_messages and broadcast_columns tables

Revision ID: 202505070001
Revises: 202505070000
Create Date: 2026-05-07

This migration adds tables and columns that were missing from the local
development DB due to migration chain issues.

Tables/Columns added idempotently:
- anonymous_messages table (VIP anonymous messaging)
- broadcast_messages.selected_emoji_ids
- user_mission_progress.last_reference_id
- broadcast_reactions unique constraint (PostgreSQL only)

Compatible with: SQLite, PostgreSQL
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '202505070001'
down_revision: Union[str, None] = '202505070000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    # ========================================
    # Create anonymous_messages table (idempotente)
    # ========================================
    if dialect == 'sqlite':
        result = conn.execute(sa.text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='anonymous_messages'"
        ))
        table_exists = result.fetchone() is not None
    else:
        result = conn.execute(sa.text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'anonymous_messages')"
        ))
        table_exists = result.scalar()

    if not table_exists:
        op.create_table(
            'anonymous_messages',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('sender_id', sa.BigInteger(), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('status', sa.Enum('UNREAD', 'READ', 'REPLIED', name='anonymousmessagestatus', create_type=False), nullable=True),
            sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('read_by', sa.BigInteger(), nullable=True),
            sa.Column('admin_reply', sa.Text(), nullable=True),
            sa.Column('replied_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.ForeignKeyConstraint(['sender_id'], ['users.telegram_id']),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_anonymous_messages_id', 'anonymous_messages', ['id'])
        op.create_index('ix_anonymous_messages_sender_id', 'anonymous_messages', ['sender_id'])

    # ========================================
    # Add selected_emoji_ids to broadcast_messages (idempotente)
    # ========================================
    if dialect == 'sqlite':
        result = conn.execute(sa.text("PRAGMA table_info(broadcast_messages)"))
        columns = [row[1] for row in result.fetchall()]
        column_exists = 'selected_emoji_ids' in columns
    else:
        result = conn.execute(sa.text(
            "SELECT EXISTS (SELECT FROM information_schema.columns "
            "WHERE table_name = 'broadcast_messages' AND column_name = 'selected_emoji_ids')"
        ))
        column_exists = result.scalar()

    if not column_exists:
        op.add_column('broadcast_messages', sa.Column('selected_emoji_ids', sa.String(length=200), nullable=True))

    # ========================================
    # Add last_reference_id to user_mission_progress (idempotente)
    # ========================================
    if dialect == 'sqlite':
        result = conn.execute(sa.text("PRAGMA table_info(user_mission_progress)"))
        columns = [row[1] for row in result.fetchall()]
        column_exists = 'last_reference_id' in columns
    else:
        result = conn.execute(sa.text(
            "SELECT EXISTS (SELECT FROM information_schema.columns "
            "WHERE table_name = 'user_mission_progress' AND column_name = 'last_reference_id')"
        ))
        column_exists = result.scalar()

    if not column_exists:
        with op.batch_alter_table('user_mission_progress', schema=None) as batch_op:
            batch_op.add_column(sa.Column('last_reference_id', sa.Integer(), nullable=True))

    # ========================================
    # Add unique constraint to broadcast_reactions (PostgreSQL only)
    # ========================================
    if dialect == 'postgresql':
        try:
            op.create_unique_constraint(
                'uq_broadcast_user_reaction',
                'broadcast_reactions',
                ['broadcast_id', 'user_id']
            )
        except Exception:
            pass  # Constraint already exists


def downgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    # Remove unique constraint from broadcast_reactions (PostgreSQL only)
    if dialect == 'postgresql':
        try:
            with op.batch_alter_table('broadcast_reactions', schema=None) as batch_op:
                batch_op.drop_constraint('uq_broadcast_user_reaction', type_='unique')
        except Exception:
            pass

    # Remove last_reference_id from user_mission_progress
    if dialect == 'sqlite':
        result = conn.execute(sa.text("PRAGMA table_info(user_mission_progress)"))
        columns = [row[1] for row in result.fetchall()]
        if 'last_reference_id' in columns:
            with op.batch_alter_table('user_mission_progress', schema=None) as batch_op:
                batch_op.drop_column('last_reference_id')
    else:
        with op.batch_alter_table('user_mission_progress', schema=None) as batch_op:
            batch_op.drop_column('last_reference_id')

    # Remove selected_emoji_ids from broadcast_messages
    op.drop_column('broadcast_messages', 'selected_emoji_ids')

    # Drop anonymous_messages table
    if dialect == 'sqlite':
        result = conn.execute(sa.text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='anonymous_messages'"
        ))
        if result.fetchone():
            op.drop_index('ix_anonymous_messages_sender_id', table_name='anonymous_messages')
            op.drop_index('ix_anonymous_messages_id', table_name='anonymous_messages')
            op.drop_table('anonymous_messages')
    else:
        op.drop_table('anonymous_messages')
