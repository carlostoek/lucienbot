"""Add question_sets table

Revision ID: 205ae3e4b36a
Revises: 20250418_trivia_auto_reset
Create Date: 2026-05-01 16:50:18.330684

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '205ae3e4b36a'
down_revision: Union[str, None] = '20250418_trivia_auto_reset'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    # Create question_sets table (idempotente)
    if dialect == 'sqlite':
        result = conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name='question_sets'"))
        table_exists = result.fetchone() is not None
    else:
        result = conn.execute(sa.text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'question_sets')"))
        table_exists = result.scalar()

    if not table_exists:
        op.create_table('question_sets',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(200), nullable=False, unique=True),
            sa.Column('file_path', sa.String(500), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('is_active', sa.Boolean(), default=False),
            sa.Column('is_override', sa.Boolean(), default=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name')
        )

    # Add question_set_id to promotions (idempotente)
    if dialect == 'sqlite':
        result = conn.execute(sa.text("PRAGMA table_info(promotions)"))
        columns = [row[1] for row in result.fetchall()]
        column_exists = 'question_set_id' in columns
    else:
        result = conn.execute(sa.text("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'promotions' AND column_name = 'question_set_id')"))
        column_exists = result.scalar()

    if not column_exists:
        with op.batch_alter_table('promotions', schema=None) as batch_op:
            batch_op.add_column(sa.Column('question_set_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('promotions', schema=None) as batch_op:
        batch_op.drop_column('question_set_id')
    op.drop_table('question_sets')
