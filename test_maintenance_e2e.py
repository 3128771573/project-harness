"""维护模式 E2E：开关 / 普通用户 503 / 公开与登录放行 / 管理员放行 / 恢复（进程内 ASGI）
运行方式（backend 容器内）：docker exec -i harness-backend python < /tmp/test_maintenance_e2e.py
"""
import asyncio
import sys

import httpx
import pyotp
from httpx import ASGITransport

sys.path.insert(0, "/app/backend")
from app.database import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User  # noqa: E402
from app.services.maintenance import invalidate  # noqa: E402


async def set_maintenance(on: bool):
    from app.services import settings as settings_svc

    async with SessionLocal() as db:
        await settings_svc.set_setting(db, "site.maintenance", "true" if on else "false")
    invalidate()


async def main():
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        # superadmin token
        async with SessionLocal() as db:
            su = (await db.execute(__import__("sqlalchemy").select(User).where(User.email == "superadmin@platformharness.ltd"))).scalar_one()
            otp = pyotp.TOTP(su.totp_secret).now()
        r = await c.post("/api/v1/auth/login", json={"email": "superadmin@platformharness.ltd", "password": "SuAdmin@2026Cloud", "totp_code": otp})
        assert r.status_code == 200
        ts = r.json()["access_token"]
        h = {"Authorization": f"Bearer {ts}"}

        # 0) 确保关闭
        await set_maintenance(False)
        await asyncio.sleep(2.5)
        r = await c.get("/api/v1/public/maintenance")
        assert r.json()["maintenance"] is False

        print("1. 开启维护模式")
        await set_maintenance(True)
        await asyncio.sleep(2.5)
        r = await c.get("/api/v1/public/maintenance")
        assert r.json()["maintenance"] is True and r.json()["message"]

        print("2. 普通用户请求 → 503")
        r = await c.get("/api/v1/ai/config")  # 登录态之外的代表性接口
        assert r.status_code == 503, r.status_code
        assert "维护" in r.json()["detail"]
        # 带普通用户 token 也 503
        r2 = await c.post("/api/v1/auth/send-code", json={"email": "maint-t@example.com", "purpose": "register"})
        assert r2.status_code == 200, "auth 放行"
        code = r2.json().get("dev_code", "")
        r2 = await c.post("/api/v1/auth/register", json={"username": "maintt", "email": "maint-t@example.com", "password": "TestPass123", "code": code or "000000"})
        assert r2.status_code == 201
        tn = r2.json()["access_token"]
        hn = {"Authorization": f"Bearer {tn}"}
        r = await c.get("/api/v1/user/profile", headers=hn)
        assert r.status_code == 503, "普通用户 API 应 503"
        r = await c.get("/api/v1/im/conversations", headers=hn)
        assert r.status_code == 503

        print("3. 公开接口放行")
        r = await c.get("/api/v1/health")
        assert r.status_code == 200
        r = await c.get("/api/v1/public/notices")
        assert r.status_code == 200
        r = await c.get("/api/v1/public/maintenance")
        assert r.status_code == 200 and r.json()["maintenance"] is True
        r = await c.get("/api/v1/captcha")
        assert r.status_code == 200

        print("4. 管理员完全放行")
        r = await c.get("/api/v1/admin/settings", headers=h)
        assert r.status_code == 200 and r.json()["maintenance_mode"] is True
        r = await c.get("/api/v1/user/profile", headers=h)
        assert r.status_code == 200, "管理员访问用户接口也应放行"
        r = await c.get("/api/v1/im/conversations", headers=h)
        assert r.status_code == 200
        r = await c.get("/api/v1/admin/exports/history", headers=h)
        assert r.status_code == 200

        print("5. 维护说明更新")
        r = await c.put("/api/v1/admin/settings", json={"maintenance_message": "数据库升级中，预计 30 分钟"}, headers=h)
        assert r.status_code == 200
        r = await c.get("/api/v1/public/maintenance")
        assert r.json()["message"] == "数据库升级中，预计 30 分钟"

        print("6. 关闭维护 → 恢复")
        await set_maintenance(False)
        await asyncio.sleep(2.5)
        r = await c.get("/api/v1/public/maintenance")
        assert r.json()["maintenance"] is False
        r = await c.get("/api/v1/user/profile", headers=hn)
        assert r.status_code == 200, "关闭后普通用户恢复"

        # 清理测试用户
        from sqlalchemy import delete as _delete

        async with SessionLocal() as db:
            u = (await db.execute(__import__("sqlalchemy").select(User).where(User.email == "maint-t@example.com"))).scalar_one_or_none()
            if u:
                await db.execute(_delete(__import__("app.models", fromlist=["RefreshToken"]).RefreshToken).where(__import__("app.models", fromlist=["RefreshToken"]).RefreshToken.uid == u.uid))
                await db.execute(_delete(__import__("app.models", fromlist=["LoginLog"]).LoginLog).where(__import__("app.models", fromlist=["LoginLog"]).LoginLog.uid == u.uid))
                await db.delete(u)
            await db.commit()

    print("MAINTENANCE E2E ALL PASSED")


asyncio.run(main())
