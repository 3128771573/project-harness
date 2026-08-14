"""reports 增加 sender_uid（举报即记录被举报消息发送者，消息删除后仍可封禁）

Revision ID: c1d2e3f4a5b6
Revises: b7c8d9e0f1a2
Create Date: 2026-08-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, None] = 'b7c8d9e0f1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('reports', sa.Column('sender_uid', sa.String(length=36), nullable=True))
    op.create_index('ix_reports_sender_uid', 'reports', ['sender_uid'])


def downgrade() -> None:
    op.drop_index('ix_reports_sender_uid', table_name='reports')
    op.drop_column('reports', 'sender_uid')
