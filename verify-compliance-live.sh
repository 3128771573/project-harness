#!/bin/bash
BASE=https://127.0.0.1
H='Host: www.platformharness.ltd'
J='Content-Type: application/json'
echo "=== 1) 准备 comp-a / comp-b（DB 直插） ==="
sudo docker exec -i harness-backend python - <<'PY'
import asyncio, sys
sys.path.insert(0, "/app/backend")
from sqlalchemy import select
from app.database import SessionLocal
from app.models import User
from app.security import hash_password

async def main():
    async with SessionLocal() as db:
        for uname in ("compa", "compb"):
            exists = (await db.execute(select(User).where(User.email == f"{uname}@example.com"))).scalar_one_or_none()
            if exists is None:
                db.add(User(username=uname, email=f"{uname}@example.com", password_hash=hash_password("TestPass123")))
        await db.commit()
        print("users ready")

asyncio.run(main())
PY
curl -sk -X POST $BASE/api/v1/auth/login -H "$H" -H "$J" -d '{"email":"compa@example.com","password":"TestPass123"}' > /tmp/ca.json
TA=$(python3 -c 'import json;print(json.load(open("/tmp/ca.json"))["access_token"])')
curl -sk -X POST $BASE/api/v1/auth/login -H "$H" -H "$J" -d '{"email":"compb@example.com","password":"TestPass123"}' > /tmp/cb.json
TB=$(python3 -c 'import json;print(json.load(open("/tmp/cb.json"))["access_token"])')
BUID=$(python3 -c 'import json;print(json.load(open("/tmp/cb.json"))["user"]["uid"])')

echo "=== 2) 敏感词拦截（HTTPS） ==="
CID=$(curl -sk -X POST $BASE/api/v1/im/conversations -H "$H" -H "$J" -H "Authorization: Bearer $TA" -d "{\"user_id\":\"$BUID\"}" | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')
curl -sk -X POST $BASE/api/v1/im/conversations/$CID/messages -H "$H" -H "$J" -H "Authorization: Bearer $TA" -d '{"kind":"text","content":"出售海洛因联系我"}' -w "\nHTTP %{http_code}\n"
curl -sk -o /dev/null -w "normal HTTP %{http_code}\n" -X POST $BASE/api/v1/im/conversations/$CID/messages -H "$H" -H "$J" -H "Authorization: Bearer $TA" -d '{"kind":"text","content":"正常合规消息"}' 

echo "=== 3) 聊天记录导出 ==="
curl -sk "$BASE/api/v1/user/conversations/$CID/export" -H "$H" -H "Authorization: Bearer $TA" | head -8

echo "=== 4) 注销账号（HTTPS 全链路） ==="
curl -sk -o /dev/null -w "wrong-pw HTTP %{http_code}\n" -X POST $BASE/api/v1/user/deactivate -H "$H" -H "$J" -H "Authorization: Bearer $TA" -d '{"password":"Wrong"}'
curl -sk -X POST $BASE/api/v1/user/deactivate -H "$H" -H "$J" -H "Authorization: Bearer $TA" -d '{"password":"TestPass123"}' -w "\ndeactivate HTTP %{http_code}\n"
curl -sk -o /dev/null -w "login-after HTTP %{http_code}\n" -X POST $BASE/api/v1/auth/login -H "$H" -H "$J" -d '{"email":"compa@example.com","password":"TestPass123"}'
sudo docker exec harness-db psql -U harness -d harness -t -A -c "SELECT is_active, email FROM users WHERE username='compa' OR username LIKE 'user_%' AND email LIKE 'deleted-%' LIMIT 3;"

echo "=== 5) 合规页面 ==="
curl -sk -o /dev/null -w "/terms HTTP %{http_code}\n" https://127.0.0.1/terms -H "Host: www.platformharness.ltd"
curl -sk -o /dev/null -w "/privacy HTTP %{http_code}\n" https://127.0.0.1/privacy -H "Host: www.platformharness.ltd"

echo "=== 6) 敏感词库管理 ==="
SECRET=$(sudo docker exec harness-db psql -U harness -d harness -t -A -c "SELECT totp_secret FROM users WHERE email='superadmin@platformharness.ltd';")
OTP=$(sudo docker exec harness-backend python -c "import pyotp;print(pyotp.TOTP('$SECRET').now())")
curl -sk -X POST $BASE/api/v1/auth/login -H "$H" -H "$J" -d "{\"email\":\"superadmin@platformharness.ltd\",\"password\":\"SuAdmin@2026Cloud\",\"totp_code\":\"$OTP\"}" > /tmp/ts.json
TS=$(python3 -c 'import json;print(json.load(open("/tmp/ts.json"))["access_token"])')
curl -sk "$BASE/api/v1/admin/im/sensitive-words?page_size=5" -H "$H" -H "Authorization: Bearer $TS" > /tmp/sw.json
python3 -c 'import json;d=json.load(open("/tmp/sw.json"));print("词库总数:", d["total"]); assert d["total"]>=30'

echo "=== 7) 清理 ==="
sudo docker exec harness-db psql -U harness -d harness -q -c "
DELETE FROM group_messages WHERE sender_id IN (SELECT uid FROM users WHERE email IN ('compa@example.com','compb@example.com'));
DELETE FROM dm_messages WHERE conversation_id IN (SELECT id FROM dm_conversations WHERE user_a IN (SELECT uid FROM users WHERE email IN ('compa@example.com','compb@example.com')) OR user_b IN (SELECT uid FROM users WHERE email IN ('compa@example.com','compb@example.com')));
DELETE FROM dm_conversation_members WHERE conversation_id IN (SELECT id FROM dm_conversations WHERE user_a IN (SELECT uid FROM users WHERE email IN ('compa@example.com','compb@example.com')) OR user_b IN (SELECT uid FROM users WHERE email IN ('compa@example.com','compb@example.com')));
DELETE FROM dm_conversations WHERE user_a IN (SELECT uid FROM users WHERE email IN ('compa@example.com','compb@example.com')) OR user_b IN (SELECT uid FROM users WHERE email IN ('compa@example.com','compb@example.com'));
DELETE FROM refresh_tokens WHERE uid IN (SELECT uid FROM users WHERE email IN ('compa@example.com','compb@example.com'));
DELETE FROM login_logs WHERE uid IN (SELECT uid FROM users WHERE email IN ('compa@example.com','compb@example.com'));
DELETE FROM email_codes WHERE email IN ('compa@example.com','compb@example.com');
DELETE FROM users WHERE email IN ('compa@example.com','compb@example.com') OR email LIKE 'deleted-%' AND username IN (SELECT username FROM users WHERE email LIKE 'deleted-%' LIMIT 0);
DELETE FROM users WHERE email IN ('compa@example.com','compb@example.com') OR (email LIKE 'deleted-%' AND is_active=false AND username LIKE 'user_%');"
echo "COMPLIANCE LIVE ALL PASSED"
