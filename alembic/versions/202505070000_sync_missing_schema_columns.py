"""Sync missing schema columns from production

Revision ID: 202505070000
Revises: 73702d0a06be
Create Date: 2026-05-07

This migration adds columns and tables that were missing from the local
development DB due to migration chain issues with the ea7e3c03df29 merge point.

Tables/Columns added idempotently:
- categories table (created if not exists)
- packages.category_id (added if not exists)
- store_products.category_id (added if not exists)
- store_products.low_stock_threshold (added if not exists)
- missions.cooldown_hours (added if not exists)

Compatible with: SQLite, PostgreSQL
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '202505070000'
down_revision: Union[str, None] = '73702d0a06be'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    # ========================================
    # Create categories table (idempotente)
    # ========================================
    if dialect == 'sqlite':
        result = conn.execute(sa.text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='categories'"
        ))
        table_exists = result.fetchone() is not None
    else:
        result = conn.execute(sa.text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'categories')"
        ))
        table_exists = result.scalar()

    if not table_exists:
        op.create_table(
            'categories',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('order_index', sa.Integer(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name')
        )

    # ========================================
    # Add category_id to packages (idempotente)
    # ========================================
    if dialect == 'sqlite':
        result = conn.execute(sa.text("PRAGMA table_info(packages)"))
        columns = [row[1] for row in result.fetchall()]
        column_exists = 'category_id' in columns
    else:
        result = conn.execute(sa.text(
            "SELECT EXISTS (SELECT FROM information_schema.columns "
            "WHERE table_name = 'packages' AND column_name = 'category_id')"
        ))
        column_exists = result.scalar()

    if not column_exists:
        with op.batch_alter_table('packages', schema=None) as batch_op:
            batch_op.add_column(sa.Column('category_id', sa.Integer(), nullable=True))
        op.create_index('ix_packages_category_id', 'packages', ['category_id'])

    # ========================================
    # Add category_id to store_products (idempotente)
    # ========================================
    if dialect == 'sqlite':
        result = conn.execute(sa.text("PRAGMA table_info(store_products)"))
        columns = [row[1] for row in result.fetchall()]
        column_exists = 'category_id' in columns
    else:
        result = conn.execute(sa.text(
            "SELECT EXISTS (SELECT FROM information_schema.columns "
            "WHERE table_name = 'store_products' AND column_name = 'category_id')"
        ))
        column_exists = result.scalar()

    if not column_exists:
        with op.batch_alter_table('store_products', schema=None) as batch_op:
            batch_op.add_column(sa.Column('category_id', sa.Integer(), nullable=True))
        op.create_index('ix_store_products_category_id', 'store_products', ['category_id'])

    # ========================================
    # Add low_stock_threshold to store_products (idempotente)
    # ========================================
    if dialect == 'sqlite':
        result = conn.execute(sa.text("PRAGMA table_info(store_products)"))
        columns = [row[1] for row in result.fetchall()]
        column_exists = 'low_stock_threshold' in columns
    else:
        result = conn.execute(sa.text(
            "SELECT EXISTS (SELECT FROM information_schema.columns "
            "WHERE table_name = 'store_products' AND column_name = 'low_stock_threshold')"
        ))
        column_exists = result.scalar()

    if not column_exists:
        with op.batch_alter_table('store_products', schema=None) as batch_op:
            batch_op.add_column(sa.Column('low_stock_threshold', sa.Integer(), nullable=True))

    # ========================================
    # Add cooldown_hours to missions (idempotente)
    # ========================================
    if dialect == 'sqlite':
        result = conn.execute(sa.text("PRAGMA table_info(missions)"))
        columns = [row[1] for row in result.fetchall()]
        column_exists = 'cooldown_hours' in columns
    else:
        result = conn.execute(sa.text(
            "SELECT EXISTS (SELECT FROM information_schema.columns "
            "WHERE table_name = 'missions' AND column_name = 'cooldown_hours')"
        ))
        column_exists = result.scalar()

    if not column_exists:
        with op.batch_alter_table('missions', schema=None) as batch_op:
            batch_op.add_column(sa.Column('cooldown_hours', sa.Integer(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    # Remove cooldown_hours from missions
    if dialect == 'sqlite':
        result = conn.execute(sa.text("PRAGMA table_info(missions)"))
        columns = [row[1] for row in result.fetchall()]
        if 'cooldown_hours' in columns:
            with op.batch_alter_table('missions', schema=None) as batch_op:
                batch_op.drop_column('cooldown_hours')
    else:
        with op.batch_alter_table('missions', schema=None) as batch_op:
            batch_op.drop_column('cooldown_hours')

    # Remove low_stock_threshold from store_products
    if dialect == 'sqlite':
        result = conn.execute(sa.text("PRAGMA table_info(store_products)"))
        columns = [row[1] for row in result.fetchall()]
        if 'low_stock_threshold' in columns:
            with op.batch_alter_table('store_products', schema=None) as batch_op:
                batch_op.drop_column('low_stock_threshold')
    else:
        with op.batch_alter_table('store_products', schema=None) as batch_op:
            batch_op.drop_column('low_stock_threshold')

    # Remove category_id from store_products
    if dialect == 'sqlite':
        result = conn.execute(sa.text("PRAGMA table_info(store_products)"))
        columns = [row[1] for row in result.fetchall()]
        if 'category_id' in columns:
            op.drop_index('ix_store_products_category_id', table_name='store_products')
            with op.batch_alter_table('store_products', schema=None) as batch_op:
                batch_op.drop_column('category_id')
    else:
        op.drop_index('ix_store_products_category_id', table_name='store_products')
        with op.batch_alter_table('store_products', schema=None) as batch_op:
            batch_op.drop_column('category_id')

    # Remove category_id from packages
    if dialect == 'sqlite':
        result = conn.execute(sa.text("PRAGMA table_info(packages)"))
        columns = [row[1] for row in result.fetchall()]
        if 'category_id' in columns:
            op.drop_index('ix_packages_category_id', table_name='packages')
            with op.batch_alter_table('packages', schema=None) as batch_op:
                batch_op.drop_column('category_id')
    else:
        op.drop_index('ix_packages_category_id', table_name='packages')
        with op.batch_alter_table('packages', schema=None) as batch_op:
            batch_op.drop_column('category_id')

    # Drop categories table
    op.drop_table('categories')
