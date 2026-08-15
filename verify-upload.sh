#!/bin/bash
BASE=https://127.0.0.1
H='Host: www.platformharness.ltd'
J='Content-Type: application/json'
SECRET=$(sudo docker exec harness-db psql -U harness -d harness -t -A -c "SELECT totp_secret FROM users WHERE email='superadmin@platformharness.ltd';")
OTP=$(sudo docker exec harness-backend python -c "import pyotp;print(pyotp.TOTP('$SECRET').now())")
curl -sk -X POST $BASE/api/v1/auth/login -H "$H" -H "$J" -d "{\"email\":\"superadmin@platformharness.ltd\",\"password\":\"SuAdmin@2026Cloud\",\"totp_code\":\"$OTP\"}" > /tmp/ts.json
TS=$(python3 -c 'import json;print(json.load(open("/tmp/ts.json"))["access_token"])')
python3 <<'PYEOF'
import struct, zlib
sig = bytes.fromhex('89504e470d0a1a0a')
ihdr = struct.pack('>IIBBBBB', 16, 16, 8, 2, 0, 0, 0)
raw = b''
for _ in range(16):
    raw += bytes.fromhex('00') + bytes.fromhex('804020') * 16
idat = zlib.compress(raw)
def chunk(t, d):
    return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xFFFFFFFF)
open('/tmp/ok.png', 'wb').write(sig + chunk(b'IHDR', ihdr) + chunk(b'IDAT', idat) + chunk(b'IEND', b''))
print('png ready', len(open('/tmp/ok.png','rb').read()), 'bytes')
PYEOF
curl -sk -X POST $BASE/api/v1/user/avatar -H "$H" -H "Authorization: Bearer $TS" -F "file=@/tmp/ok.png;type=image/png" -w "\nreal HTTP %{http_code}\n" | tail -1
echo "UPLOAD VERIFY DONE"
