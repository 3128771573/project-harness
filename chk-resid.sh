#!/bin/bash
echo "=== 残留群 ==="
sudo docker exec harness-db psql -U harness -d harness -c "SELECT id, name, owner_id FROM group_chats;"
echo "=== 残留成员 ==="
sudo docker exec harness-db psql -U harness -d harness -c "SELECT group_id, user_id FROM group_members;"
echo "=== 测试用户 ==="
sudo docker exec harness-db psql -U harness -d harness -c "SELECT uid, username, email FROM users WHERE email LIKE '%im@example.com' OR email LIKE 'deleted-%' OR username LIKE 'user_%' OR username IN ('alice_im','bob_im','carol_im');"
echo DONE
