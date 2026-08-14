#!/bin/bash
sudo docker exec harness-db psql -U harness -d harness -c "
SELECT m.content, m.created_time
FROM dm_messages m
JOIN dm_conversations c ON c.id = m.conversation_id
WHERE (c.user_a = 'bot-harness-official' OR c.user_b = 'bot-harness-official')
ORDER BY m.created_time DESC LIMIT 8;"
echo "=== 上轮遗留 reports ==="
sudo docker exec harness-db psql -U harness -d harness -c "SELECT id, target_type, target_id, reason, status FROM reports ORDER BY created_time DESC LIMIT 5;"
