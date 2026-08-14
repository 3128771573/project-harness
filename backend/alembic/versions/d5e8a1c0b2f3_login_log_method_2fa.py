"""login_logs 增加 method / used_2fa 列（登录方式与 2FA 标记）

Revision ID: d5e8a1c0b2f3
Revises: c3a9f2b71d4e
Create Date: 2026-08-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5e8a1c0b2f3'
down_revision: Union[str, None] = 'c3a9f2b71d4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('login_logs', sa.Column('method', sa.String(length=16), nullable=True))
    op.add_column('login_logs', sa.Column('used_2fa', sa.Boolean(), server_default=sa.text('false'), nullable=False))


def downgrade() -> None:
    op.drop_column('login_logs', 'used_2fa')
    op.drop_column('login_logs', 'method')
