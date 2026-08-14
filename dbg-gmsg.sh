#!/bin/bash
BASE=https://127.0.0.1
H='Host: www.platformharness.ltd'
J='Content-Type: application/json'
curl -sk -X POST $BASE/api/v1/auth/login -H "$H" -H "$J" -d '{"email":"alice-im@example.com","password":"TestPass123"}' > /tmp/ta.json
TA=$(python3 -c 'import json;print(json.load(open("/tmp/ta.json"))["access_token"])')
GID=$(sudo docker exec harness-db psql -U harness -d harness -t -A -c "SELECT id FROM group_chats WHERE name='审核测试群' LIMIT 1;")
echo "gid: $GID"
curl -sk -X POST $BASE/api/v1/im/groups/$GID/messages -H "$H" -H "$J" -H "Authorization: Bearer $TA" -d '{"kind":"text","content":"这条将被匿名化"}' -w "\nHTTP %{http_code}\n"
echo "=== 最近敏感词表 ==="
sudo docker exec harness-db psql -U harness -d harness -c "SELECT word, enabled FROM sensitive_words WHERE word LIKE '%匿名%' OR word LIKE '%测试词%' LIMIT 5;"
echo DONE
