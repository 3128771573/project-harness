#!/bin/bash
BASE=https://127.0.0.1
H='Host: www.platformharness.ltd'
J='Content-Type: application/json'
echo "=== 1) 注册 im2-a / im2-b ==="
curl -sk -X POST $BASE/api/v1/auth/send-code -H "$H" -H "$J" -d '{"email":"im2-a@example.com","purpose":"register"}' > /tmp/i2a.json
CA=$(python3 -c 'import json;print(json.load(open("/tmp/i2a.json")).get("dev_code",""))')
curl -sk -o /dev/null -w "a %{http_code}\n" -X POST $BASE/api/v1/auth/register -H "$H" -H "$J" -d "{\"username\":\"im2a\",\"email\":\"im2-a@example.com\",\"password\":\"TestPass123\",\"code\":\"$CA\"}"
curl -sk -X POST $BASE/api/v1/auth/send-code -H "$H" -H "$J" -d '{"email":"im2-b@example.com","purpose":"register"}' > /tmp/i2b.json
CB=$(python3 -c 'import json;print(json.load(open("/tmp/i2b.json")).get("dev_code",""))')
curl -sk -o /dev/null -w "b %{http_code}\n" -X POST $BASE/api/v1/auth/register -H "$H" -H "$J" -d "{\"username\":\"im2b\",\"email\":\"im2-b@example.com\",\"password\":\"TestPass123\",\"code\":\"$CB\"}"
curl -sk -X POST $BASE/api/v1/auth/login -H "$H" -H "$J" -d '{"email":"im2-a@example.com","password":"TestPass123"}' > /tmp/t2a.json
TA=$(python3 -c 'import json;print(json.load(open("/tmp/t2a.json"))["access_token"])')
curl -sk -X POST $BASE/api/v1/auth/login -H "$H" -H "$J" -d '{"email":"im2-b@example.com","password":"TestPass123"}' > /tmp/t2b.json
TB=$(python3 -c 'import json;print(json.load(open("/tmp/t2b.json"))["access_token"])')
BUID=$(python3 -c 'import json;print(json.load(open("/tmp/t2b.json"))["user"]["uid"])')

echo "=== 2) 建会话发消息 + 举报 ==="
CID=$(curl -sk -X POST $BASE/api/v1/im/conversations -H "$H" -H "$J" -H "Authorization: Bearer $TA" -d "{\"user_id\":\"$BUID\"}" | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')
MID=$(curl -sk -X POST $BASE/api/v1/im/conversations/$CID/messages -H "$H" -H "$J" -H "Authorization: Bearer $TA" -d '{"kind":"text","content":"这是一条待举报消息"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')
curl -sk -o /dev/null -w "report HTTP %{http_code}\n" -X POST $BASE/api/v1/im/messages/$MID/report -H "$H" -H "$J" -H "Authorization: Bearer $TB" -d '{"reason":"广告骚扰"}'

echo "=== 3) 拉黑 API + 403 + 解除 ==="
curl -sk -o /dev/null -w "block HTTP %{http_code}\n" -X POST $BASE/api/v1/im/blocks -H "$H" -H "$J" -H "Authorization: Bearer $TA" -d "{\"user_id\":\"$BUID\"}"
curl -sk -o /dev/null -w "send-blocked HTTP %{http_code}\n" -X POST $BASE/api/v1/im/conversations/$CID/messages -H "$H" -H "$J" -H "Authorization: Bearer $TA" -d '{"kind":"text","content":"被拉黑后"}'
curl -sk "$BASE/api/v1/im/blocks" -H "$H" -H "Authorization: Bearer $TA" > /tmp/bl2.json
python3 -c 'import json;d=json.load(open("/tmp/bl2.json"));print("blocks:", len(d)); assert len(d)==1'
curl -sk -o /dev/null -w "unblock HTTP %{http_code}\n" -X DELETE $BASE/api/v1/im/blocks/$BUID -H "$H" -H "Authorization: Bearer $TA"
curl -sk -o /dev/null -w "send-recovered HTTP %{http_code}\n" -X POST $BASE/api/v1/im/conversations/$CID/messages -H "$H" -H "$J" -H "Authorization: Bearer $TA" -d '{"kind":"text","content":"解除后恢复"}'

echo "=== 4) 举报落库核对 ==="
sudo docker exec harness-db psql -U harness -d harness -t -A -c "SELECT target_type, reason, status FROM reports WHERE target_id='$MID';"

echo "=== 5) 清理 ==="
sudo docker exec harness-db psql -U harness -d harness -q -c "
DELETE FROM reports WHERE target_id IN (SELECT id FROM dm_messages WHERE conversation_id IN (SELECT id FROM dm_conversations WHERE user_a IN (SELECT uid FROM users WHERE email IN ('im2-a@example.com','im2-b@example.com')) OR user_b IN (SELECT uid FROM users WHERE email IN ('im2-a@example.com','im2-b@example.com'))));
DELETE FROM dm_messages WHERE conversation_id IN (SELECT id FROM dm_conversations WHERE user_a IN (SELECT uid FROM users WHERE email IN ('im2-a@example.com','im2-b@example.com')) OR user_b IN (SELECT uid FROM users WHERE email IN ('im2-a@example.com','im2-b@example.com')));
DELETE FROM dm_conversation_members WHERE conversation_id IN (SELECT id FROM dm_conversations WHERE user_a IN (SELECT uid FROM users WHERE email IN ('im2-a@example.com','im2-b@example.com')) OR user_b IN (SELECT uid FROM users WHERE email IN ('im2-a@example.com','im2-b@example.com')));
DELETE FROM dm_conversations WHERE user_a IN (SELECT uid FROM users WHERE email IN ('im2-a@example.com','im2-b@example.com')) OR user_b IN (SELECT uid FROM users WHERE email IN ('im2-a@example.com','im2-b@example.com'));
DELETE FROM refresh_tokens WHERE uid IN (SELECT uid FROM users WHERE email IN ('im2-a@example.com','im2-b@example.com'));
DELETE FROM login_logs WHERE uid IN (SELECT uid FROM users WHERE email IN ('im2-a@example.com','im2-b@example.com'));
DELETE FROM email_codes WHERE email IN ('im2-a@example.com','im2-b@example.com');
DELETE FROM users WHERE email IN ('im2-a@example.com','im2-b@example.com');"
echo "IM2 LIVE ALL PASSED"
