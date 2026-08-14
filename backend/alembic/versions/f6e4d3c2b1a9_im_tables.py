"""站内消息系统（IM）数据表 + users.is_bot

Revision ID: f6e4d3c2b1a9
Revises: d5e8a1c0b2f3
Create Date: 2026-08-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6e4d3c2b1a9'
down_revision: Union[str, None] = 'd5e8a1c0b2f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 机器人标记（登录拒绝 / 搜索排除 / 不可发起私信）
    op.add_column('users', sa.Column('is_bot', sa.Boolean(), server_default=sa.text('false'), nullable=False))

    op.create_table(
        'dm_conversations',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_a', sa.String(length=36), sa.ForeignKey('users.uid'), nullable=False),
        sa.Column('user_b', sa.String(length=36), sa.ForeignKey('users.uid'), nullable=False),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('user_a', 'user_b', name='uq_dm_conv_pair'),
        sa.CheckConstraint('user_a < user_b', name='ck_dm_conv_order'),
    )
    op.create_table(
        'dm_conversation_members',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('conversation_id', sa.String(length=36), sa.ForeignKey('dm_conversations.id'), nullable=False),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.uid'), nullable=False),
        sa.Column('last_read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('hidden', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('conversation_id', 'user_id', name='uq_dm_member'),
    )
    op.create_index('ix_dm_conversation_members_conversation_id', 'dm_conversation_members', ['conversation_id'])
    op.create_index('ix_dm_conversation_members_user_id', 'dm_conversation_members', ['user_id'])
    op.create_table(
        'dm_messages',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('conversation_id', sa.String(length=36), sa.ForeignKey('dm_conversations.id'), nullable=False),
        sa.Column('sender_id', sa.String(length=36), sa.ForeignKey('users.uid'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('kind', sa.String(length=16), server_default=sa.text("'text'"), nullable=False),
        sa.Column('status', sa.String(length=16), server_default=sa.text("'active'"), nullable=False),
        sa.Column('recalled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_dm_messages_conversation_id', 'dm_messages', ['conversation_id'])
    op.create_index('ix_dm_messages_sender_id', 'dm_messages', ['sender_id'])
    op.create_index('ix_dm_messages_created_time', 'dm_messages', ['created_time'])
    op.create_table(
        'group_chats',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('owner_id', sa.String(length=36), sa.ForeignKey('users.uid'), nullable=False),
        sa.Column('announcement', sa.Text(), nullable=True),
        sa.Column('max_members', sa.Integer(), server_default=sa.text('200'), nullable=False),
        sa.Column('created_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_group_chats_owner_id', 'group_chats', ['owner_id'])
    op.create_table(
        'group_members',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('group_id', sa.String(length=36), sa.ForeignKey('group_chats.id'), nullable=False),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.uid'), nullable=False),
        sa.Column('role', sa.String(length=16), server_default=sa.text("'member'"), nullable=False),
        sa.Column('last_read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('joined_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('group_id', 'user_id', name='uq_group_member'),
    )
    op.create_index('ix_group_members_group_id', 'group_members', ['group_id'])
    op.create_index('ix_group_members_user_id', 'group_members', ['user_id'])
    op.create_table(
        'group_messages',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('group_id', sa.String(length=36), sa.ForeignKey('group_chats.id'), nullable=False),
        sa.Column('sender_id', sa.String(length=36), sa.ForeignKey('users.uid'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('kind', sa.String(length=16), server_default=sa.text("'text'"), nullable=False),
        sa.Column('status', sa.String(length=16), server_default=sa.text("'active'"), nullable=False),
        sa.Column('recalled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_group_messages_group_id', 'group_messages', ['group_id'])
    op.create_index('ix_group_messages_sender_id', 'group_messages', ['sender_id'])
    op.create_index('ix_group_messages_created_time', 'group_messages', ['created_time'])
    op.create_table(
        'blocks',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('uid', sa.String(length=36), sa.ForeignKey('users.uid'), nullable=False),
        sa.Column('blocked_uid', sa.String(length=36), sa.ForeignKey('users.uid'), nullable=False),
        sa.Column('created_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('uid', 'blocked_uid', name='uq_block_pair'),
    )
    op.create_index('ix_blocks_uid', 'blocks', ['uid'])
    op.create_index('ix_blocks_blocked_uid', 'blocks', ['blocked_uid'])
    op.create_table(
        'watermark_grants',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.uid'), nullable=False),
        sa.Column('granted_by', sa.String(length=36), sa.ForeignKey('users.uid'), nullable=True),
        sa.Column('quota_type', sa.String(length=16), nullable=False),
        sa.Column('max_uses', sa.Integer(), nullable=True),
        sa.Column('used_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_watermark_grants_user_id', 'watermark_grants', ['user_id'])
    op.create_table(
        'watermark_logs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('actor_id', sa.String(length=36), sa.ForeignKey('users.uid'), nullable=False),
        sa.Column('kind', sa.String(length=16), nullable=False),
        sa.Column('input_hash', sa.String(length=64), nullable=True),
        sa.Column('matched_uid', sa.String(length=36), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('consumed', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_watermark_logs_actor_id', 'watermark_logs', ['actor_id'])
    op.create_index('ix_watermark_logs_matched_uid', 'watermark_logs', ['matched_uid'])


def downgrade() -> None:
    op.drop_index('ix_watermark_logs_matched_uid', table_name='watermark_logs')
    op.drop_index('ix_watermark_logs_actor_id', table_name='watermark_logs')
    op.drop_table('watermark_logs')
    op.drop_index('ix_watermark_grants_user_id', table_name='watermark_grants')
    op.drop_table('watermark_grants')
    op.drop_index('ix_blocks_blocked_uid', table_name='blocks')
    op.drop_index('ix_blocks_uid', table_name='blocks')
    op.drop_table('blocks')
    op.drop_index('ix_group_messages_created_time', table_name='group_messages')
    op.drop_index('ix_group_messages_sender_id', table_name='group_messages')
    op.drop_index('ix_group_messages_group_id', table_name='group_messages')
    op.drop_table('group_messages')
    op.drop_index('ix_group_members_user_id', table_name='group_members')
    op.drop_index('ix_group_members_group_id', table_name='group_members')
    op.drop_table('group_members')
    op.drop_index('ix_group_chats_owner_id', table_name='group_chats')
    op.drop_table('group_chats')
    op.drop_index('ix_dm_messages_created_time', table_name='dm_messages')
    op.drop_index('ix_dm_messages_sender_id', table_name='dm_messages')
    op.drop_index('ix_dm_messages_conversation_id', table_name='dm_messages')
    op.drop_table('dm_messages')
    op.drop_index('ix_dm_conversation_members_user_id', table_name='dm_conversation_members')
    op.drop_index('ix_dm_conversation_members_conversation_id', table_name='dm_conversation_members')
    op.drop_table('dm_conversation_members')
    op.drop_table('dm_conversations')
    op.drop_column('users', 'is_bot')
