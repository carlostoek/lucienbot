"""Add question_set_id to trivia_promotion_configs

Revision ID: add_qs_to_trivia_promotion_config
Revises: 205ae3e4b36a
Create Date: 2026-05-03 20:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_qs_to_trivia_promotion_config'
down_revision: Union[str, None] = '205ae3e4b36a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    if dialect == 'sqlite':
        result = conn.execute(sa.text("PRAGMA table_info(trivia_promotion_configs)"))
        columns = [row[1] for row in result.fetchall()]
        column_exists = 'question_set_id' in columns
    else:
        result = conn.execute(sa.text("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'trivia_promotion_configs' AND column_name = 'question_set_id')"))
        column_exists = result.scalar()

    if not column_exists:
        with op.batch_alter_table('trivia_promotion_configs', schema=None) as batch_op:
            batch_op.add_column(sa.Column('question_set_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('trivia_promotion_configs', schema=None) as batch_op:
        batch_op.drop_column('question_set_id')