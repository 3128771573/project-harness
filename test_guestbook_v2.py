"""留言板 v2 E2E：档案号 / 多轮回复时间线 / 状态流转 / 模板 / 筛选（进程内 ASGI）
运行方式（backend 容器内）：docker exec -i harness-backend python < /tmp/test_guestbook_v2.py
"""
import asyncio
import re
import sys

import httpx
import pyotp
from httpx import ASGITransport

sys.path.insert(0, "/app/backend")
from app.database import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models import GuestbookReply, GuestbookTemplate, Message, User  # noqa: E402
from app.services.captcha import _store  # noqa: E402


def extract_captcha_id(resp) -> str | None:
    sc = resp.headers.get("set-cookie") or ""
    for part in sc.split(";"):
        part = part.strip()
        if part.startswith("captcha_id="):
            return part.split("=", 1)[1].strip()
    return None


async def get_captcha(c) -> tuple[str, str]:
    r = await c.get("/api/v1/captcha")
    cid = extract_captcha_id(r)
    code = _store.get(cid, (0, "?"))[1]
    return cid, code


async def main():
    from sqlalchemy import delete as _delete, select

    async with SessionLocal() as db:
        await db.execute(_delete(GuestbookReply).where(GuestbookReply.sender_name == "归档测试访客"))
        await db.execute(_delete(Message).where(Message.ip == "127.0.0.1"))
        await db.execute(_delete(GuestbookTemplate).where(GuestbookTemplate.name.like("测试模板%")))
        await db.commit()

    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        print("1. 提交留言 → 档案号")
        cid, code = await get_captcha(c)
        r = await c.post(
            "/api/v1/messages",
            json={"nickname": "归档测试访客", "email": "gb-v2@example.com", "content": "第一条归档留言", "captcha": code},
            cookies={"captcha_id": cid},
        )
        assert r.status_code == 200, r.text
        q1 = r.json()["query_code"]
        a1 = r.json()["archive_no"]
        assert re.fullmatch(r"GB-\d{8}-\d{3}", a1), a1
        print("   archive1:", a1)

        cid, code = await get_captcha(c)
        r = await c.post(
            "/api/v1/messages",
            json={"nickname": "归档测试访客", "email": "gb-v2@example.com", "content": "第二条归档留言", "captcha": code},
            cookies={"captcha_id": cid},
        )
        a2 = r.json()["archive_no"]
        assert re.fullmatch(r"GB-\d{8}-\d{3}", a2) and a2 != a1, (a1, a2)
        seq1, seq2 = int(a1.rsplit("-", 1)[1]), int(a2.rsplit("-", 1)[1])
        assert seq2 == seq1 + 1, "当日档案号应递增"
        print("   archive2:", a2, "| 递增 ✓")

        print("2. 查询 → 档案号 + 空时间线")
        r = await c.post("/api/v1/query", json={"query_code": q1, "email": "gb-v2@example.com"})
        assert r.status_code == 200
        d = r.json()["data"]
        assert d["archive_no"] == a1 and d["status"] == "pending" and d["replies"] == []

        print("3. superadmin 登录 + 列表（档案号/筛选）")
        async with SessionLocal() as db:
            su = (await db.execute(select(User).where(User.email == "superadmin@platformharness.ltd"))).scalar_one()
            otp = pyotp.TOTP(su.totp_secret).now()
        r = await c.post("/api/v1/auth/login", json={"email": "superadmin@platformharness.ltd", "password": "SuAdmin@2026Cloud", "totp_code": otp})
        assert r.status_code == 200
        ts = r.json()["access_token"]
        h = {"Authorization": f"Bearer {ts}"}
        r = await c.get("/api/v1/admin/messages?page_size=50", headers=h)
        items = r.json()["items"]
        m1 = [x for x in items if x["archive_no"] == a1][0]
        assert m1["status"] == "pending" and m1["query_code"] == q1 and m1["email"] == "gb-v2@example.com"
        # 关键词筛选：档案号
        r = await c.get("/api/v1/admin/messages?keyword=" + a2, headers=h)
        assert len(r.json()["items"]) == 1 and r.json()["items"][0]["archive_no"] == a2
        # 状态筛选
        r = await c.get("/api/v1/admin/messages?status=pending", headers=h)
        assert any(x["archive_no"] == a1 for x in r.json()["items"])
        r = await c.get("/api/v1/admin/messages?status=closed", headers=h)
        assert all(x["status"] == "closed" for x in r.json()["items"])

        print("4. 管理员回复 → 时间线 + replied")
        r = await c.put(f"/api/v1/admin/messages/{m1['id']}/reply", json={"reply": "您好，已收到您的留言，我们正在处理。"}, headers=h)
        assert r.status_code == 200, r.text
        r = await c.get(f"/api/v1/admin/messages/{m1['id']}/replies", headers=h)
        tl = r.json()
        assert len(tl) == 1 and tl[0]["sender_type"] == "admin" and tl[0]["content"].startswith("您好")
        r = await c.get("/api/v1/admin/messages?keyword=" + a1, headers=h)
        assert r.json()["items"][0]["status"] == "replied"
        # 访客视角查询看到时间线
        r = await c.post("/api/v1/query", json={"query_code": q1, "email": "gb-v2@example.com"})
        d = r.json()["data"]
        assert d["status"] == "replied" and len(d["replies"]) == 1 and d["replies"][0]["sender_type"] == "admin"

        print("5. 访客追问 → 状态回 pending")
        r = await c.post("/api/v1/query/reply", json={"query_code": q1, "email": "gb-v2@example.com", "content": "请问大概多久能处理完？"})
        assert r.status_code == 200, r.text
        d = r.json()["data"]
        assert d["status"] == "pending" and len(d["replies"]) == 2
        assert d["replies"][-1]["sender_type"] == "visitor"
        # 管理员列表未读标记
        r = await c.get("/api/v1/admin/messages?keyword=" + a1, headers=h)
        assert r.json()["items"][0]["is_read"] is False, "追问后应回到未读"

        print("6. 关闭 / 重开")
        r = await c.post(f"/api/v1/admin/messages/{m1['id']}/close", headers=h)
        assert r.status_code == 200
        r = await c.post("/api/v1/query/reply", json={"query_code": q1, "email": "gb-v2@example.com", "content": "还能问吗"})
        assert r.status_code == 400, "关闭后应拒绝追问"
        r = await c.post(f"/api/v1/admin/messages/{m1['id']}/reopen", headers=h)
        assert r.status_code == 200
        r = await c.post("/api/v1/query/reply", json={"query_code": q1, "email": "gb-v2@example.com", "content": "重开后追问"})
        assert r.status_code == 200 and len(r.json()["data"]["replies"]) == 3

        print("7. 快捷回复模板 CRUD")
        r = await c.post("/api/v1/admin/messages/templates", json={"name": "测试模板-致谢", "content": "感谢您的反馈，我们将持续改进。"}, headers=h)
        assert r.status_code == 201, r.text
        tid = r.json()["id"]
        r = await c.get("/api/v1/admin/messages/templates", headers=h)
        assert any(t["id"] == tid for t in r.json())
        r = await c.delete(f"/api/v1/admin/messages/templates/{tid}", headers=h)
        assert r.status_code == 204
        r = await c.get("/api/v1/admin/messages/templates", headers=h)
        assert all(t["id"] != tid for t in r.json())

        print("8. 邮件通知静默（SMTP 未配置不抛错）")
        cid, code = await get_captcha(c)
        r = await c.post(
            "/api/v1/messages",
            json={"nickname": "归档测试访客", "email": "gb-v2@example.com", "content": "带邮箱的留言用于回复通知", "captcha": code},
            cookies={"captcha_id": cid},
        )
        m3 = r.json()["archive_no"]
        r = await c.get("/api/v1/admin/messages?keyword=" + m3, headers=h)
        mid3 = r.json()["items"][0]["id"]
        r = await c.put(f"/api/v1/admin/messages/{mid3}/reply", json={"reply": "通知测试回复"}, headers=h)
        assert r.status_code == 200, "SMTP 未配置也应正常回复"

        print("9. 清理")
        async with SessionLocal() as db:
            await db.execute(_delete(GuestbookReply).where(GuestbookReply.sender_name == "归档测试访客"))
            await db.execute(_delete(Message).where(Message.ip == "127.0.0.1"))
            await db.execute(_delete(GuestbookTemplate).where(GuestbookTemplate.name.like("测试模板%")))
            await db.commit()

    print("GUESTBOOK V2 E2E ALL PASSED")


asyncio.run(main())
