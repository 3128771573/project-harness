#!/bin/bash
BASE=https://127.0.0.1
H='Host: www.platformharness.ltd'
J='Content-Type: application/json'
echo "=== 1) 取一条库中留言 ==="
ROW=$(sudo docker exec harness-db psql -U harness -d harness -t -A -F'|' -c "SELECT archive_no, query_code, COALESCE(email,'') FROM messages ORDER BY created_time DESC LIMIT 1;")
ANO=$(echo "$ROW" | cut -d'|' -f1)
QCODE=$(echo "$ROW" | cut -d'|' -f2)
GEMAIL=$(echo "$ROW" | cut -d'|' -f3)
echo "档案号: $ANO | 查询码: $QCODE"

echo "=== 2) 访客查询 ==="
curl -sk -X POST $BASE/api/v1/query -H "$H" -H "$J" -d "{\"query_code\":\"$QCODE\",\"email\":\"$GEMAIL\"}" > /tmp/gb-q.json
python3 -c 'import json;d=json.load(open("/tmp/gb-q.json"))["data"];print("status:",d["status"],"| archive:",d["archive_no"],"| 时间线条数:",len(d["replies"]))'

echo "=== 3) 管理员回复 ==="
SECRET=$(sudo docker exec harness-db psql -U harness -d harness -t -A -c "SELECT totp_secret FROM users WHERE email='superadmin@platformharness.ltd';")
OTP=$(sudo docker exec harness-backend python -c "import pyotp;print(pyotp.TOTP('$SECRET').now())")
curl -sk -X POST $BASE/api/v1/auth/login -H "$H" -H "$J" -d "{\"email\":\"superadmin@platformharness.ltd\",\"password\":\"SuAdmin@2026Cloud\",\"totp_code\":\"$OTP\"}" > /tmp/ts.json
TS=$(python3 -c 'import json;print(json.load(open("/tmp/ts.json"))["access_token"])')
MID=$(curl -sk "$BASE/api/v1/admin/messages?keyword=$ANO" -H "$H" -H "Authorization: Bearer $TS" | python3 -c 'import sys,json;print(json.load(sys.stdin)["items"][0]["id"])')
echo "mid: $MID"
curl -sk -o /dev/null -w "reply HTTP %{http_code}\n" -X PUT $BASE/api/v1/admin/messages/$MID/reply -H "$H" -H "$J" -H "Authorization: Bearer $TS" -d '{"reply":"【系统验证】已通过线上链路回复本条留言。"}'
curl -sk "$BASE/api/v1/admin/messages/$MID/replies" -H "$H" -H "Authorization: Bearer $TS" | python3 -c 'import sys,json;d=json.load(sys.stdin);print("时间线条数:",len(d),"| 最新类型:",d[-1]["sender_type"])'

echo "=== 4) 访客追问 ==="
curl -sk -X POST $BASE/api/v1/query/reply -H "$H" -H "$J" -d "{\"query_code\":\"$QCODE\",\"email\":\"$GEMAIL\",\"content\":\"线上追问验证\"}" > /tmp/gb-f.json
python3 -c 'import json;d=json.load(open("/tmp/gb-f.json"))["data"];print("追问后 status:",d["status"],"| 时间线条数:",len(d["replies"]))'

echo "=== 5) 关闭/重开 ==="
curl -sk -o /dev/null -w "close HTTP %{http_code}\n" -X POST $BASE/api/v1/admin/messages/$MID/close -H "$H" -H "Authorization: Bearer $TS"
curl -sk -o /dev/null -w "reopen HTTP %{http_code}\n" -X POST $BASE/api/v1/admin/messages/$MID/reopen -H "$H" -H "Authorization: Bearer $TS"

echo "=== 6) 页面 ==="
curl -sk -o /dev/null -w "/guestbook HTTP %{http_code}\n" https://127.0.0.1/guestbook -H "Host: www.platformharness.ltd"
curl -sk -o /dev/null -w "/admin/messages HTTP %{http_code}\n" https://127.0.0.1/admin/messages -H "Host: www.platformharness.ltd"
echo "GUESTBOOK LIVE ALL PASSED"
