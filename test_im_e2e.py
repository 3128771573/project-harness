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
from app.models import AuditLog, Block, DmConversation, DmConversationMember, DmMessage, EmailCode, LoginLog, RefreshToken, Report, User  # noqa: E402
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
    test_uids: list[str] = []
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        print("0. 清理旧测试数据")
        async with SessionLocal() as db:
            emails = ("alice-im@example.com", "bob-im@example.com", "carol-im@example.com")
            from app.models import Report

            await db.execute(_delete(EmailCode).where(EmailCode.email.in_(emails)))
            urows = (await db.execute(select(User).where(User.email.in_(emails)))).scalars().all()
            uids = list(dict.fromkeys([u.uid for u in urows] + test_uids))
            if uids:
                from app.models import GroupChat, GroupMember, GroupMessage, WatermarkGrant, WatermarkLog

                # 按「群主或成员」维度收集相关群（覆盖孤儿群/仅成员群）
                gcids = [
                    gid for (gid,) in (
                        await db.execute(select(GroupChat.id).where(GroupChat.owner_id.in_(uids)))
                    ).all()
                ]
                gcids += [
                    gid for (gid,) in (
                        await db.execute(select(GroupMember.group_id).where(GroupMember.user_id.in_(uids)))
                    ).all()
                ]
                gcids = list(dict.fromkeys(gcids))
                if gcids:
                    await db.execute(_delete(GroupMessage).where(GroupMessage.group_id.in_(gcids)))
                    await db.execute(_delete(GroupMember).where(GroupMember.group_id.in_(gcids)))
                    await db.execute(_delete(GroupChat).where(GroupChat.id.in_(gcids)))
                await db.execute(_delete(WatermarkGrant).where(WatermarkGrant.user_id.in_(uids)))
                await db.execute(_delete(WatermarkLog).where(WatermarkLog.actor_id.in_(uids)))
                conv_ids = [
                    cid for (cid,) in (
                        await db.execute(
                            select(DmConversation.id).where(
                                (DmConversation.user_a.in_(uids)) | (DmConversation.user_b.in_(uids))
                            )
                        )
                    ).all()
                ]
                if conv_ids:
                    await db.execute(_delete(DmMessage).where(DmMessage.conversation_id.in_(conv_ids)))
                    await db.execute(_delete(DmConversationMember).where(DmConversationMember.conversation_id.in_(conv_ids)))
                    await db.execute(_delete(DmConversation).where(DmConversation.id.in_(conv_ids)))
                await db.execute(_delete(Block).where((Block.uid.in_(uids)) | (Block.blocked_uid.in_(uids))))
                await db.execute(_delete(Report).where((Report.reporter_id.in_(uids)) | (Report.target_id.in_(conv_ids))))
                await db.execute(_delete(RefreshToken).where(RefreshToken.uid.in_(uids)))
                await db.execute(_delete(LoginLog).where(LoginLog.uid.in_(uids)))
                await db.execute(_delete(User).where(User.uid.in_(uids)))
            await db.commit()

        print("1. 注册 alice / bob")
        ua = await register(c, "alice-im@example.com", "alice_im")
        ub = await register(c, "bob-im@example.com", "bob_im")
        ta, tb = await login(c, "alice-im@example.com"), await login(c, "bob-im@example.com")
        alice_uid, bob_uid = ua["user"]["uid"], ub["user"]["uid"]
        test_uids.extend([alice_uid, bob_uid])
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
        # 超时：直接造一条 10 分钟前的消息 → 撤回应 400
        async with SessionLocal() as db:
            old = DmMessage(conversation_id=conv_id, sender_id=alice_uid, content="很旧的消息", kind="text", status="active")
            old.created_time = datetime.now(timezone.utc) - timedelta(minutes=10)
            db.add(old)
            await db.commit()
            old_id = old.id
        r = await c.post(f"/api/v1/im/messages/{old_id}/recall", headers=H(ta))
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
        hit_names = [x["username"] for x in r.json()["items"]]
        assert "harness_official" not in hit_names and "alice_im" not in hit_names, hit_names

        print("11. 图片消息")
        import struct as _struct
        import zlib as _zlib

        def _make_png(w=4, h=4):
            sig = b"\x89PNG\r\n\x1a\n"
            ihdr = _struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
            raw = b""
            for _ in range(h):
                raw += b"\x00" + b"\x80\x40\x20" * w
            idat = _zlib.compress(raw)

            def chunk(t, d):
                return _struct.pack(">I", len(d)) + t + d + _struct.pack(">I", _zlib.crc32(t + d) & 0xFFFFFFFF)

            return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")

        png = _make_png()
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
        assert "email" not in r.json()["user"], "最小化输出：不返回邮箱"
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

        print("16b. 拉黑管理（API 全流程）")
        r = await c.post("/api/v1/im/blocks", json={"user_id": bob_uid}, headers=H(ta))
        assert r.status_code == 201, r.text
        assert r.json()["blocked"]["uid"] == bob_uid
        r = await c.post("/api/v1/im/blocks", json={"user_id": bob_uid}, headers=H(ta))
        assert r.status_code == 409, "重复拉黑应 409"
        r = await c.post("/api/v1/im/blocks", json={"user_id": alice_uid}, headers=H(ta))
        assert r.status_code == 400, "拉黑自己应 400"
        r = await c.post("/api/v1/im/blocks", json={"user_id": BOT_UID}, headers=H(ta))
        assert r.status_code == 404, "拉黑机器人应 404"
        r = await c.get("/api/v1/im/blocks", headers=H(ta))
        assert len(r.json()) == 1 and r.json()[0]["blocked"]["uid"] == bob_uid
        # 拉黑后双方互发 403
        r = await c.post(
            f"/api/v1/im/conversations/{conv_id}/messages",
            json={"kind": "text", "content": "api 拉黑后"},
            headers=H(ta),
        )
        assert r.status_code == 403
        r = await c.post(
            f"/api/v1/im/conversations/{conv_id}/messages",
            json={"kind": "text", "content": "api 拉黑反向"},
            headers=H(tb),
        )
        assert r.status_code == 403
        # 解除后恢复
        r = await c.delete(f"/api/v1/im/blocks/{bob_uid}", headers=H(ta))
        assert r.status_code == 204
        r = await c.post(
            f"/api/v1/im/conversations/{conv_id}/messages",
            json={"kind": "text", "content": "解除拉黑后恢复"},
            headers=H(ta),
        )
        assert r.status_code == 200

        print("16c. 举报落库（P0 数据，P1 审核）")
        r = await c.post(f"/api/v1/im/messages/{m1['id']}/report", json={"reason": "广告骚扰"}, headers=H(tb))
        assert r.status_code == 204, r.text
        r = await c.post("/api/v1/im/messages/nonexist-msg/report", json={"reason": "x"}, headers=H(tb))
        assert r.status_code == 404
        async with SessionLocal() as db:
            from app.models import Report

            rep = (
                await db.execute(
                    select(Report).where(Report.target_id == m1["id"], Report.reporter_id == bob_uid)
                )
            ).scalar_one_or_none()
            assert rep is not None and rep.status == "pending" and rep.target_type == "dm", "举报应落库 pending"

        print("16d. 消息长度边界（max 4000）")
        r = await c.post(
            f"/api/v1/im/conversations/{conv_id}/messages",
            json={"kind": "text", "content": "长" * 3999},
            headers=H(ta),
        )
        assert r.status_code == 200, r.text
        r = await c.post(
            f"/api/v1/im/conversations/{conv_id}/messages",
            json={"kind": "text", "content": "长" * 4001},
            headers=H(ta),
        )
        assert r.status_code == 422, "超长应 422"

        print("17. WS 实时推送（连真实 uvicorn 8000）")
        import websockets

        async with websockets.connect(
            f"ws://127.0.0.1:8000/api/v1/im/ws?token={tb}",
            origin="https://www.platformharness.ltd",
        ) as ws:
            await ws.send(json.dumps({"type": "join", "conversation_id": conv_id}))
            await asyncio.sleep(0.5)  # 等服务端处理 join
            # alice 经真实 HTTP 发消息
            async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as lc:
                r = await lc.post(
                    f"/api/v1/im/conversations/{conv_id}/messages",
                    json={"kind": "text", "content": "WS 实时推送测试"},
                    headers=H(ta),
                )
                assert r.status_code == 200
                mid4 = r.json()["id"]
            # 轮询直到收到目标事件（可能先到 conv_update）
            async def wait_event(etype, msg_id=None):
                while True:
                    ev = json.loads(await asyncio.wait_for(ws.recv(), timeout=8))
                    if ev["type"] == etype and (msg_id is None or ev.get("message", {}).get("id") == msg_id or ev.get("message_id") == msg_id):
                        return ev
            ev = await wait_event("im.message", mid4)
            print("   ws im.message ok")
            # 撤回推送
            async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as lc:
                await lc.post(f"/api/v1/im/messages/{mid4}/recall", headers=H(ta))
            ev2 = await wait_event("im.recalled", mid4)
            print("   ws im.recalled ok")
            # 心跳：ping → pong
            await ws.send(json.dumps({"type": "ping"}))
            got3 = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
            assert got3["type"] == "pong", got3
            print("   ws ping/pong ok")


        print("19. 群聊：建群 / 消息 / 未读 / 撤回 / 举报")
        r = await c.post("/api/v1/im/groups", json={"name": "P1测试群", "member_uids": [bob_uid]}, headers=H(ta))
        assert r.status_code == 201, r.text
        gid = r.json()["id"]
        assert r.json()["owner_id"] == alice_uid and r.json()["member_count"] == 2
        r = await c.post(f"/api/v1/im/groups/{gid}/messages", json={"kind": "text", "content": "大家好，欢迎进群"}, headers=H(ta))
        assert r.status_code == 201, r.text
        gm1 = r.json()
        r = await c.get("/api/v1/im/groups", headers=H(tb))
        bg = [x for x in r.json()["items"] if x["id"] == gid][0]
        assert bg["unread"] == 1 and bg["my_role"] == "member", bg
        # bob 读群消息
        r = await c.get(f"/api/v1/im/groups/{gid}/messages", headers=H(tb))
        assert len(r.json()["items"]) == 1 and r.json()["items"][0]["content"] == "大家好，欢迎进群"
        await c.post(f"/api/v1/im/groups/{gid}/read", headers=H(tb))
        # bob 回复 → alice 未读
        r = await c.post(f"/api/v1/im/groups/{gid}/messages", json={"kind": "text", "content": "收到，群主"}, headers=H(tb))
        assert r.status_code == 201
        r = await c.get("/api/v1/im/groups", headers=H(ta))
        ag = [x for x in r.json()["items"] if x["id"] == gid][0]
        assert ag["unread"] == 1
        # 群消息撤回：alice 撤回自己的 gm1；bob 撤回 alice 的 → 403
        r = await c.post(f"/api/v1/im/group-messages/{gm1['id']}/recall", headers=H(ta))
        assert r.status_code == 200 and r.json()["status"] == "recalled"
        r = await c.post(f"/api/v1/im/group-messages/{gm1['id']}/recall", headers=H(tb))
        assert r.status_code == 403
        # 群消息举报 → reports target_type=group
        r = await c.post(f"/api/v1/im/group-messages/{gm1['id']}/report", json={"reason": "群内骚扰"}, headers=H(tb))
        assert r.status_code == 204
        # 群未读计入总角标
        r = await c.get("/api/v1/im/unread", headers=H(ta))
        assert r.json()["total"] >= 1
        # 非成员访问 → 404
        r = await c.get(f"/api/v1/im/groups/{gid}/messages", headers=H(tsu))
        assert r.status_code == 404
        print("   gid:", gid)

        print("20. 群聊：成员管理 / 角色 / 转让 / 解散")
        # member 不能改群名
        r = await c.put(f"/api/v1/im/groups/{gid}", json={"name": "越权改名"}, headers=H(tb))
        assert r.status_code == 403
        # owner 改名 + 公告
        r = await c.put(f"/api/v1/im/groups/{gid}", json={"name": "P1测试群2", "announcement": "欢迎新成员"}, headers=H(ta))
        assert r.status_code == 200 and r.json()["name"] == "P1测试群2"
        # 注册 carol 并邀请
        uc = await register(c, "carol-im@example.com", "carol_im")
        carol_uid = uc["user"]["uid"]
        test_uids.append(carol_uid)
        r = await c.post(f"/api/v1/im/groups/{gid}/invite", json={"user_ids": [carol_uid]}, headers=H(tb))
        assert r.status_code == 403, "member 不能邀请"
        # 提 bob 为 admin（DB 直改）
        async with SessionLocal() as db:
            from app.models import GroupMember as _GM

            bm = (await db.execute(select(_GM).where(_GM.group_id == gid, _GM.user_id == bob_uid))).scalar_one()
            bm.role = "admin"
            await db.commit()
        r = await c.post(f"/api/v1/im/groups/{gid}/invite", json={"user_ids": [carol_uid]}, headers=H(tb))
        assert r.status_code == 200 and any(m["user"]["uid"] == carol_uid for m in r.json()["members"])
        # 踢人：admin 踢 member carol；admin 踢 owner → 400
        r = await c.post(f"/api/v1/im/groups/{gid}/kick", json={"user_id": carol_uid}, headers=H(tb))
        assert r.status_code == 200
        r = await c.post(f"/api/v1/im/groups/{gid}/kick", json={"user_id": alice_uid}, headers=H(tb))
        assert r.status_code == 400, "不能踢群主"
        # carol 重新邀请加入后自己退群
        await c.post(f"/api/v1/im/groups/{gid}/invite", json={"user_ids": [carol_uid]}, headers=H(ta))
        tc = await login(c, "carol-im@example.com")
        r = await c.post(f"/api/v1/im/groups/{gid}/leave", headers=H(tc))
        assert r.status_code == 204
        # owner 不能直接退群
        r = await c.post(f"/api/v1/im/groups/{gid}/leave", headers=H(ta))
        assert r.status_code == 400
        # 转让群主 → bob 变 owner
        r = await c.post(f"/api/v1/im/groups/{gid}/transfer", json={"user_id": bob_uid}, headers=H(ta))
        assert r.status_code == 200
        r = await c.get(f"/api/v1/im/groups/{gid}", headers=H(tb))
        assert r.json()["owner_id"] == bob_uid
        # 新群主解散
        r = await c.delete(f"/api/v1/im/groups/{gid}", headers=H(tb))
        assert r.status_code == 204
        r = await c.get("/api/v1/im/groups", headers=H(tb))
        assert all(x["id"] != gid for x in r.json()["items"])

        print("21. 举报审核（Admin）")
        r = await c.get("/api/v1/admin/im/reports?status=pending", headers=H(tsu))
        items = r.json()["items"]
        dm_rep = [x for x in items if x["target_type"] == "dm" and x["target_id"] == m1["id"]]
        gr_rep = [x for x in items if x["target_type"] == "group" and x["target_id"] == gm1["id"]]
        assert dm_rep and gr_rep, "两条举报都应在待处理队列"
        assert dm_rep[0]["message_content"] == "你好 Bob，这是第一条"
        # 删除消息处理
        rid = dm_rep[0]["id"]
        r = await c.post(f"/api/v1/admin/im/reports/{rid}/handle", json={"action": "delete", "note": "违规内容"}, headers=H(tsu))
        assert r.status_code == 200 and r.json()["result"] == "消息已删除", r.text
        # 重复处理 → 400
        r = await c.post(f"/api/v1/admin/im/reports/{rid}/handle", json={"action": "ignore"}, headers=H(tsu))
        assert r.status_code == 400
        # 消息状态变为 removed（bob 视角）
        r = await c.get(f"/api/v1/im/conversations/{conv_id}/messages", headers=H(tb))
        m1_now = [x for x in r.json()["items"] if x["id"] == m1["id"]][0]
        assert m1_now["status"] == "removed", m1_now
        # 机器人告知举报者（bob 的机器人会话出现处理结果）
        r = await c.get("/api/v1/im/conversations", headers=H(tb))
        bot_conv_b = [x for x in r.json()["items"] if x["other"]["uid"] == BOT_UID]
        assert bot_conv_b and "举报处理结果" in bot_conv_b[0]["last_message"]["content"], "举报者应收到机器人处理结果"
        # 封禁处理
        r = await c.get("/api/v1/admin/im/reports?status=pending", headers=H(tsu))
        gr_rep = [x for x in r.json()["items"] if x["target_type"] == "group" and x["target_id"] == gm1["id"]][0]
        r = await c.post(f"/api/v1/admin/im/reports/{gr_rep['id']}/handle", json={"action": "ban"}, headers=H(tsu))
        assert r.status_code == 200
        async with SessionLocal() as db:
            banned = (await db.execute(select(User).where(User.uid == alice_uid))).scalar_one()
            assert banned.is_active is False, "被举报消息发送者应被封禁"
            banned.is_active = True  # 恢复，供后续步骤使用
            await db.commit()

        print("22. 水印取证授权体系")
        # 未授权用户 403（已覆盖 step 15；这里验证 grant 流程）
        r = await c.post("/api/v1/admin/im/watermark/grants", json={"user_id": alice_uid, "quota_type": "times", "max_uses": 2}, headers=H(tsu))
        assert r.status_code == 201, r.text
        grant_id = r.json()["id"]
        zw_a = encode_text_watermark(alice_uid, m1["id"], 1755234000)
        # 命中 1 → 扣 1
        r = await c.post("/api/v1/im/decode-text", json={"text": "泄密" + zw_a}, headers=H(ta))
        assert r.status_code == 200 and r.json()["matched"], r.text
        # 命中 2 → 扣 2
        r = await c.post("/api/v1/im/decode-text", json={"text": "再泄密" + zw_a}, headers=H(ta))
        assert r.status_code == 200
        # 第 3 次（额度耗尽）→ 403
        r = await c.post("/api/v1/im/decode-text", json={"text": "三连" + zw_a}, headers=H(ta))
        assert r.status_code == 403, r.text
        # 失败不扣额度：新授权 1 次 → 先失败（无有效水印）再成功
        r = await c.post("/api/v1/admin/im/watermark/grants", json={"user_id": alice_uid, "quota_type": "times", "max_uses": 1}, headers=H(tsu))
        assert r.status_code == 201
        r = await c.post("/api/v1/im/decode-text", json={"text": "没有水印的普通文本"}, headers=H(ta))
        assert r.status_code == 200 and r.json()["matched"] is False
        r = await c.get("/api/v1/admin/im/watermark/grants", headers=H(tsu))
        grants = [x for x in r.json() if x["quota_type"] == "times" and x["max_uses"] == 1]
        assert grants[0]["used_count"] == 0, "失败不应扣额度"
        r = await c.post("/api/v1/im/decode-text", json={"text": "成功" + zw_a}, headers=H(ta))
        assert r.status_code == 200 and r.json()["matched"]
        r = await c.get("/api/v1/admin/im/watermark/grants", headers=H(tsu))
        grants = [x for x in r.json() if x["quota_type"] == "times" and x["max_uses"] == 1]
        assert grants[0]["used_count"] == 1
        # 吊销 → 403
        r = await c.post(f"/api/v1/admin/im/watermark/grants/{grant_id}/revoke", headers=H(tsu))
        assert r.status_code == 200
        r = await c.post("/api/v1/im/decode-text", json={"text": "吊销后" + zw_a}, headers=H(ta))
        assert r.status_code == 403, "吊销后应 403"
        # watermark_logs 有记录
        async with SessionLocal() as db:
            from app.models import WatermarkLog

            logs = (
                await db.execute(select(WatermarkLog).where(WatermarkLog.actor_id == alice_uid))
            ).scalars().all()
            assert len(logs) >= 4, "取证调用应有日志"
            assert any(l.consumed for l in logs) and any(not l.consumed for l in logs), "命中/未命中日志都应存在"


        print("23. 敏感词过滤（合规 FR8.3）")
        # 私信发送违规词 → 400
        r = await c.post(
            f"/api/v1/im/conversations/{conv_id}/messages",
            json={"kind": "text", "content": "今晚一起看博彩网站下注"},
            headers=H(ta),
        )
        assert r.status_code == 400 and "违规" in r.json()["detail"], r.text
        # 群消息违规 → 400（临时建群）
        r = await c.post("/api/v1/im/groups", json={"name": "审核测试群", "member_uids": [bob_uid]}, headers=H(ta))
        gid2 = r.json()["id"]
        r = await c.post(
            f"/api/v1/im/groups/{gid2}/messages",
            json={"kind": "text", "content": "出售大麻请联系"},
            headers=H(ta),
        )
        assert r.status_code == 400 and "违规" in r.json()["detail"], r.text
        # 正常消息不受影响
        r = await c.post(
            f"/api/v1/im/conversations/{conv_id}/messages",
            json={"kind": "text", "content": "正常交流没问题"},
            headers=H(ta),
        )
        assert r.status_code == 200
        # admin 新增词 → 立即拦截；停用 → 放行；删除 → 放行
        r = await c.post("/api/v1/admin/im/sensitive-words", json={"word": "合规测试词"}, headers=H(tsu))
        assert r.status_code == 201, r.text
        wid = r.json()["id"]
        r = await c.post(
            f"/api/v1/im/conversations/{conv_id}/messages",
            json={"kind": "text", "content": "这里出现合规测试词了"},
            headers=H(ta),
        )
        assert r.status_code == 400, "新增词应立即生效"
        await c.post(f"/api/v1/admin/im/sensitive-words/{wid}/toggle", headers=H(tsu))
        r = await c.post(
            f"/api/v1/im/conversations/{conv_id}/messages",
            json={"kind": "text", "content": "合规测试词已停用"},
            headers=H(ta),
        )
        assert r.status_code == 200, "停用后应放行"
        r = await c.delete(f"/api/v1/admin/im/sensitive-words/{wid}", headers=H(tsu))
        assert r.status_code == 204
        # 词库列表
        r = await c.get("/api/v1/admin/im/sensitive-words?page_size=10", headers=H(tsu))
        assert r.status_code == 200 and r.json()["total"] >= 30, "内置词库应存在"

        print("24. 聊天记录导出（数据携带权）")
        r = await c.get(f"/api/v1/user/conversations/{conv_id}/export", headers=H(ta))
        assert r.status_code == 200, r.text
        assert "正常交流没问题" in r.text, "普通消息应出现在导出中"
        assert "已被管理员删除" in r.text, "被删除消息应在导出中标注"
        assert "已撤回" in r.text, "撤回消息应在导出中标注"
        assert "图片" in r.text, "图片消息应在导出中标注"
        # 越权导出 → 404
        r = await c.get(f"/api/v1/user/conversations/{conv_id}/export", headers=H(tc))
        assert r.status_code == 404

        print("25. 账号注销（合规：删除权）")
        # 密码错误 → 400
        r = await c.post("/api/v1/user/deactivate", json={"password": "WrongPass"}, headers=H(ta))
        assert r.status_code == 400
        # 群消息匿名化准备：alice 在 gid2 发一条
        r = await c.post(
            f"/api/v1/im/groups/{gid2}/messages",
            json={"kind": "text", "content": "这条将被匿名化"},
            headers=H(ta),
        )
        assert r.status_code == 201, f"gid2={gid2} resp={r.text[:200]}"
        gm_anon = r.json()["id"]
        # 注销 alice
        r = await c.post("/api/v1/user/deactivate", json={"password": PASS}, headers=H(ta))
        assert r.status_code == 200, r.text
        # alice 登录被拒
        r = await c.post("/api/v1/auth/login", json={"email": "alice-im@example.com", "password": PASS})
        assert r.status_code == 401, "注销后应无法登录"
        async with SessionLocal() as db:
            alice_now = await db.get(User, alice_uid)
            assert alice_now is not None and alice_now.is_active is False
            assert alice_now.email.startswith("deleted-"), "邮箱应匿名化"
            assert alice_now.nickname == "已注销用户"
            # bob 与 alice 的会话已删除
            conv_left = (
                await db.execute(
                    select(DmConversation).where(
                        (DmConversation.user_a == alice_uid) | (DmConversation.user_b == alice_uid)
                    )
                )
            ).scalar_one_or_none()
            assert conv_left is None, "私信会话应被删除"
            # 群消息匿名化
            anon = await db.get(GroupMessage, gm_anon)
            assert anon.sender_id == "00000000-0000-4000-8000-000000000001", "群消息应匿名化"
            # alice 已退出所有群
            gm_left = (
                await db.execute(select(GroupMember).where(GroupMember.user_id == alice_uid))
            ).scalar_one_or_none()
            assert gm_left is None, "应退出所有群"
        # bob 侧会话列表无 alice 会话
        r = await c.get("/api/v1/im/conversations", headers=H(tb))
        assert all(x["other"]["uid"] != alice_uid for x in r.json()["items"]), "bob 侧会话应消失"
        # gid2 由 alice 创建，alice 注销后应转让给 bob（唯一成员）
        r = await c.get(f"/api/v1/im/groups/{gid2}", headers=H(tb))
        assert r.status_code == 200 and r.json()["owner_id"] == bob_uid, "群主应转让给剩余成员"
        r = await c.delete(f"/api/v1/im/groups/{gid2}", headers=H(tb))
        assert r.status_code == 204, r.text
        r = await c.get(f"/api/v1/im/groups/{gid2}/messages", headers=H(tb))
        assert r.status_code == 404 or r.status_code == 200

        print("26. 保留期配置读取")
        from app.services import settings as settings_svc

        async with SessionLocal() as db:
            days = await settings_svc.get_setting(db, "im.message_retention_days", "365")
        assert days == "365", days

        print("27. 企业级日志导出")
        from datetime import timedelta as _td

        exp_start = datetime.now(timezone.utc)
        now_iso = exp_start.isoformat()
        week_ago = (exp_start - _td(days=7)).isoformat()
        ok_payload = {"source": "audit", "format": "csv", "start": week_ago, "end": now_iso}
        # 权限：普通用户 403
        r = await c.post("/api/v1/admin/exports/count", json=ok_payload, headers=H(ta))
        assert r.status_code == 403, "普通用户应 403"
        # 范围校验：end < start → 400；跨度 > 90 天 → 400
        r = await c.post("/api/v1/admin/exports/count", json={"source": "audit", "start": now_iso, "end": week_ago}, headers=H(tsu))
        assert r.status_code == 400
        r = await c.post(
            "/api/v1/admin/exports/count",
            json={"source": "audit", "start": (exp_start - _td(days=100)).isoformat(), "end": now_iso},
            headers=H(tsu),
        )
        assert r.status_code == 400
        # count 预览
        r = await c.post("/api/v1/admin/exports/count", json=ok_payload, headers=H(tsu))
        assert r.status_code == 200 and r.json()["count"] >= 0, r.text
        # 六数据源 count 全部可用
        for src in ("audit", "login", "visit", "watermark", "report", "bot"):
            r = await c.post("/api/v1/admin/exports/count", json={**ok_payload, "source": src}, headers=H(tsu))
            assert r.status_code == 200, f"{src} count 失败"
        # run CSV：BOM + 列头 + SHA-256 头
        r = await c.post("/api/v1/admin/exports/run", json=ok_payload, headers=H(tsu))
        assert r.status_code == 200, r.text
        assert r.headers.get("x-export-sha256") and len(r.headers["x-export-sha256"]) == 64
        assert r.headers.get("x-export-rows") is not None
        assert r.text.startswith("\ufeff"), "CSV 应带 UTF-8 BOM"
        assert "time_utc" in r.text and "action" in r.text
        assert "audit.export" in r.text, "本次导出行为自身应出现在审计数据中"
        # CSV 结构解析（9 列，转义正确）
        import csv as _csv
        import io as _io

        parsed = list(_csv.reader(_io.StringIO(r.text.lstrip("\ufeff"))))
        assert len(parsed) >= 2 and len(parsed[0]) == 9, f"audit 应为 9 列，实际 {len(parsed[0]) if parsed else 0}"
        # run JSON：完整结构
        r = await c.post("/api/v1/admin/exports/run", json={**ok_payload, "format": "json"}, headers=H(tsu))
        j = r.json()
        assert j["source"] == "audit" and j["row_count"] > 0 and j["rows"][0][0], j
        assert j["range_start"] == week_ago and j["exported_at"]
        # history：导出留痕
        r = await c.get("/api/v1/admin/exports/history?limit=10", headers=H(tsu))
        items = r.json()
        assert items and items[0]["source"] == "audit" and items[0]["sha256"], items
        # bot 源内容正确（含机器人广播）
        r = await c.post("/api/v1/admin/exports/run", json={**ok_payload, "source": "bot", "format": "json"}, headers=H(tsu))
        j = r.json()
        assert j["row_count"] >= 1 and j["rows"][0][-1], "机器人消息应可导出"
        # 限流：6 次/分 → 第 7 次 429
        for _ in range(6):
            await c.post("/api/v1/admin/exports/run", json={**ok_payload, "source": "login"}, headers=H(tsu))
        r = await c.post("/api/v1/admin/exports/run", json={**ok_payload, "source": "login"}, headers=H(tsu))
        assert r.status_code == 429, r.text
        # 清理测试窗口内的导出审计记录
        async with SessionLocal() as db:
            await db.execute(_delete(AuditLog).where(AuditLog.action == "audit.export", AuditLog.created_time >= exp_start))
            await db.commit()
        print("18. 清理测试数据")
        async with SessionLocal() as db:
            uids = [alice_uid, bob_uid]
            conv_ids = [
                cid for (cid,) in (
                    await db.execute(
                        select(DmConversation.id).where(
                            (DmConversation.user_a.in_(uids)) | (DmConversation.user_b.in_(uids))
                        )
                    )
                ).all()
            ]
            from app.models import GroupChat, GroupMember, GroupMessage

            gcids = [
                gid for (gid,) in (
                    await db.execute(select(GroupChat.id).where(GroupChat.owner_id.in_(uids)))
                ).all()
            ]
            gcids += [
                gid for (gid,) in (
                    await db.execute(select(GroupMember.group_id).where(GroupMember.user_id.in_(uids)))
                ).all()
            ]
            gcids = list(dict.fromkeys(gcids))
            if gcids:
                await db.execute(_delete(GroupMessage).where(GroupMessage.group_id.in_(gcids)))
                await db.execute(_delete(GroupMember).where(GroupMember.group_id.in_(gcids)))
                await db.execute(_delete(GroupChat).where(GroupChat.id.in_(gcids)))
            if conv_ids:
                await db.execute(_delete(DmMessage).where(DmMessage.conversation_id.in_(conv_ids)))
                await db.execute(_delete(DmConversationMember).where(DmConversationMember.conversation_id.in_(conv_ids)))
                await db.execute(_delete(DmConversation).where(DmConversation.id.in_(conv_ids)))
            await db.execute(_delete(Block).where((Block.uid.in_(uids)) | (Block.blocked_uid.in_(uids))))
            await db.execute(_delete(Report).where((Report.reporter_id.in_(uids)) | (Report.target_id.in_(conv_ids))))
            from app.models import WatermarkGrant, WatermarkLog

            await db.execute(_delete(WatermarkGrant).where(WatermarkGrant.user_id.in_(uids)))
            await db.execute(_delete(WatermarkLog).where(WatermarkLog.actor_id.in_(uids)))
            await db.execute(_delete(RefreshToken).where(RefreshToken.uid.in_(uids)))
            await db.execute(_delete(LoginLog).where(LoginLog.uid.in_(uids)))
            await db.execute(_delete(User).where(User.uid.in_(uids)))
            await db.commit()

    print("IM E2E ALL PASSED")


async def ensure_bot_session(c, token):
    """确保机器人存在（启动时已建，这里仅兜底）"""
    async with SessionLocal() as db:
        await ensure_bot(db)


asyncio.run(main())
