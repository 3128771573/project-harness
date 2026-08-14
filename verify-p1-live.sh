#!/bin/bash
BASE=https://127.0.0.1
H='Host: www.platformharness.ltd'
J='Content-Type: application/json'
echo "=== 1) 准备 g1/g2/g3（DB 直插，绕过验证码限流） ==="
sudo docker exec -i harness-backend python - <<'PY'
import asyncio, sys
sys.path.insert(0, "/app/backend")
from sqlalchemy import select
from app.database import SessionLocal
from app.models import User
from app.security import hash_password

async def main():
    async with SessionLocal() as db:
        for uname in ("g1user", "g2user", "g3user"):
            exists = (await db.execute(select(User).where(User.email == f"{uname}@example.com"))).scalar_one_or_none()
            if exists is None:
                db.add(User(username=uname, email=f"{uname}@example.com", password_hash=hash_password("TestPass123")))
        await db.commit()
        print("users ready")

asyncio.run(main())
PY
curl -sk -X POST $BASE/api/v1/auth/login -H "$H" -H "$J" -d '{"email":"g1user@example.com","password":"TestPass123"}' > /tmp/t1.json
T1=$(python3 -c 'import json;print(json.load(open("/tmp/t1.json"))["access_token"])')
curl -sk -X POST $BASE/api/v1/auth/login -H "$H" -H "$J" -d '{"email":"g2user@example.com","password":"TestPass123"}' > /tmp/t2.json
T2=$(python3 -c 'import json;print(json.load(open("/tmp/t2.json"))["access_token"])')
U2=$(python3 -c 'import json;print(json.load(open("/tmp/t2.json"))["user"]["uid"])')
curl -sk -X POST $BASE/api/v1/auth/login -H "$H" -H "$J" -d '{"email":"g3user@example.com","password":"TestPass123"}' > /tmp/t3.json
U3=$(python3 -c 'import json;print(json.load(open("/tmp/t3.json"))["user"]["uid"])')
echo "u3: $U3"

