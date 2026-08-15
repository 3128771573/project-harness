"""安全加固回归（规格 §5）：限流/登出吊销/设备绑定/上传校验/docs关闭/枚举统一/二次验证/AI并发/WS上限
运行方式（backend 容器内）：docker exec -i harness-backend python < /tmp/test_security_e2e.py
"""
import asyncio
import io
import sys

import httpx
from httpx import ASGITransport

sys.path.insert(0, "/app/backend")
from app.main import app  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import User  # noqa: E402


async def main():
    from sqlalchemy import delete as _delete, select

    async with SessionLocal() as db:
        from app.models import EmailCode as _EC
        from app.models import LoginLog as _LL
        from app.models import RefreshToken as _RT

        await db.execute(_delete(_EC).where(_EC.email.like("sec-%@example.com")))
        urows = (await db.execute(select(User).where(User.email.like("sec-%@example.com")))).scalars().all()
        for u in urows:
            await db.execute(_delete(_RT).where(_RT.uid == u.uid))
            await db.execute(_delete(_LL).where(_LL.uid == u.uid))
            await db.delete(u)
        await db.commit()

    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        print("1. 密码登录 IP 限流：5 次后 429")
        codes = []
        for _ in range(6):
            r = await c.post("/api/v1/auth/login", json={"email": "sec-none@example.com", "password": "WrongPass1"})
            codes.append(r.status_code)
        print("   ", codes)
        assert codes[:5] == [401] * 5 and codes[5] == 429, codes

        print("2. 邮箱失败锁定：轮换 IP 无法绕过（按邮箱累计，5 次后锁）")
        codes = []
        for i in range(6):
            r = await c.post(
                "/api/v1/auth/login",
                json={"email": "sec-lock@example.com", "password": "WrongPass1"},
                headers={"X-Real-IP": f"10.0.0.{i + 1}"},
            )
            codes.append(r.status_code)
        print("   ", codes)
        assert codes[:5] == [401] * 5 and codes[5] == 429, "邮箱锁应按邮箱累计且独立于 IP"
        # 新 IP 请求仍被邮箱锁拦截（XFF/X-Real-IP 轮换无效）
        r = await c.post("/api/v1/auth/login", json={"email": "sec-lock@example.com", "password": "WrongPass1"}, headers={"X-Real-IP": "9.9.9.9", "X-Forwarded-For": "1.1.1.1"})
        print("   换新IP后:", r.status_code, r.json().get("detail", "")[:30])
        assert r.status_code == 429, f"邮箱锁不受 IP 变化影响（实际 {r.status_code}）"

        print("3. 登出吊销 refresh")
        r = await c.post("/api/v1/auth/send-code", json={"email": "sec-a@example.com", "purpose": "register"})
        code = r.json().get("dev_code", "")
        r = await c.post("/api/v1/auth/register", json={"username": "seca", "email": "sec-a@example.com", "password": "TestPass123", "code": code or "000000"})
        assert r.status_code == 201, r.text
        refresh = r.json()["refresh_token"]
        r = await c.post("/api/v1/auth/logout", json={"refresh_token": refresh})
        assert r.status_code == 204
        r = await c.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
        assert r.status_code == 401, "登出后旧 refresh 应 401"

        print("4. 设备绑定：UA 变化 → 吊销全部 + 401")
        r = await c.post("/api/v1/auth/send-code", json={"email": "sec-b@example.com", "purpose": "register"})
        code = r.json().get("dev_code", "")
        r = await c.post("/api/v1/auth/register", json={"username": "secb", "email": "sec-b@example.com", "password": "TestPass123", "code": code or "000000"}, headers={"User-Agent": "Mozilla/5.0 Chrome/120"})
        refresh_b = r.json()["refresh_token"]
        # 换 UA 续期 → 401 + 原 token 全部吊销
        r = await c.post("/api/v1/auth/refresh", json={"refresh_token": refresh_b}, headers={"User-Agent": "Mozilla/5.0 Firefox/130"})
        assert r.status_code == 401, "设备变化应拒绝续期"
        r = await c.post("/api/v1/auth/refresh", json={"refresh_token": refresh_b}, headers={"User-Agent": "Mozilla/5.0 Chrome/120"})
        assert r.status_code == 401, "被吊销后原设备也应 401"

        print("5. 上传校验：伪造 content_type → 400；真图 → 200 PNG")
        r = await c.post(
            "/api/v1/auth/login",
            json={"email": "sec-a@example.com", "password": "TestPass123"},
            headers={"User-Agent": "Mozilla/5.0 Chrome/120"},
        )
        ta = r.json()["access_token"]
        h = {"Authorization": f"Bearer {ta}"}
        # 伪图：HTML 伪装 image/jpeg
        r = await c.post(
            "/api/v1/user/avatar",
            files={"file": ("evil.jpg", io.BytesIO(b"<html><script>alert(1)</script></html>"), "image/jpeg")},
            headers=h,
        )
        assert r.status_code == 400 and "不是有效图片" in r.json()["detail"], r.text
        # 真 PNG
        import struct
        import zlib

        def make_png(w=4, h=4):
            sig = b"\x89PNG\r\n\x1a\n"
            ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
            raw = b""
            for _ in range(h):
                raw += b"\x00" + b"\x80\x40\x20" * w
            idat = zlib.compress(raw)
            def chunk(t, d):
                return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
            return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")

        r = await c.post(
            "/api/v1/user/avatar",
            files={"file": ("ok.png", io.BytesIO(make_png()), "image/png")},
            headers=h,
        )
        assert r.status_code == 200, r.text
        assert r.json()["avatar"].endswith(".png"), r.json()["avatar"]

        print("6. API 文档生产关闭")
        r = await c.get("/docs")
        assert r.status_code == 404
        r = await c.get("/openapi.json")
        assert r.status_code == 404
        r = await c.get("/redoc")
        assert r.status_code == 404

        print("7. 枚举统一")
        r = await c.post("/api/v1/auth/send-code", json={"email": "sec-a@example.com", "purpose": "register"})
        code = r.json().get("dev_code", "")
        r = await c.post("/api/v1/auth/register", json={"username": "seca2", "email": "sec-a@example.com", "password": "TestPass123", "code": code or "000000"})
        assert r.status_code == 400 and "注册未成功" in r.json()["detail"], r.text

        print("8. 敏感操作二次验证（改角色/重置密码缺操作人密码 → 400）")
        # 准备 superadmin token
        import pyotp

        async with SessionLocal() as db:
            su = (await db.execute(select(User).where(User.email == "superadmin@platformharness.ltd"))).scalar_one()
            otp = pyotp.TOTP(su.totp_secret).now()
        r = await c.post("/api/v1/auth/login", json={"email": "superadmin@platformharness.ltd", "password": "SuAdmin@2026Cloud", "totp_code": otp})
        ts = r.json()["access_token"]
        hs = {"Authorization": f"Bearer {ts}"}
        r = await c.get("/api/v1/user/profile", headers=h)
        uid_a = r.json()["uid"]
        # 改角色缺密码 → 400（sec-a 是普通用户，改普通角色不需密码——用 admin 角色场景：给 sec-a 升 admin）
        r = await c.put(f"/api/v1/admin/users/{uid_a}/role", json={"role": "admin"}, headers=hs)
        assert r.status_code == 400 and "当前密码" in r.json()["detail"], r.text
        # 带错误密码 → 400
        r = await c.put(f"/api/v1/admin/users/{uid_a}/role", json={"role": "admin", "operator_password": "WrongPass"}, headers=hs)
        assert r.status_code == 400, r.text
        # 正确密码 → 200
        r = await c.put(f"/api/v1/admin/users/{uid_a}/role", json={"role": "admin", "operator_password": "SuAdmin@2026Cloud"}, headers=hs)
        assert r.status_code == 200, r.text
        # 重置密码缺操作人密码 → 400
        r = await c.post(f"/api/v1/admin/users/{uid_a}/reset-password", json={"new_password": "NewPass123"}, headers=hs)
        assert r.status_code == 400, r.text

        print("9. 可信 IP：XFF 伪造无法绕过限流（X-Real-IP 生效）")
        # 前面已触发 login 限流（IP=127.0.0.1），换 XFF 但同 X-Real-IP → 仍 429
        r = await c.post(
            "/api/v1/auth/login",
            json={"email": "sec-none2@example.com", "password": "WrongPass1"},
            headers={"X-Forwarded-For": "8.8.8.8", "X-Real-IP": "127.0.0.1"},
        )
        assert r.status_code == 429, "XFF 轮换应无法绕过（真实 IP 仍限流）"

        print("10. AI 流式并发槽位（第 3 个并发 → 429）")
        async def stream_call():
            return await c.post(
                "/api/v1/ai/chat",
                json={"question": "测试并发", "stream": True},
                headers=h,
                timeout=httpx.Timeout(30),
            )

        r1 = await stream_call()
        r2 = await stream_call()
        r3 = await stream_call()
        print("   ", r1.status_code, r2.status_code, r3.status_code)
        assert r1.status_code in (200, 201) and r2.status_code in (200, 201), (r1.status_code, r2.status_code)
        assert r3.status_code == 429, r3.text

        print("11. 清理")
        async with SessionLocal() as db:
            urows = (await db.execute(select(User).where(User.email.like("sec-%@example.com")))).scalars().all()
            for u in urows:
                await db.execute(_delete(_RT).where(_RT.uid == u.uid))
                await db.execute(_delete(_LL).where(_LL.uid == u.uid))
                await db.delete(u)
            await db.commit()

    print("SECURITY E2E ALL PASSED")


asyncio.run(main())
