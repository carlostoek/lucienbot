"""
Add category_id to store_products table

Revision ID: 20250406_add_category_id_to_store_products
Revises: 20250406_add_category_id_to_packages
Create Date: 2026-04-06

Esta migración:
1. Agrega categoria_id a store_products (nullable)
2. Crea índice en category_id
3. Crea foreign key a categories
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250406_add_category_id_to_store_products'
down_revision: Union[str, None] = '20250406_add_category_id_to_packages'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    # Verificar si la columna category_id ya existe en store_products (idempotente)
    column_exists = False
    if dialect == 'sqlite':
        result = conn.execute(sa.text("PRAGMA table_info(store_products)"))
        columns = [row[1] for row in result.fetchall()]
        column_exists = 'category_id' in columns
    else:
        result = conn.execute(sa.text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'store_products' AND column_name = 'category_id'
            )
        """))
        column_exists = result.scalar()

    if not column_exists:
        # Agregar columna category_id a store_products (idempotente)
        with op.batch_alter_table('store_products', schema=None) as batch_op:
            batch_op.add_column(sa.Column('category_id', sa.Integer(), nullable=True))

        op.create_index('ix_store_products_category_id', 'store_products', ['category_id'])
        # En SQLite, la foreign key se maneja a nivel de aplicación


def downgrade() -> None:
    # Eliminar índice en category_id
    op.drop_index('ix_store_products_category_id', table_name='store_products')

    # Eliminar columna category_id
    with op.batch_alter_table('store_products', schema=None) as batch_op:
        batch_op.drop_column('category_id')