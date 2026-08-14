#!/bin/bash
set -euo pipefail
KEY=/home/x230user/.ssh/id_ed25519_cloud
cd ~/projects/harness
echo "=== 打包并传输到云 ==="
tar czf /tmp/harness-r3.tar.gz --exclude='*__pycache__*' frontend/src frontend/index.html frontend/public frontend/package.json frontend/package-lock.json frontend/Dockerfile frontend/nginx.conf backend/Dockerfile backend/alembic.ini backend/alembic backend/app/main.py backend/app/models.py backend/app/schemas.py backend/app/config.py backend/app/middleware.py backend/app/routers backend/app/services backend/requirements.txt docker-compose.prod.yml scripts
scp -i $KEY -o StrictHostKeyChecking=accept-new /tmp/harness-r3.tar.gz ubuntu@124.222.140.57:/tmp/harness-r3.tar.gz
echo "=== 生成迁移 SQL ==="
cat > /tmp/migrate.sql <<'SQL'
ALTER TABLE ai_history ADD COLUMN IF NOT EXISTS conversation_id VARCHAR(36);
CREATE INDEX IF NOT EXISTS ix_ai_history_conversation_id ON ai_history(conversation_id);
ALTER TABLE visit_logs ADD COLUMN IF NOT EXISTS ip_location VARCHAR(128);
ALTER TABLE login_logs ADD COLUMN IF NOT EXISTS ip_location VARCHAR(128);
ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_secret VARCHAR(64);
ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_enabled BOOLEAN NOT NULL DEFAULT FALSE;
-- 注意：不再手工 stamp alembic_version（链式迁移由容器启动时的 alembic upgrade head 自愈，
-- 手工插入会与已推进的版本产生双行导致 overlaps 错误）
DELETE FROM visit_logs WHERE method <> 'PAGE' OR method IS NULL;
-- 维护模式：部署期间开启（新容器启动后生效），部署完成后关闭
INSERT INTO maintenance_config (id, config_key, config_value, updated_by) VALUES (gen_random_uuid()::text, 'mode', 'full', 'deploy')
  ON CONFLICT (config_key) DO UPDATE SET config_value='full', updated_by='deploy', updated_at=now();
SQL
scp -i $KEY -o StrictHostKeyChecking=accept-new /tmp/migrate.sql ubuntu@124.222.140.57:/tmp/migrate.sql
echo "=== 生成维护关闭 SQL（部署完成后执行） ==="
cat > /tmp/maint-off.sql <<'SQL'
INSERT INTO maintenance_config (id, config_key, config_value, updated_by) VALUES (gen_random_uuid()::text, 'mode', 'none', 'deploy')
  ON CONFLICT (config_key) DO UPDATE SET config_value='none', updated_by='deploy', updated_at=now();
SQL
scp -i $KEY -o StrictHostKeyChecking=accept-new /tmp/maint-off.sql ubuntu@124.222.140.57:/tmp/maint-off.sql
echo "=== 云端解包 + 重建 backend + frontend ==="
ssh -i $KEY -o StrictHostKeyChecking=accept-new ubuntu@124.222.140.57 'set -e; cd /app/harness && sudo -n chown -R ubuntu:ubuntu /app/harness && sudo -n find /app/harness -name __pycache__ -type d -prune -exec rm -rf {} + && tar xzf /tmp/harness-r3.tar.gz && cp -f docker-compose.prod.yml docker-compose.yml && sudo -n mkdir -p /data/harness/mosquitto /data/harness/mosquitto-log && sudo -n chown -R 1883:1883 /data/harness/mosquitto /data/harness/mosquitto-log && echo "=== jwt secret / public url ===" && grep -q "^JWT_SECRET=" /app/harness/.env || echo "JWT_SECRET=$(openssl rand -hex 32)" >> /app/harness/.env && grep -q "^PUBLIC_BASE_URL=" /app/harness/.env || echo "PUBLIC_BASE_URL=https://www.platformharness.ltd" >> /app/harness/.env && echo "=== db migrate (含 alembic stamp) ===" && sudo -n docker exec -i harness-db psql -U harness -d harness < /tmp/migrate.sql && (sudo -n docker compose build backend frontend > /tmp/harness-build.log 2>&1) && echo "BUILD OK" && sudo -n docker compose up -d mqtt backend frontend && echo "=== containers ===" && sudo -n docker ps --format "{{.Names}} {{.Status}}" && echo "=== status ===" && sleep 4 && curl -sk https://127.0.0.1/api/v1/public/status -H "Host: www.platformharness.ltd" && echo && echo "=== 关闭维护模式 ===" && sudo -n docker exec -i harness-db psql -U harness -d harness < /tmp/maint-off.sql && echo "=== build log tail ===" && tail -4 /tmp/harness-build.log'
