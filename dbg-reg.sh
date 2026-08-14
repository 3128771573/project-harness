#!/bin/bash
BASE=https://127.0.0.1
H='Host: www.platformharness.ltd'
J='Content-Type: application/json'
echo "=== send-code 响应 ==="
curl -sk -X POST $BASE/api/v1/auth/send-code -H "$H" -H "$J" -d '{"email":"g9@example.com","purpose":"register"}' -w "\nHTTP %{http_code}\n"
echo "=== register 422 详情 ==="
curl -sk -X POST $BASE/api/v1/auth/send-code -H "$H" -H "$J" -d '{"email":"g8@example.com","purpose":"register"}' > /tmp/sc.json
C=$(python3 -c 'import json;print(json.load(open("/tmp/sc.json")).get("dev_code",""))')
echo "code=[$C]"
curl -sk -X POST $BASE/api/v1/auth/register -H "$H" -H "$J" -d "{\"username\":\"g8user\",\"email\":\"g8@example.com\",\"password\":\"TestPass123\",\"code\":\"$C\"}" -w "\nHTTP %{http_code}\n"
echo DONE
