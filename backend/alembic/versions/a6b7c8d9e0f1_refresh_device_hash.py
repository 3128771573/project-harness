"""RefreshToken 增加 device_hash（设备绑定）

Revision ID: a6b7c8d9e0f1
Revises: f4a5b6c7d8e9
Create Date: 2026-08-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6b7c8d9e0f1'
down_revision: Union[str, None] = 'f4a5b6c7d8e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('refresh_tokens', sa.Column('device_hash', sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column('refresh_tokens', 'device_hash')
