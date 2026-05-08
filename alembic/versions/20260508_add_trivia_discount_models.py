"""Add trivia discount models (8 tables + 3 enums)

Revision ID: 20260508_add_trivia_discount_models
Revises: 3f20074a2dd3
Create Date: 2026-05-08 12:00:00.000000

---
PHASE 16: Trivia Discount System

Tables created:
- trivia_promotion_configs: Configuracion de promociones trivia
- tiers: Niveles de descuento con pool de codigos
- discount_codes: Codigos de descuento individuales
- user_streaks: Racha activa por usuario
- trivia_game_records: Registro de partidas trivia (separado de game_records)
- question_sets: Grupos de preguntas con tematica
- questions: Preguntas individuales de trivia
- trivia_config: Configuracion global singleton

Enums created:
- discountcodestatus: AVAILABLE, CLAIMED, USED, CANCELLED, EXPIRED
- gameresult: WON, LOST, ABANDONED, EXPIRED
- difficulty: EASY, MEDIUM, HARD
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260508_add_trivia_discount_models'
down_revision: Union[str, None] = '3f20074a2dd3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ============================================================
    # Create enums (for PostgreSQL)
    # ============================================================
    dialect = op.get_context().dialect.name

    if dialect == 'postgresql':
        # discountcodestatus enum
        op.execute("""
            DO $$ BEGIN
                CREATE TYPE discountcodestatus AS ENUM (
                    'available', 'claimed', 'used', 'cancelled', 'expired'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """)
        # gameresult enum
        op.execute("""
            DO $$ BEGIN
                CREATE TYPE gameresult AS ENUM (
                    'won', 'lost', 'abandoned', 'expired'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """)
        # difficulty enum
        op.execute("""
            DO $$ BEGIN
                CREATE TYPE difficulty AS ENUM (
                    'easy', 'medium', 'hard'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """)

    # ============================================================
    # Create tables
    # ============================================================

    # question_sets table (no FK dependencies first)
    op.create_table('question_sets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('file_path', sa.String(length=255), nullable=True),
        sa.Column('is_override', sa.Boolean(), nullable=True, default=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_question_sets_id', 'question_sets', ['id'])

    # questions table
    op.create_table('questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('question_set_id', sa.Integer(), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('option_a', sa.String(length=255), nullable=False),
        sa.Column('option_b', sa.String(length=255), nullable=False),
        sa.Column('option_c', sa.String(length=255), nullable=False),
        sa.Column('option_d', sa.String(length=255), nullable=False),
        sa.Column('correct_option', sa.String(length=1), nullable=False),
        sa.Column('difficulty', sa.Enum('easy', 'medium', 'hard', name='difficulty', create_type=False), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['question_set_id'], ['question_sets.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_questions_id', 'questions', ['id'])

    # trivia_promotion_configs table
    op.create_table('trivia_promotion_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_days', sa.Integer(), nullable=True, default=7),
        sa.Column('auto_reset', sa.Boolean(), nullable=True, default=True),
        sa.Column('question_set_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['question_set_id'], ['question_sets.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_trivia_promotion_configs_id', 'trivia_promotion_configs', ['id'])

    # tiers table
    op.create_table('tiers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('promotion_config_id', sa.Integer(), nullable=False),
        sa.Column('tier_number', sa.Integer(), nullable=False),
        sa.Column('streak_threshold', sa.Integer(), nullable=False),
        sa.Column('discount_percentage', sa.Integer(), nullable=False),
        sa.Column('max_codes', sa.Integer(), nullable=False),
        sa.Column('codes_generated', sa.Integer(), nullable=True, default=0),
        sa.ForeignKeyConstraint(['promotion_config_id'], ['trivia_promotion_configs.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tiers_id', 'tiers', ['id'])

    # discount_codes table
    op.create_table('discount_codes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('tier_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('status', sa.Enum('available', 'claimed', 'used', 'cancelled', 'expired', name='discountcodestatus', create_type=False), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('claimed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tier_id'], ['tiers.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index('ix_discount_codes_id', 'discount_codes', ['id'])
    op.create_index('ix_discount_codes_code', 'discount_codes', ['code'])

    # user_streaks table
    op.create_table('user_streaks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('promotion_config_id', sa.Integer(), nullable=True),
        sa.Column('current_streak', sa.Integer(), nullable=True, default=0),
        sa.Column('active_tier_id', sa.Integer(), nullable=True),
        sa.Column('active_code_id', sa.Integer(), nullable=True),
        sa.Column('streak_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_answered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.ForeignKeyConstraint(['promotion_config_id'], ['trivia_promotion_configs.id']),
        sa.ForeignKeyConstraint(['active_tier_id'], ['tiers.id']),
        sa.ForeignKeyConstraint(['active_code_id'], ['discount_codes.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_streaks_id', 'user_streaks', ['id'])
    op.create_index('ix_user_streaks_user_id', 'user_streaks', ['user_id'])

    # trivia_game_records table
    op.create_table('trivia_game_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('promotion_config_id', sa.Integer(), nullable=True),
        sa.Column('discount_code_id', sa.Integer(), nullable=True),
        sa.Column('game_type', sa.String(length=32), nullable=False),
        sa.Column('questions_answered', sa.Integer(), nullable=True, default=0),
        sa.Column('correct_answers', sa.Integer(), nullable=True, default=0),
        sa.Column('final_streak', sa.Integer(), nullable=True, default=0),
        sa.Column('result', sa.Enum('won', 'lost', 'abandoned', 'expired', name='gameresult', create_type=False), nullable=False),
        sa.Column('played_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['promotion_config_id'], ['trivia_promotion_configs.id']),
        sa.ForeignKeyConstraint(['discount_code_id'], ['discount_codes.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_trivia_game_records_id', 'trivia_game_records', ['id'])
    op.create_index('ix_trivia_game_records_user_id', 'trivia_game_records', ['user_id'])

    # trivia_config table (singleton)
    op.create_table('trivia_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('free_daily_limit', sa.Integer(), nullable=True, default=7),
        sa.Column('vip_daily_limit', sa.Integer(), nullable=True, default=15),
        sa.Column('vip_exclusive_daily_limit', sa.Integer(), nullable=True, default=5),
        sa.Column('streak_timeout_minutes', sa.Integer(), nullable=True, default=2),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_trivia_config_id', 'trivia_config', ['id'])


def downgrade() -> None:
    """Drop all trivia discount tables and enums.

    Note: PostgreSQL does not support removing enum values.
    The enums will remain in the database as unused types.
    """
    dialect = op.get_context().dialect.name

    # Drop tables in reverse dependency order
    op.drop_table('trivia_config')
    op.drop_table('trivia_game_records')
    op.drop_table('user_streaks')
    op.drop_table('discount_codes')
    op.drop_table('tiers')
    op.drop_table('trivia_promotion_configs')
    op.drop_table('questions')
    op.drop_table('question_sets')

    if dialect == 'postgresql':
        # PostgreSQL does not support DROP TYPE for enum types
        # Enums will remain but become unused
        pass
