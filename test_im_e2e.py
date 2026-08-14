"""IM P0 端到端测试：私信全流程 + 机器人广播 + 文本水印取证 + WS 实时推送
运行方式（backend 容器内）：
    docker exec -i harness-backend python < /tmp/test_im_e2e.py
"""
import asyncio
import io
import json
import sys

import httpx
import pyotp
from httpx import ASGITransport
from sqlalchemy import delete as _delete, select

sys.path.insert(0, "/app/backend")
from app.database import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Block, DmConversation, DmConversationMember, DmMessage, User  # noqa: E402
from app.services.bot import BOT_UID, ensure_bot  # noqa: E402
from app.services.watermark import encode_text_watermark  # noqa: E402

PASS = "TestPass123"


async def register(c, email, username):
    r = await c.post("/api/v1/auth/send-code", json={"email": email, "purpose": "register"})
    code = r.json().get("dev_code")
    r = await c.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": PASS, "code": code},
    )
    assert r.status_code == 201, r.text
    return r.json()


async def login(c, email):
    r = await c.post("/api/v1/auth/login", json={"email": email, "password": PASS})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def H(token):
    return {"Authorization": f"Bearer {token}"}


async def main():
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        # 0) 清理旧测试数据
        async with SessionLocal() as db:
            for email in ("alice-im@example.com", "bob-im@example.com", "carol-im@example.com"):
                u = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
                if u:
                    await db.execute(_delete(DmMessage).where(DmMessage.sender_id == u.uid))
                    await db.execute(_delete(Block).where((Block.uid == u.uid) | (Block.blocked_uid == u.uid)))
                    await db.delete(u)
            await db.commit()

        print("1. 注册 alice / bob")
        ua = await register(c, "alice-im@example.com", "alice_im")
        ub = await register(c, "bob-im@example.com", "bob_im")
        ta, tb = await login(c, "alice-im@example.com"), await login(c, "bob-im@example.com")
        alice_uid, bob_uid = ua["uid"], ub["uid"]
        print("   alice:", alice_uid, "bob:", bob_uid)

        print("2. 越权防护：不存在会话 → 404")
        r = await c.get("/api/v1/im/conversations/nonexist/messages", headers=H(ta))
        assert r.status_code == 404, r.text

        print("3. 发起会话（幂等）")
        r = await c.post("/api/v1/im/conversations", json={"user_id": bob_uid}, headers=H(ta))
        assert r.status_code == 200, r.text
        conv_id = r.json()["id"]
        r2 = await c.post("/api/v1/im/conversations", json={"user_id": bob_uid}, headers=H(ta))
        assert r2.json()["id"] == conv_id, "会话必须幂等"
        print("   conv:", conv_id)

        print("4. 边界：与自己/机器人/不存在用户")
        r = await c.post("/api/v1/im/conversations", json={"user_id": alice_uid}, headers=H(ta))
        assert r.status_code == 400
        await ensure_bot_session(c, ta)
        r = await c.post("/api/v1/im/conversations", json={"user_id": BOT_UID}, headers=H(ta))
        assert r.status_code == 400, r.text
        r = await c.post("/api/v1/im/conversations", json={"user_id": "no-such-user-000"}, headers=H(ta))
        assert r.status_code == 404

        print("5. alice 发消息 → bob 未读 1")
        r = await c.post(
            f"/api/v1/im/conversations/{conv_id}/messages",
            json={"kind": "text", "content": "你好 Bob，这是第一条"},
            headers=H(ta),
        )
        assert r.status_code == 200, r.text
        m1 = r.json()
        r = await c.get("/api/v1/im/conversations", headers=H(tb))
        bob_conv = [x for x in r.json()["items"] if x["id"] == conv_id][0]
        assert bob_conv["unread"] == 1, bob_conv
        assert bob_conv["last_message"]["content"] == "你好 Bob，这是第一条"
        r = await c.get("/api/v1/im/unread", headers=H(tb))
        assert r.json()["total"] >= 1

        print("6. bob 读取 + 已读回执")
        r = await c.get(f"/api/v1/im/conversations/{conv_id}/messages", headers=H(tb))
        assert len(r.json()["items"]) == 1
        await c.post(f"/api/v1/im/conversations/{conv_id}/read", headers=H(tb))
        r = await c.get("/api/v1/im/conversations", headers=H(ta))
        alice_conv = [x for x in r.json()["items"] if x["id"] == conv_id][0]
        assert alice_conv["other_last_read_at"] is not None, "bob 已读后 alice 应可见已读时间"
        assert alice_conv["unread"] == 0

        print("7. bob 回复 → alice 未读 1")
        r = await c.post(
            f"/api/v1/im/conversations/{conv_id}/messages",
            json={"kind": "text", "content": "收到，Alice！"},
            headers=H(tb),
        )
        assert r.status_code == 200
        r = await c.get("/api/v1/im/unread", headers=H(ta))
        assert r.json()["total"] == 1

        print("8. 撤回：本人 2 分钟内可撤；非本人 403；超时 400")
        r = await c.post(
            f"/api/v1/im/conversations/{conv_id}/messages",
            json={"kind": "text", "content": "这句话马上撤回"},
            headers=H(ta),
        )
        m2 = r.json()
        r = await c.post(f"/api/v1/im/messages/{m2['id']}/recall", headers=H(tb))
        assert r.status_code == 403
        r = await c.post(f"/api/v1/im/messages/{m2['id']}/recall", headers=H(ta))
        assert r.status_code == 200 and r.json()["status"] == "recalled"
        # 超时：改 DB created_time 到 3 分钟前
        async with SessionLocal() as db:
            from datetime import datetime, timedelta, timezone

            msg = await db.get(DmMessage, m2["id"])
            msg.created_time = datetime.now(timezone.utc) - timedelta(minutes=3)
            await db.commit()
        r = await c.post(
            f"/api/v1/im/conversations/{conv_id}/messages",
            json={"kind": "text", "content": "超时测试"},
            headers=H(ta),
        )
        m3 = r.json()
        r = await c.post(f"/api/v1/im/messages/{m3['id']}/recall", headers=H(ta))
        assert r.status_code == 200  # 刚发的还在窗口内
        async with SessionLocal() as db:
            msg = await db.get(DmMessage, m2["id"])
            msg.created_time = datetime.now(timezone.utc) - timedelta(minutes=3)
            await db.commit()
        r = await c.post(f"/api/v1/im/messages/{m2['id']}/recall", headers=H(ta))
        assert r.status_code == 400, r.text

        print("9. 隐藏会话（仅本人视图）")
        r = await c.delete(f"/api/v1/im/conversations/{conv_id}", headers=H(tb))
        assert r.status_code == 204
        r = await c.get("/api/v1/im/conversations", headers=H(tb))
        assert all(x["id"] != conv_id for x in r.json()["items"]), "bob 视图应隐藏"
        r = await c.get("/api/v1/im/conversations", headers=H(ta))
        assert any(x["id"] == conv_id for x in r.json()["items"]), "alice 视图应保留"
        # 重新打开解除隐藏
        r = await c.post("/api/v1/im/conversations", json={"user_id": alice_uid}, headers=H(tb))
        assert r.status_code == 200
        r = await c.get("/api/v1/im/conversations", headers=H(tb))
        assert any(x["id"] == conv_id for x in r.json()["items"])

        print("10. 用户搜索：排除自己/机器人/拉黑")
        r = await c.get("/api/v1/im/users?q=alice", headers=H(ta))
        names = [x["username"] for x in r.json()["items"]]
        assert "alice_im" not in names and "harness_official" not in names, names
        r = await c.get("/api/v1/im/users?q=harness", headers=H(ta))
        assert r.json()["items"] == []

        print("11. 图片消息")
        png = b"\x89PNG\r\n\x1a\n" + b"0" * 100
        r = await c.post(
            "/api/v1/im/upload",
            files={"file": ("t.png", io.BytesIO(png), "image/png")},
            headers=H(ta),
        )
        assert r.status_code == 200 and r.json()["url"].startswith("/uploads/im/"), r.text
        img_url = r.json()["url"]
        r = await c.post(
            f"/api/v1/im/conversations/{conv_id}/messages",
            json={"kind": "image", "content": img_url},
            headers=H(ta),
        )
        assert r.status_code == 200 and r.json()["kind"] == "image"

        print("12. 机器人：登录拒绝")
        async with SessionLocal() as db:
            bot = await ensure_bot(db)
        assert bot.is_bot
        r = await c.post("/api/v1/auth/login", json={"email": bot.email, "password": "whatever123"})
        assert r.status_code == 403, r.text

        print("13. 超级管理员 → 机器人全量广播")
        async with SessionLocal() as db:
            su = (await db.execute(select(User).where(User.email == "superadmin@platformharness.ltd"))).scalar_one()
            otp = pyotp.TOTP(su.totp_secret).now()
        r = await c.post(
            "/api/v1/auth/login",
            json={"email": "superadmin@platformharness.ltd", "password": "SuAdmin@2026Cloud", "totp_code": otp},
        )
        assert r.status_code == 200, r.text
        tsu = r.json()["access_token"]
        r = await c.post(
            "/api/v1/admin/im/broadcast",
            json={"content": "系统将于今晚 23:00 维护升级", "reason": "v0.11 发布"},
            headers=H(tsu),
        )
        assert r.status_code == 200 and r.json()["sent"] >= 2, r.text
        r = await c.get("/api/v1/im/conversations", headers=H(ta))
        bot_conv = [x for x in r.json()["items"] if x["other"]["uid"] == BOT_UID]
        assert bot_conv, "alice 应有机器人会话"
        assert bot_conv[0]["last_message"]["content"] == "系统将于今晚 23:00 维护升级"
        assert bot_conv[0]["unread"] >= 1
        r = await c.get("/api/v1/admin/im/history?limit=5", headers=H(tsu))
        assert r.json()["items"], "机器人发送记录应有数据"

        print("14. 定向私信")
        r = await c.post(
            "/api/v1/admin/im/dm",
            json={"user_id": bob_uid, "content": "你的工单 #123 已处理"},
            headers=H(tsu),
        )
        assert r.status_code == 200, r.text
        r = await c.get("/api/v1/im/conversations", headers=H(tb))
        bot_conv_b = [x for x in r.json()["items"] if x["other"]["uid"] == BOT_UID]
        assert bot_conv_b and "工单" in bot_conv_b[0]["last_message"]["content"]

        print("15. 文本水印取证")
        zw = encode_text_watermark(alice_uid, m1["id"], 1755234000)
        r = await c.post("/api/v1/im/decode-text", json={"text": "泄露内容" + zw}, headers=H(tsu))
        assert r.status_code == 200 and r.json()["matched"], r.text
        assert r.json()["user"]["uid"] == alice_uid and r.json()["message_id"] == m1["id"]
        assert r.json()["user"]["email"] is None, "最小化输出：不返回邮箱"
        r = await c.post("/api/v1/im/decode-text", json={"text": "没有水印的内容"}, headers=H(tsu))
        assert r.json()["matched"] is False
        r = await c.post("/api/v1/im/decode-text", json={"text": "x" + zw}, headers=H(ta))
        assert r.status_code == 403, "非 superadmin 必须 403"

        print("16. 拉黑双向禁止（服务端）")
        async with SessionLocal() as db:
            db.add(Block(uid=alice_uid, blocked_uid=bob_uid))
            await db.commit()
        r = await c.post(
            f"/api/v1/im/conversations/{conv_id}/messages",
            json={"kind": "text", "content": "拉黑后"},
            headers=H(ta),
        )
        assert r.status_code == 403, r.text
        r = await c.post(
            f"/api/v1/im/conversations/{conv_id}/messages",
            json={"kind": "text", "content": "反向也禁止"},
            headers=H(tb),
        )
        assert r.status_code == 403, r.text
        async with SessionLocal() as db:
            await db.execute(_delete(Block).where(Block.uid == alice_uid))
            await db.commit()

        print("17. WS 实时推送（连真实 uvicorn 8000）")
        import websockets

        async with websockets.connect(f"ws://127.0.0.1:8000/api/v1/im/ws?token={tb}") as ws:
            await ws.send(json.dumps({"type": "join", "conversation_id": conv_id}))
            # alice 经真实 HTTP 发消息
            async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as lc:
                r = await lc.post(
                    f"/api/v1/im/conversations/{conv_id}/messages",
                    json={"kind": "text", "content": "WS 实时推送测试"},
                    headers=H(ta),
                )
                assert r.status_code == 200
                mid4 = r.json()["id"]
            got = await asyncio.wait_for(ws.recv(), timeout=5)
            ev = json.loads(got)
            assert ev["type"] == "im.message" and ev["message"]["id"] == mid4, ev
            print("   ws im.message ok")
            # 撤回推送
            async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as lc:
                await lc.post(f"/api/v1/im/messages/{mid4}/recall", headers=H(ta))
            got2 = await asyncio.wait_for(ws.recv(), timeout=5)
            ev2 = json.loads(got2)
            assert ev2["type"] == "im.recalled" and ev2["message_id"] == mid4, ev2
            print("   ws im.recalled ok")

        print("18. 清理测试数据")
        async with SessionLocal() as db:
            for uid in (alice_uid, bob_uid):
                await db.execute(_delete(DmMessage).where(DmMessage.sender_id == uid))
                await db.execute(_delete(DmConversationMember).where(DmConversationMember.user_id == uid))
                await db.execute(_delete(DmConversation).where((DmConversation.user_a == uid) | (DmConversation.user_b == uid)))
                await db.execute(_delete(Block).where((Block.uid == uid) | (Block.blocked_uid == uid)))
                u = await db.get(User, uid)
                if u:
                    await db.delete(u)
            await db.commit()

    print("IM P0 E2E ALL PASSED")


async def ensure_bot_session(c, token):
    """确保机器人存在（启动时已建，这里仅兜底）"""
    async with SessionLocal() as db:
        await ensure_bot(db)


asyncio.run(main())
