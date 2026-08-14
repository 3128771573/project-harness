"""oauth_accounts 表（GitHub OAuth 绑定）

Revision ID: c3a9f2b71d4e
Revises: 4f21a19de782
Create Date: 2026-08-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3a9f2b71d4e'
down_revision: Union[str, None] = '4f21a19de782'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'oauth_accounts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('uid', sa.String(length=36), nullable=False),
        sa.Column('provider', sa.String(length=32), nullable=False),
        sa.Column('provider_sub', sa.String(length=128), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('nickname', sa.String(length=64), nullable=True),
        sa.Column('avatar', sa.String(length=512), nullable=True),
        sa.Column('created_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['uid'], ['users.uid'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'provider_sub', name='uq_oauth_provider_sub'),
    )
    op.create_index('ix_oauth_accounts_uid', 'oauth_accounts', ['uid'])


def downgrade() -> None:
    op.drop_index('ix_oauth_accounts_uid', table_name='oauth_accounts')
    op.drop_table('oauth_accounts')
