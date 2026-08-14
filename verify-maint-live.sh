#!/bin/bash
BASE=https://127.0.0.1
H='Host: www.platformharness.ltd'
J='Content-Type: application/json'
echo "=== 1) 开启维护（superadmin） ==="
SECRET=$(sudo docker exec harness-db psql -U harness -d harness -t -A -c "SELECT totp_secret FROM users WHERE email='superadmin@platformharness.ltd';")
OTP=$(sudo docker exec harness-backend python -c "import pyotp;print(pyotp.TOTP('$SECRET').now())")
curl -sk -X POST $BASE/api/v1/auth/login -H "$H" -H "$J" -d "{\"email\":\"superadmin@platformharness.ltd\",\"password\":\"SuAdmin@2026Cloud\",\"totp_code\":\"$OTP\"}" > /tmp/ts.json
TS=$(python3 -c 'import json;print(json.load(open("/tmp/ts.json"))["access_token"])')
curl -sk -o /dev/null -w "set-maint HTTP %{http_code}\n" -X PUT $BASE/api/v1/admin/settings -H "$H" -H "$J" -H "Authorization: Bearer $TS" -d '{"maintenance_mode":true,"maintenance_message":"正在进行安全升级，预计 30 分钟"}'
sleep 3
echo "=== 2) 公开维护状态 ==="
curl -sk $BASE/api/v1/public/maintenance -H "$H" | python3 -m json.tool

echo "=== 3) 普通用户（未登录）请求 → 503 ==="
curl -sk -o /dev/null -w "public/stats HTTP %{http_code}\n" $BASE/api/v1/public/stats -H "$H"
curl -sk -o /dev/null -w "public/notices HTTP %{http_code}\n" $BASE/api/v1/public/notices -H "$H"
curl -sk -o /dev/null -w "health HTTP %{http_code}\n" $BASE/api/v1/health -H "$H"
curl -sk -o /dev/null -w "captcha HTTP %{http_code}\n" $BASE/api/v1/captcha -H "$H"
curl -sk -X POST $BASE/api/v1/auth/login -H "$H" -H "$J" -d '{"email":"nobody@example.com","password":"WrongPass1"}' -o /dev/null -w "login HTTP %{http_code}\n"
curl -sk $BASE/api/v1/im/conversations -H "$H" -w "\nim HTTP %{http_code}\n" | tail -1

echo "=== 4) 管理员（带 token）完全放行 ==="
curl -sk -o /dev/null -w "admin/settings HTTP %{http_code}\n" $BASE/api/v1/admin/settings -H "$H" -H "Authorization: Bearer $TS"
curl -sk -o /dev/null -w "admin/messages HTTP %{http_code}\n" "$BASE/api/v1/admin/messages?page=1" -H "$H" -H "Authorization: Bearer $TS"
curl -sk -o /dev/null -w "user/profile HTTP %{http_code}\n" $BASE/api/v1/user/profile -H "$H" -H "Authorization: Bearer $TS"

echo "=== 5) 维护页 ==="
curl -sk -o /dev/null -w "/maintenance HTTP %{http_code}\n" https://127.0.0.1/maintenance -H "Host: www.platformharness.ltd"
curl -sk -o /dev/null -w "/ HTTP %{http_code}\n" https://127.0.0.1/ -H "Host: www.platformharness.ltd"

echo "=== 6) 关闭维护 ==="
curl -sk -o /dev/null -w "set-maint-off HTTP %{http_code}\n" -X PUT $BASE/api/v1/admin/settings -H "$H" -H "$J" -H "Authorization: Bearer $TS" -d '{"maintenance_mode":false}'
sleep 3
curl -sk $BASE/api/v1/public/maintenance -H "$H" | python3 -c 'import sys,json;print("维护状态:",json.load(sys.stdin)["maintenance"])'
curl -sk -o /dev/null -w "im-after HTTP %{http_code}\n" $BASE/api/v1/im/conversations -H "$H"
echo "MAINTENANCE LIVE ALL PASSED"
