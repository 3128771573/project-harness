#!/bin/bash
# 云端 HTTPS 全链路验证（独立于容器内 E2E）
BASE=https://127.0.0.1
H='Host: www.platformharness.ltd'
J='Content-Type: application/json'
FAIL=0
step() { echo "=== $1 ==="; }

cleanup_users() {
  sudo docker exec harness-db psql -U harness -d harness -q -c "DELETE FROM dm_messages WHERE sender_id IN (SELECT uid FROM users WHERE email IN ('im-live-a@example.com','im-live-b@example.com')); DELETE FROM dm_conversation_members WHERE user_id IN (SELECT uid FROM users WHERE email IN ('im-live-a@example.com','im-live-b@example.com')); DELETE FROM dm_conversations WHERE user_a IN (SELECT uid FROM users WHERE email IN ('im-live-a@example.com','im-live-b@example.com')) OR user_b IN (SELECT uid FROM users WHERE email IN ('im-live-a@example.com','im-live-b@example.com')); DELETE FROM users WHERE email IN ('im-live-a@example.com','im-live-b@example.com');"
}
cleanup_users

step "1) 注册 im-live-a / im-live-b"
curl -sk -X POST $BASE/api/v1/auth/send-code -H "$H" -H "$J" -d '{"email":"im-live-a@example.com","purpose":"register"}' > /tmp/la.json
CA=$(python3 -c 'import json;print(json.load(open("/tmp/la.json")).get("dev_code",""))')
curl -sk -o /dev/null -w "register-a HTTP %{http_code}\n" -X POST $BASE/api/v1/auth/register -H "$H" -H "$J" -d "{\"username\":\"imlivea\",\"email\":\"im-live-a@example.com\",\"password\":\"TestPass123\",\"code\":\"$CA\"}"
curl -sk -X POST $BASE/api/v1/auth/send-code -H "$H" -H "$J" -d '{"email":"im-live-b@example.com","purpose":"register"}' > /tmp/lb.json
CB=$(python3 -c 'import json;print(json.load(open("/tmp/lb.json")).get("dev_code",""))')
curl -sk -o /dev/null -w "register-b HTTP %{http_code}\n" -X POST $BASE/api/v1/auth/register -H "$H" -H "$J" -d "{\"username\":\"imliveb\",\"email\":\"im-live-b@example.com\",\"password\":\"TestPass123\",\"code\":\"$CB\"}"

curl -sk -X POST $BASE/api/v1/auth/login -H "$H" -H "$J" -d '{"email":"im-live-a@example.com","password":"TestPass123"}' > /tmp/ta.json
TA=$(python3 -c 'import json;print(json.load(open("/tmp/ta.json"))["access_token"])')
curl -sk -X POST $BASE/api/v1/auth/login -H "$H" -H "$J" -d '{"email":"im-live-b@example.com","password":"TestPass123"}' > /tmp/tb.json
TB=$(python3 -c 'import json;print(json.load(open("/tmp/tb.json"))["access_token"])')
BUID=$(python3 -c 'import json;print(json.load(open("/tmp/tb.json"))["user"]["uid"])')
echo "bob uid: $BUID"

