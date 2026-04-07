"""Merge heads: add_category_id_to_store_products and add_trivia_to_transaction_source

Revision ID: ea7e3c03df29
Revises: 20250406_add_category_id_to_store_products, 20250406_add_trivia_to_transaction_source
Create Date: 2026-04-06 21:23:12.275787

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea7e3c03df29'
down_revision: Union[str, None] = ('20250406_add_category_id_to_store_products', '20250406_add_trivia_to_transaction_source')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
