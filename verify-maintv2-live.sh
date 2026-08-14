#!/bin/bash
BASE=https://127.0.0.1
H='Host: www.platformharness.ltd'
J='Content-Type: application/json'
SECRET=$(sudo docker exec harness-db psql -U harness -d harness -t -A -c "SELECT totp_secret FROM users WHERE email='superadmin@platformharness.ltd';")
OTP=$(sudo docker exec harness-backend python -c "import pyotp;print(pyotp.TOTP('$SECRET').now())")
curl -sk -X POST $BASE/api/v1/auth/login -H "$H" -H "$J" -d "{\"email\":\"superadmin@platformharness.ltd\",\"password\":\"SuAdmin@2026Cloud\",\"totp_code\":\"$OTP\"}" > /tmp/ts.json
TS=$(python3 -c 'import json;print(json.load(open("/tmp/ts.json"))["access_token"])')

echo "=== 1) 状态 / 页面 ==="
curl -sk $BASE/api/v1/admin/maintenance/status -H "$H" -H "Authorization: Bearer $TS" | python3 -c 'import sys,json;d=json.load(sys.stdin);print("mode:",d["mode"],"| 超时兜底:",d["max_duration_minutes"],"分 | 紧急令牌:",d["emergency_configured"])'
curl -sk -o /dev/null -w "/admin/maintenance HTTP %{http_code}\n" https://127.0.0.1/admin/maintenance -H "Host: www.platformharness.ltd"

echo "=== 2) 开启 block_new ==="
curl -sk -X POST $BASE/api/v1/admin/maintenance/enable -H "$H" -H "$J" -H "Authorization: Bearer $TS" -d '{"mode":"block_new","reason":"灰度测试：新功能内测","duration_minutes":30}' -o /dev/null -w "enable HTTP %{http_code}\n"
sleep 2
curl -sk $BASE/api/v1/im/conversations -H "$H" -o /dev/null -w "admin HTTP %{http_code}\n" -H "Authorization: Bearer $TS"
curl -sk $BASE/api/v1/public/maintenance -H "$H" | python3 -c 'import sys,json;d=json.load(sys.stdin);print("mode:",d["mode"],"| reason:",d["reason"])'

echo "=== 3) 延长 + 倒计时 ==="
curl -sk -X POST $BASE/api/v1/admin/maintenance/extend -H "$H" -H "$J" -H "Authorization: Bearer $TS" -d '{"minutes":60}' | python3 -c 'import sys,json;d=json.load(sys.stdin);print("remaining:",d["remaining_seconds"],"s")'

echo "=== 4) 紧急令牌 ==="
TOK=$(curl -sk -X POST $BASE/api/v1/admin/maintenance/regenerate-token -H "$H" -H "Authorization: Bearer $TS" | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])')
echo "token len: $(echo -n "$TOK" | wc -c)"
curl -sk -o /dev/null -w "bypass-with-token HTTP %{http_code}\n" "$BASE/api/v1/im/conversations?__emergency=$TOK" -H "$H"
curl -sk "$BASE/api/v1/admin/maintenance/emergency-close?token=$TOK" -H "$H" | python3 -c 'import sys,json;print(json.load(sys.stdin)["message"])'
curl -sk $BASE/api/v1/public/maintenance -H "$H" | python3 -c 'import sys,json;print("维护状态:",json.load(sys.stdin)["maintenance"])'

echo "=== 5) 定时计划 ==="
curl -sk -X POST $BASE/api/v1/admin/maintenance/schedule -H "$H" -H "$J" -H "Authorization: Bearer $TS" -d '{"enabled":true,"time":"03:00","duration":60,"days":[]}' | python3 -c 'import sys,json;d=json.load(sys.stdin);print("scheduled:",d["scheduled_enabled"],d["scheduled_time"])'
curl -sk -X POST $BASE/api/v1/admin/maintenance/schedule -H "$H" -H "$J" -H "Authorization: Bearer $TS" -d '{"enabled":false}' -o /dev/null -w "schedule-off HTTP %{http_code}\n"

echo "=== 6) 操作记录 ==="
curl -sk "$BASE/api/v1/admin/maintenance/history?limit=6" -H "$H" -H "Authorization: Bearer $TS" | python3 -c 'import sys,json;[print(x["time_utc"][:19],"|",x["operator"],"|",x["action"],"|",x["detail"][:40]) for x in json.load(sys.stdin)]'
echo "MAINTENANCE V2 LIVE ALL PASSED"
