"""sensitive_words 敏感词库（内容审核 FR8.3）+ 内置词库

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-08-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2e3f4a5b6c7'
down_revision: Union[str, None] = 'c1d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 内置基础词库（明确违法/违规类别；仅作兜底，管理员可增删）
DEFAULT_WORDS = [
    # 毒品
    "海洛因", "冰毒", "大麻", "摇头丸", "可卡因", "制毒", "吸毒", "毒品交易",
    # 赌博
    "博彩", "赌场", "百家乐", "网络赌博", "下注网站", "赌球", "六合彩",
    # 色情交易
    "援交", "约炮", "色情交易", "卖淫", "嫖娼", "裸聊",
    # 诈骗/洗钱
    "刷单返利", "杀猪盘", "跑分洗钱", "洗钱", "网络诈骗", "冒充客服", "裸聊敲诈",
    # 违法物品/服务
    "枪支", "炸药", "制枪", "售卖公民信息", "开锁服务", "伪造证件", "假发票", "虚开发票", "考试答案出售",
]


def upgrade() -> None:
    op.create_table(
        'sensitive_words',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('word', sa.String(length=64), nullable=False, unique=True),
        sa.Column('category', sa.String(length=32), server_default=sa.text("'other'"), nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_sensitive_words_word', 'sensitive_words', ['word'])
    for w in DEFAULT_WORDS:
        op.execute(
            sa.text("INSERT INTO sensitive_words (id, word, category) VALUES (:id, :word, 'builtin') ON CONFLICT (word) DO NOTHING").bindparams(
                id=str(__import__('uuid').uuid4()), word=w
            )
        )


def downgrade() -> None:
    op.drop_index('ix_sensitive_words_word', table_name='sensitive_words')
    op.drop_table('sensitive_words')
