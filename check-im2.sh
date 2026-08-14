#!/bin/bash
sleep 14
echo "=== 健康 ==="
curl -sk https://127.0.0.1/api/v1/health -H "Host: www.platformharness.ltd"
echo
echo "=== 迁移版本 ==="
sudo docker exec harness-db psql -U harness -d harness -t -A -c "SELECT version_num FROM alembic_version;"
echo "=== reports 表 ==="
sudo docker exec harness-db psql -U harness -d harness -t -A -c "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name='reports';"
echo "=== /admin/watermark SPA ==="
curl -sk -o /dev/null -w "HTTP %{http_code}\n" https://127.0.0.1/admin/watermark -H "Host: www.platformharness.ltd"
echo CHK-DONE
