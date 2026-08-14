#!/bin/bash
sleep 12
echo "=== 健康 ==="
curl -sk https://127.0.0.1/api/v1/health -H "Host: www.platformharness.ltd"
echo
echo "=== 迁移版本 ==="
sudo docker exec harness-db psql -U harness -d harness -t -A -c "SELECT version_num FROM alembic_version;"
echo "=== 新表 ==="
sudo docker exec harness-db psql -U harness -d harness -t -A -c "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('dm_conversations','dm_messages','dm_conversation_members','group_chats','group_members','group_messages','blocks','watermark_grants','watermark_logs') ORDER BY table_name;"
echo "=== is_bot 列 ==="
sudo docker exec harness-db psql -U harness -d harness -t -A -c "SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='is_bot';"
echo "=== 机器人账号 ==="
sudo docker exec harness-db psql -U harness -d harness -t -A -c "SELECT uid, username, nickname, is_bot FROM users WHERE uid='bot-harness-official';"
echo "=== 后端日志尾 ==="
sudo docker logs harness-backend --tail 5 2>&1
echo CHK-DONE
