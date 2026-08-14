#!/bin/bash
BASE=https://127.0.0.1
H='Host: www.platformharness.ltd'
J='Content-Type: application/json'
echo "=== pending reports ==="
sudo docker exec harness-db psql -U harness -d harness -c "SELECT id, target_type, target_id, status FROM reports WHERE status='pending' ORDER BY created_time DESC LIMIT 3;"
RID=$(sudo docker exec harness-db psql -U harness -d harness -t -A -c "SELECT id FROM reports WHERE status='pending' AND target_type='group' ORDER BY created_time DESC LIMIT 1;")
echo "group report id: $RID"
SECRET=$(sudo docker exec harness-db psql -U harness -d harness -t -A -c "SELECT totp_secret FROM users WHERE email='superadmin@platformharness.ltd';")
OTP=$(sudo docker exec harness-backend python -c "import pyotp;print(pyotp.TOTP('$SECRET').now())")
curl -sk -X POST $BASE/api/v1/auth/login -H "$H" -H "$J" -d "{\"email\":\"superadmin@platformharness.ltd\",\"password\":\"SuAdmin@2026Cloud\",\"totp_code\":\"$OTP\"}" > /tmp/ts.json
TS=$(python3 -c 'import json;print(json.load(open("/tmp/ts.json"))["access_token"])')
if [ -n "$RID" ]; then
  curl -sk -X POST $BASE/api/v1/admin/im/reports/$RID/handle -H "$H" -H "$J" -H "Authorization: Bearer $TS" -d '{"action":"ban"}' -w "\nHTTP %{http_code}\n"
fi
echo DONE
