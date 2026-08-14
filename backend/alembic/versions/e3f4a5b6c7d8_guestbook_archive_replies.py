"""留言板升级：档案号 + 状态 + 回复时间线 + 快捷模板

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-08-15

"""
from collections import Counter
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3f4a5b6c7d8'
down_revision: Union[str, None] = 'd2e3f4a5b6c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('messages', sa.Column('archive_no', sa.String(length=20), nullable=True))
    op.create_index('ix_messages_archive_no', 'messages', ['archive_no'], unique=True)
    op.add_column('messages', sa.Column('status', sa.String(length=12), server_default=sa.text("'pending'"), nullable=False))

    op.create_table(
        'guestbook_replies',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('guestbook_id', sa.String(length=36), sa.ForeignKey('messages.id'), nullable=False),
        sa.Column('sender_type', sa.String(length=8), nullable=False),
        sa.Column('sender_name', sa.String(length=64), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_guestbook_replies_guestbook_id', 'guestbook_replies', ['guestbook_id'])
    op.create_table(
        'guestbook_templates',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 回填历史留言档案号（按创建时间，日期 + 当日序号）
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, created_time FROM messages ORDER BY created_time ASC")).fetchall()
    day_count: Counter = Counter()
    for rid, ct in rows:
        d = ct.strftime("%Y%m%d") if ct else "19700101"
        day_count[d] += 1
        conn.execute(
            sa.text("UPDATE messages SET archive_no=:a WHERE id=:i"),
            {"a": f"GB-{d}-{day_count[d]:03d}", "i": rid},
        )


def downgrade() -> None:
    op.drop_table('guestbook_templates')
    op.drop_index('ix_guestbook_replies_guestbook_id', table_name='guestbook_replies')
    op.drop_table('guestbook_replies')
    op.drop_column('messages', 'status')
    op.drop_index('ix_messages_archive_no', table_name='messages')
    op.drop_column('messages', 'archive_no')
