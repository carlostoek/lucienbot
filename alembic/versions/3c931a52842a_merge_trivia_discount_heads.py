"""merge trivia discount heads

Revision ID: 3c931a52842a
Revises: 20250407_add_game_and_anon_enum, 20260508_add_trivia_discount_models
Create Date: 2026-05-08 23:26:49.713118

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c931a52842a'
down_revision: Union[str, None] = ('20250407_add_game_and_anon_enum', '20260508_add_trivia_discount_models')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
