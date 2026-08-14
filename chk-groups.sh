#!/bin/bash
echo "=== 最近的群 ==="
sudo docker exec harness-db psql -U harness -d harness -c "SELECT id, name, owner_id FROM group_chats ORDER BY created_time DESC LIMIT 5;"
echo "=== 群成员 ==="
sudo docker exec harness-db psql -U harness -d harness -c "SELECT gm.group_id, gm.user_id, u.username, gm.role FROM group_members gm JOIN users u ON u.uid = gm.user_id ORDER BY gm.joined_time DESC LIMIT 10;"
echo "=== alice 测试用户 ==="
sudo docker exec harness-db psql -U harness -d harness -c "SELECT uid, username, email, is_active FROM users WHERE email LIKE '%im@example.com' OR username IN ('alice_im','bob_im','carol_im') LIMIT 10;"
echo DONE
