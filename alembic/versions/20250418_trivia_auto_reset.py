"""Add auto_reset fields to TriviaPromotionConfig

Revision ID: 20250418_trivia_auto_reset
Revises: 20250418_trivia_duration
Create Date: 2025-04-18 12:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '20250418_trivia_auto_reset'
down_revision = '20250418_trivia_duration'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'trivia_promotion_configs',
        sa.Column('auto_reset_enabled', sa.Boolean(), nullable=True, server_default='false')
    )
    op.add_column(
        'trivia_promotion_configs',
        sa.Column('reset_count', sa.Integer(), nullable=True, server_default='0')
    )
    op.add_column(
        'trivia_promotion_configs',
        sa.Column('max_reset_cycles', sa.Integer(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('trivia_promotion_configs', 'max_reset_cycles')
    op.drop_column('trivia_promotion_configs', 'reset_count')
    op.drop_column('trivia_promotion_configs', 'auto_reset_enabled')
