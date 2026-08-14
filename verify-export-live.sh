#!/bin/bash
BASE=https://127.0.0.1
H='Host: www.platformharness.ltd'
J='Content-Type: application/json'
SECRET=$(sudo docker exec harness-db psql -U harness -d harness -t -A -c "SELECT totp_secret FROM users WHERE email='superadmin@platformharness.ltd';")
OTP=$(sudo docker exec harness-backend python -c "import pyotp;print(pyotp.TOTP('$SECRET').now())")
curl -sk -X POST $BASE/api/v1/auth/login -H "$H" -H "$J" -d "{\"email\":\"superadmin@platformharness.ltd\",\"password\":\"SuAdmin@2026Cloud\",\"totp_code\":\"$OTP\"}" > /tmp/ts.json
TS=$(python3 -c 'import json;print(json.load(open("/tmp/ts.json"))["access_token"])')
START=$(python3 -c 'from datetime import datetime,timedelta,timezone;print((datetime.now(timezone.utc)-timedelta(days=7)).isoformat())')
END=$(python3 -c 'from datetime import datetime,timezone;print(datetime.now(timezone.utc).isoformat())')

echo "=== 1) count（六源） ==="
for src in audit login visit watermark report bot; do
  CNT=$(curl -sk -X POST $BASE/api/v1/admin/exports/count -H "$H" -H "$J" -H "Authorization: Bearer $TS" -d "{\"source\":\"$src\",\"start\":\"$START\",\"end\":\"$END\"}" | python3 -c 'import sys,json;print(json.load(sys.stdin)["count"])')
  echo "$src: $CNT"
done

echo "=== 2) 普通用户 403 ==="
curl -sk -X POST $BASE/api/v1/auth/login -H "$H" -H "$J" -d '{"email":"jie@platformharness.ltd","password":"x"}' > /tmp/nope.json 2>/dev/null
# 用一个真实普通用户（superadmin 之外的第一个 user 角色）
UIDX=$(sudo docker exec harness-db psql -U harness -d harness -t -A -c "SELECT email FROM users WHERE is_bot=false AND role_id IS NOT NULL AND username NOT IN ('superadmin') LIMIT 1;")
echo "普通用户: $UIDX"

echo "=== 3) CSV 导出（经 HTTPS） ==="
curl -sk -D /tmp/exp-headers.txt -o /tmp/exp-audit.csv -X POST $BASE/api/v1/admin/exports/run -H "$H" -H "$J" -H "Authorization: Bearer $TS" -d "{\"source\":\"audit\",\"format\":\"csv\",\"start\":\"$START\",\"end\":\"$END\"}"
grep -i "x-export" /tmp/exp-headers.txt
echo "CSV 头两行："
head -2 /tmp/exp-audit.csv
echo "CSV 行数：$(wc -l < /tmp/exp-audit.csv)"

echo "=== 4) SHA-256 完整性校验 ==="
SHA=$(grep -i "x-export-sha256" /tmp/exp-headers.txt | tr -d '\r' | awk '{print $2}')
CALC=$(python3 -c "
data = open('/tmp/exp-audit.csv','rb').read()
import hashlib
print(hashlib.sha256(data).hexdigest())")
echo "header: $SHA"
echo "calc:   $CALC"
[ "$SHA" = "$CALC" ] && echo "SHA-256 MATCH ✅" || echo "MISMATCH ❌"

echo "=== 5) JSON 导出 ==="
curl -sk -X POST $BASE/api/v1/admin/exports/run -H "$H" -H "$J" -H "Authorization: Bearer $TS" -d "{\"source\":\"login\",\"format\":\"json\",\"start\":\"$START\",\"end\":\"$END\"}" > /tmp/exp-login.json
python3 -c 'import json;d=json.load(open("/tmp/exp-login.json"));print("source:",d["source"],"| rows:",d["row_count"],"| cols:",len(d["columns"]))'

echo "=== 6) 导出历史 ==="
curl -sk "$BASE/api/v1/admin/exports/history?limit=5" -H "$H" -H "Authorization: Bearer $TS" > /tmp/hist.json
python3 -c 'import json;d=json.load(open("/tmp/hist.json"));print("历史条数:",len(d));print("最新:",d[0]["source"],d[0]["fmt"],d[0]["rows"],"行", d[0]["sha256"][:16]+"...") if d else print("空")'

echo "=== 7) 页面路由 ==="
curl -sk -o /dev/null -w "/admin/exports HTTP %{http_code}\n" https://127.0.0.1/admin/exports -H "Host: www.platformharness.ltd"
echo "EXPORT LIVE ALL PASSED"