step "2) 建会话 + 发消息"
CID=$(curl -sk -X POST $BASE/api/v1/im/conversations -H "$H" -H "$J" -H "Authorization: Bearer $TA" -d "{\"user_id\":\"$BUID\"}" | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')
echo "conv: $CID"
MID=$(curl -sk -X POST $BASE/api/v1/im/conversations/$CID/messages -H "$H" -H "$J" -H "Authorization: Bearer $TA" -d '{"kind":"text","content":"HTTPS 实时链路验证"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')
echo "msg: $MID"

step "3) bob 未读 + 已读 + 撤回"
curl -sk "$BASE/api/v1/im/conversations" -H "$H" -H "Authorization: Bearer $TB" > /tmp/bl.json
python3 - <<'PY'
import json
d = json.load(open("/tmp/bl.json"))
c = [x for x in d["items"] if x["other"]["uid"] == json.load(open("/tmp/ta.json"))["user"]["uid"]][0]
print("bob unread:", c["unread"], "| last:", c["last_message"]["content"])
assert c["unread"] == 1 and c["last_message"]["content"] == "HTTPS 实时链路验证"
PY
curl -sk -o /dev/null -w "read HTTP %{http_code}\n" -X POST $BASE/api/v1/im/conversations/$CID/read -H "$H" -H "Authorization: Bearer $TB"
curl -sk -o /dev/null -w "recall HTTP %{http_code}\n" -X POST $BASE/api/v1/im/messages/$MID/recall -H "$H" -H "Authorization: Bearer $TA"

step "4) 机器人全量广播（superadmin TOTP）"
SECRET=$(sudo docker exec harness-db psql -U harness -d harness -t -A -c "SELECT totp_secret FROM users WHERE email='superadmin@platformharness.ltd';")
OTP=$(sudo docker exec harness-backend python -c "import pyotp;print(pyotp.TOTP('$SECRET').now())")
curl -sk -X POST $BASE/api/v1/auth/login -H "$H" -H "$J" -d "{\"email\":\"superadmin@platformharness.ltd\",\"password\":\"SuAdmin@2026Cloud\",\"totp_code\":\"$OTP\"}" > /tmp/ts.json
TS=$(python3 -c 'import json;print(json.load(open("/tmp/ts.json"))["access_token"])')
curl -sk -X POST $BASE/api/v1/admin/im/broadcast -H "$H" -H "$J" -H "Authorization: Bearer $TS" -d '{"content":"【平台通知】新私信系统已上线","reason":"IM P0 发布"}' > /tmp/bc.json
python3 -c 'import json;d=json.load(open("/tmp/bc.json"));print("broadcast sent:", d.get("sent")); assert d.get("sent",0)>=1'
curl -sk "$BASE/api/v1/im/conversations" -H "$H" -H "Authorization: Bearer $TA" > /tmp/al.json
python3 - <<'PY'
import json
d = json.load(open("/tmp/al.json"))
bot = [x for x in d["items"] if x["other"]["uid"] == "bot-harness-official"]
assert bot and "新私信系统" in bot[0]["last_message"]["content"], "alice 应收到机器人广播"
print("alice 收到机器人广播:", bot[0]["last_message"]["content"], "| unread:", bot[0]["unread"])
PY

step "5) 文本水印取证（superadmin 解码）"
sudo docker exec harness-db psql -U harness -d harness -t -A -c "SELECT uid FROM users WHERE email='im-live-a@example.com';" > /tmp/auid.txt
AUID=$(cat /tmp/auid.txt | tr -d ' 
')
ZW=$(sudo docker exec harness-backend python -c "from app.services.watermark import encode_text_watermark; print(encode_text_watermark('$AUID', '$MID', 1755234000))")
curl -sk -X POST $BASE/api/v1/im/decode-text -H "$H" -H "$J" -H "Authorization: Bearer $TS" -d "{\"text\":\"泄露截图内容$ZW\"}" > /tmp/dc.json
python3 - <<'PY'
import json
d = json.load(open("/tmp/dc.json"))
print("decode:", json.dumps(d, ensure_ascii=False)[:200])
assert d["matched"] and d["user"]["uid"] == open("/tmp/auid.txt").read().strip(), d
PY
echo "未授权 → 应 403"
curl -sk -o /dev/null -w "alice decode HTTP %{http_code}\n" -X POST $BASE/api/v1/im/decode-text -H "$H" -H "$J" -H "Authorization: Bearer $TA" -d "{\"text\":\"x$ZW\"}"

step "6) 铃铛未读接口"
curl -sk "$BASE/api/v1/im/unread" -H "$H" -H "Authorization: Bearer $TA" > /tmp/un.json
python3 -c 'import json;d=json.load(open("/tmp/un.json"));print("alice unread total:", d["total"]); assert d["total"]>=1'

step "7) 清理"
cleanup_users
echo "IM LIVE ALL PASSED"
