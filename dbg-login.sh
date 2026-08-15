#!/bin/bash
BASE=https://127.0.0.1
H='Host: www.platformharness.ltd'
J='Content-Type: application/json'
SECRET=$(sudo docker exec harness-db psql -U harness -d harness -t -A -c "SELECT totp_secret FROM users WHERE email='superadmin@platformharness.ltd';")
OTP=$(sudo docker exec harness-backend python -c "import pyotp;print(pyotp.TOTP('$SECRET').now())")
echo "OTP: $OTP"
for ip in 10.2.2.2 10.2.2.9; do
  curl -sk -X POST $BASE/api/v1/auth/login -H "$H" -H "$J" -H "X-Real-IP: $ip" -d "{\"email\":\"superadmin@platformharness.ltd\",\"password\":\"SuAdmin@2026Cloud\",\"totp_code\":\"$OTP\"}" -w "\nHTTP %{http_code} ip=$ip\n" | tail -2
done
echo DONE