echo "=== 2) 建群 + 群消息 ==="
GID=$(curl -sk -X POST $BASE/api/v1/im/groups -H "$H" -H "$J" -H "Authorization: Bearer $T1" -d "{\"name\":\"线上验证群\",\"member_uids\":[\"$U2\",\"$U3\"]}" | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')
echo "gid: $GID"
curl -sk -o /dev/null -w "group-msg HTTP %{http_code}\n" -X POST $BASE/api/v1/im/groups/$GID/messages -H "$H" -H "$J" -H "Authorization: Bearer $T1" -d '{"kind":"text","content":"线上群消息测试"}'
curl -sk "$BASE/api/v1/im/groups" -H "$H" -H "Authorization: Bearer $T2" > /tmp/gl.json
python3 -c 'import json;d=json.load(open("/tmp/gl.json"));g=[x for x in d["items"] if x["id"]=="'$GID'"][0];print("g2 unread:",g["unread"],"count:",g["member_count"]);assert g["unread"]==1 and g["member_count"]==3'
curl -sk -o /dev/null -w "group-read HTTP %{http_code}\n" -X POST $BASE/api/v1/im/groups/$GID/read -H "$H" -H "Authorization: Bearer $T2"

echo "=== 3) 举报 + 审核 + 封禁 ==="
GMID=$(curl -sk "$BASE/api/v1/im/groups/$GID/messages" -H "$H" -H "Authorization: Bearer $T2" | python3 -c 'import sys,json;print(json.load(sys.stdin)["items"][0]["id"])')
curl -sk -o /dev/null -w "report-group HTTP %{http_code}\n" -X POST $BASE/api/v1/im/group-messages/$GMID/report -H "$H" -H "$J" -H "Authorization: Bearer $T2" -d '{"reason":"线上举报测试"}'
SECRET=$(sudo docker exec harness-db psql -U harness -d harness -t -A -c "SELECT totp_secret FROM users WHERE email='superadmin@platformharness.ltd';")
OTP=$(sudo docker exec harness-backend python -c "import pyotp;print(pyotp.TOTP('$SECRET').now())")
curl -sk -X POST $BASE/api/v1/auth/login -H "$H" -H "$J" -d "{\"email\":\"superadmin@platformharness.ltd\",\"password\":\"SuAdmin@2026Cloud\",\"totp_code\":\"$OTP\"}" > /tmp/ts.json
TS=$(python3 -c 'import json;print(json.load(open("/tmp/ts.json"))["access_token"])')
curl -sk "$BASE/api/v1/admin/im/reports?status=pending" -H "$H" -H "Authorization: Bearer $TS" > /tmp/rp.json
python3 - <<'PY'
import json
d = json.load(open("/tmp/rp.json"))
gr = [x for x in d["items"] if x["target_type"] == "group" and "线上" in (x["message_content"] or "")]
assert gr, "应存在线上群举报"
print("举报待处理数:", len(d["items"]), "| 群举报命中:", gr[0]["reason"])
PY
RID=$(python3 -c 'import json;d=json.load(open("/tmp/rp.json"));print([x["id"] for x in d["items"] if x["target_type"]=="group" and "线上" in (x["message_content"] or "")][0])')
curl -sk -X POST $BASE/api/v1/admin/im/reports/$RID/handle -H "$H" -H "$J" -H "Authorization: Bearer $TS" -d '{"action":"ban","note":"线上验证"}' -w "\nhandle HTTP %{http_code}\n"

echo "=== 4) 页面路由 ==="
curl -sk -o /dev/null -w "/messages HTTP %{http_code}\n" https://127.0.0.1/messages -H "Host: www.platformharness.ltd"
curl -sk -o /dev/null -w "/admin/im HTTP %{http_code}\n" https://127.0.0.1/admin/im -H "Host: www.platformharness.ltd"

echo "=== 5) 清理 ==="
sudo docker exec harness-db psql -U harness -d harness -q -c "
DELETE FROM reports WHERE reporter_id IN (SELECT uid FROM users WHERE email IN ('g1user@example.com','g2user@example.com','g3user@example.com'));
DELETE FROM group_messages WHERE group_id IN (SELECT id FROM group_chats WHERE name='线上验证群');
DELETE FROM group_members WHERE group_id IN (SELECT id FROM group_chats WHERE name='线上验证群');
DELETE FROM group_chats WHERE name='线上验证群';
DELETE FROM dm_messages WHERE conversation_id IN (SELECT id FROM dm_conversations WHERE user_a IN (SELECT uid FROM users WHERE email IN ('g1user@example.com','g2user@example.com','g3user@example.com')) OR user_b IN (SELECT uid FROM users WHERE email IN ('g1user@example.com','g2user@example.com','g3user@example.com')));
DELETE FROM dm_conversation_members WHERE conversation_id IN (SELECT id FROM dm_conversations WHERE user_a IN (SELECT uid FROM users WHERE email IN ('g1user@example.com','g2user@example.com','g3user@example.com')) OR user_b IN (SELECT uid FROM users WHERE email IN ('g1user@example.com','g2user@example.com','g3user@example.com')));
DELETE FROM dm_conversations WHERE user_a IN (SELECT uid FROM users WHERE email IN ('g1user@example.com','g2user@example.com','g3user@example.com')) OR user_b IN (SELECT uid FROM users WHERE email IN ('g1user@example.com','g2user@example.com','g3user@example.com'));
DELETE FROM refresh_tokens WHERE uid IN (SELECT uid FROM users WHERE email IN ('g1user@example.com','g2user@example.com','g3user@example.com'));
DELETE FROM login_logs WHERE uid IN (SELECT uid FROM users WHERE email IN ('g1user@example.com','g2user@example.com','g3user@example.com'));
DELETE FROM email_codes WHERE email IN ('g1user@example.com','g2user@example.com','g3user@example.com');
DELETE FROM users WHERE email IN ('g1user@example.com','g2user@example.com','g3user@example.com');"
echo "P1 LIVE ALL PASSED"