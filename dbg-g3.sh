#!/bin/bash
BASE=https://127.0.0.1
H='Host: www.platformharness.ltd'
J='Content-Type: application/json'
echo "=== g3user 是否存在 ==="
sudo docker exec harness-db psql -U harness -d harness -t -A -c "SELECT uid, username, email FROM users WHERE email='g3user@example.com';"
echo "=== send-code ==="
curl -sk -X POST $BASE/api/v1/auth/send-code -H "$H" -H "$J" -d '{"email":"g3user@example.com","purpose":"register"}' -w "\nHTTP %{http_code}\n"
echo "=== email_codes ==="
sudo docker exec harness-db psql -U harness -d harness -t -A -c "SELECT email, code, created_time FROM email_codes WHERE email='g3user@example.com' ORDER BY created_time DESC LIMIT 3;"
echo DONE
