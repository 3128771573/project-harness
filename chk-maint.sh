#!/bin/bash
echo "=== 云端 migrate.sql 维护行 ==="
grep -n "maintenance" /tmp/migrate.sql 2>/dev/null || echo "migrate.sql 不存在或无维护行"
echo "=== AppSetting 当前值 ==="
sudo docker exec harness-db psql -U harness -d harness -c "SELECT key, value, updated_at FROM app_settings WHERE key LIKE 'site.maintenance%';"
echo "=== 本地 deploy-r3.sh 维护行 ==="
grep -n "maintenance" /home/x230user/projects/harness/deploy-r3.sh
echo DONE
