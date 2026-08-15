#!/bin/bash
echo "=== alembic 版本 ==="
sudo docker exec harness-db psql -U harness -d harness -t -A -c "SELECT version_num FROM alembic_version;"
echo "=== refresh_tokens 列 ==="
sudo docker exec harness-db psql -U harness -d harness -t -A -c "SELECT column_name FROM information_schema.columns WHERE table_name='refresh_tokens' ORDER BY ordinal_position;"
echo "=== 容器内 alembic 文件 ==="
sudo docker exec harness-backend ls /app/backend/alembic/versions/ | tail -6
echo "=== 后端日志（启动段） ==="
sudo docker logs harness-backend 2>&1 | head -12
echo DONE
