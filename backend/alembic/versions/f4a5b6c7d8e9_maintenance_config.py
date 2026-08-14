"""企业级维护模式：maintenance_config 配置表（四模式/倒计时/定时/紧急令牌）

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
Create Date: 2026-08-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f4a5b6c7d8e9'
down_revision: Union[str, None] = 'e3f4a5b6c7d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'maintenance_config',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('config_key', sa.String(length=64), nullable=False, unique=True),
        sa.Column('config_value', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.String(length=64), nullable=True),
    )
    op.create_index('ix_maintenance_config_key', 'maintenance_config', ['config_key'])
    # 迁移旧维护开关（AppSetting site.maintenance）→ mode
    conn = op.get_bind()
    row = conn.execute(sa.text("SELECT value FROM app_settings WHERE key='site.maintenance'")).fetchone()
    if row is not None and str(row[0]).lower() == 'true':
        conn.execute(
            sa.text("INSERT INTO maintenance_config (id, config_key, config_value) VALUES (:id, 'mode', 'full')"),
            {"id": str(__import__('uuid').uuid4())},
        )
    # 默认配置
    defaults = {
        'max_duration_minutes': '120',
        'scheduled_enabled': 'false',
        'scheduled_time': '03:00',
        'scheduled_duration': '60',
        'scheduled_days': '',
    }
    for k, v in defaults.items():
        conn.execute(
            sa.text("INSERT INTO maintenance_config (id, config_key, config_value) VALUES (:id, :k, :v)"),
            {"id": str(__import__('uuid').uuid4()), "k": k, "v": v},
        )


def downgrade() -> None:
    op.drop_index('ix_maintenance_config_key', table_name='maintenance_config')
    op.drop_table('maintenance_config')
