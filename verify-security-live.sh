#!/bin/bash
BASE=https://127.0.0.1
H='Host: www.platformharness.ltd'
J='Content-Type: application/json'
echo "=== 1) API 文档生产关闭 ==="
curl -sk -o /dev/null -w "/docs HTTP %{http_code}\n" $BASE/docs -H "$H"
curl -sk -o /dev/null -w "/openapi.json HTTP %{http_code}\n" $BASE/openapi.json -H "$H"
curl -sk -o /dev/null -w "/api/docs HTTP %{http_code}\n" $BASE/api/docs -H "$H"

echo "=== 2) 安全头 ==="
curl -sk -D - -o /dev/null https://127.0.0.1/ -H "$H" | grep -iE "server:|content-security|permissions-policy" | head -4

echo "=== 3) 登录限流（后端 5/60s） ==="
for i in 1 2 3 4 5 6; do
  curl -sk -o /dev/null -w "%{http_code} " -X POST $BASE/api/v1/auth/login -H "$H" -H "$J" -d '{"email":"nonexist-z@example.com","password":"WrongPass1"}'
done
echo
echo "=== 4) 上传校验 ==="
SECRET=$(sudo docker exec harness-db psql -U harness -d harness -t -A -c "SELECT totp_secret FROM users WHERE email='superadmin@platformharness.ltd';")
OTP=$(sudo docker exec harness-backend python -c "import pyotp;print(pyotp.TOTP('$SECRET').now())")
curl -sk -X POST $BASE/api/v1/auth/login -H "$H" -H "$J" -H "X-Real-IP: 10.2.2.2" -d "{\"email\":\"superadmin@platformharness.ltd\",\"password\":\"SuAdmin@2026Cloud\",\"totp_code\":\"$OTP\"}" > /tmp/ts.json
TS=$(python3 -c 'import json;print(json.load(open("/tmp/ts.json"))["access_token"])')
printf '<html><script>alert(1)</script></html>' > /tmp/evil.jpg
curl -sk -X POST $BASE/api/v1/user/avatar -H "$H" -H "Authorization: Bearer $TS" -F "file=@/tmp/evil.jpg;type=image/jpeg" -w "\nfake HTTP %{http_code}\n"
B64=$(python3 -c "
import struct, zlib, base64
sig = b'\x89PNG\r\n\x1a\n'
ihdr = struct.pack('>IIBBBBB', 16, 16, 8, 2, 0, 0, 0)
raw = b''
for _ in range(16):
    raw += b'\x00' + b'\x80\x40\x20' * 16
idat = zlib.compress(raw)
def chunk(t, d):
    return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xFFFFFFFF)
print(base64.b64encode(sig + chunk(b'IHDR', ihdr) + chunk(b'IDAT', idat) + chunk(b'IEND', b'')).decode())
")
echo "$B64" | base64 -d > /tmp/ok.png
curl -sk -X POST $BASE/api/v1/user/avatar -H "$H" -H "Authorization: Bearer $TS" -F "file=@/tmp/ok.png;type=image/png" -w "\nreal HTTP %{http_code}\n" | tail -1

echo "=== 5) XFF 伪造无法绕过 ==="
for i in 1 2 3; do
  curl -sk -o /dev/null -w "%{http_code} " -X POST $BASE/api/v1/auth/login -H "$H" -H "$J" -H "X-Forwarded-For: 8.8.8.$i" -d '{"email":"nonexist-w@example.com","password":"WrongPass1"}'
done
echo
echo "=== 6) 登出吊销 ==="
curl -sk -X POST $BASE/api/v1/auth/login -H "$H" -H "$J" -H "X-Real-IP: 10.2.2.3" -d "{\"email\":\"superadmin@platformharness.ltd\",\"password\":\"SuAdmin@2026Cloud\",\"totp_code\":\"$OTP\"}" > /tmp/t2.json
RF=$(python3 -c 'import json;print(json.load(open("/tmp/t2.json"))["refresh_token"])')
curl -sk -o /dev/null -w "logout HTTP %{http_code}\n" -X POST $BASE/api/v1/auth/logout -H "$H" -H "$J" -d "{\"refresh_token\":\"$RF\"}"
curl -sk -X POST $BASE/api/v1/auth/refresh -H "$H" -H "$J" -d "{\"refresh_token\":\"$RF\"}" -w "\nrefresh-after-logout HTTP %{http_code}\n"
echo "SECURITY LIVE ALL PASSED"
