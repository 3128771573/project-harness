"""企业级维护模式 E2E：四模式矩阵 / 倒计时 / 超时兜底 / 定时 / 紧急令牌 / 审计 / 通知 / 头信息
运行方式（backend 容器内）：docker exec -i harness-backend python < /tmp/test_maintenance_v2_e2e.py
"""
import asyncio
import sys
from datetime import datetime, timedelta, timezone

import httpx
import pyotp
from httpx import ASGITransport

sys.path.insert(0, "/app/backend")
from app.database import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User  # noqa: E402
from app.services import maintenance as maint  # noqa: E402


async def main():
    from sqlalchemy import delete as _delete, select

    # 清理历史测试数据
    from app.models import EmailCode as _EC
    from app.models import LoginLog as _LL
    from app.models import RefreshToken as _RT

    async with SessionLocal() as db:
        await db.execute(_delete(_EC).where(_EC.email == "maintv2@example.com"))
        u = (await db.execute(select(User).where(User.email == "maintv2@example.com"))).scalar_one_or_none()
        if u:
            await db.execute(_delete(_RT).where(_RT.uid == u.uid))
            await db.execute(_delete(_LL).where(_LL.uid == u.uid))
            await db.delete(u)
        await db.commit()

    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        # superadmin token
        async with SessionLocal() as db:
            su = (await db.execute(select(User).where(User.email == "superadmin@platformharness.ltd"))).scalar_one()
            otp = pyotp.TOTP(su.totp_secret).now()
        r = await c.post("/api/v1/auth/login", json={"email": "superadmin@platformharness.ltd", "password": "SuAdmin@2026Cloud", "totp_code": otp})
        assert r.status_code == 200
        ts = r.json()["access_token"]
        h = {"Authorization": f"Bearer {ts}"}
        # 普通用户
        r2 = await c.post("/api/v1/auth/send-code", json={"email": "maintv2@example.com", "purpose": "register"})
        code = r2.json().get("dev_code", "")
        r2 = await c.post("/api/v1/auth/register", json={"username": "maintv2", "email": "maintv2@example.com", "password": "TestPass123", "code": code or "000000"})
        assert r2.status_code == 201, r2.text
        tn = r2.json()["access_token"]
        hn = {"Authorization": f"Bearer {tn}"}

        # 确保关闭
        async with SessionLocal() as db:
            await maint.disable(db, by="test")
        maint.invalidate()

        print("1. 四模式拦截矩阵")
        matrix = [
            ("full", 503, 503, 200),
            ("block_new", 503, 200, 200),
            ("scheduled", 503, 503, 200),
            ("admin_only", 503, 503, 200),
        ]
        for mode, anon_code, user_code, admin_code in matrix:
            async with SessionLocal() as db:
                await maint.enable(db, mode=mode, reason=f"矩阵测试-{mode}", duration_minutes=None, by="test")
            r_anon = await c.get("/api/v1/im/conversations")
            r_user = await c.get("/api/v1/im/conversations", headers=hn)
            r_admin = await c.get("/api/v1/im/conversations", headers=h)
            print(f"   {mode}: 访客={r_anon.status_code} 普通={r_user.status_code} 管理员={r_admin.status_code}")
            assert r_anon.status_code == anon_code, f"{mode} 访客应 {anon_code}"
            assert r_user.status_code == user_code, f"{mode} 普通用户应 {user_code}"
            assert r_admin.status_code == admin_code, f"{mode} 管理员应 {admin_code}"
            if anon_code == 503:
                assert "Retry-After" in r_anon.headers and "no-cache" in r_anon.headers.get("Cache-Control", "")
                assert r_anon.json().get("mode") == mode

        print("2. 503 响应头（Retry-After / Cache-Control / 模式信息）")
        async with SessionLocal() as db:
            await maint.enable(db, mode="full", reason="头信息测试", duration_minutes=30, by="test")
        r = await c.get("/api/v1/im/conversations")
        assert r.status_code == 503
        assert r.headers.get("retry-after", "").isdigit() and 1500 <= int(r.headers["retry-after"]) <= 1801
        assert "no-store" in r.headers.get("cache-control", "")
        body = r.json()
        assert body["mode"] == "full" and body["reason"] == "头信息测试" and body["auto_close_at"]
        r = await c.get("/api/v1/public/maintenance")
        assert r.json()["mode"] == "full" and r.json()["reason"] == "头信息测试"

        print("3. 倒计时自动关闭（优先级 1）")
        async with SessionLocal() as db:
            await maint._set(db, "auto_close_at", (datetime.now(timezone.utc) + timedelta(seconds=1)).isoformat(), "test")
        maint.invalidate()
        await asyncio.sleep(1.5)
        async with SessionLocal() as db:
            result = await maint.maintenance_tick(db)
        assert result.get("action") == "auto_close", result
        r = await c.get("/api/v1/public/maintenance")
        assert r.json()["maintenance"] is False

        print("4. 超时兜底（优先级 2：默认 120 分钟）")
        async with SessionLocal() as db:
            await maint.enable(db, mode="full", reason="超时测试", duration_minutes=None, by="test")
            await maint._set(db, "start_at", (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat(), "test")
        maint.invalidate()
        async with SessionLocal() as db:
            result = await maint.maintenance_tick(db)
        assert result.get("action") == "auto_close" and "120" in result.get("detail", ""), result
        async with SessionLocal() as db:
            assert await maint.is_maintenance(db) is False

        print("5. 定时维护（到达计划时间自动开启）")
        now_minute = datetime.now(timezone.utc).strftime("%H:%M")
        async with SessionLocal() as db:
            await maint._set(db, "scheduled_enabled", "true", "test")
            await maint._set(db, "scheduled_time", now_minute, "test")
            await maint._set(db, "scheduled_duration", "60", "test")
        maint.invalidate()
        async with SessionLocal() as db:
            result = await maint.maintenance_tick(db)
        assert result.get("action") == "scheduled_start", result
        async with SessionLocal() as db:
            snap = await maint.snapshot(db)
            assert snap["mode"] == "scheduled" and snap["auto_close_at"], snap
        # 关闭并禁用定时
        async with SessionLocal() as db:
            await maint.disable(db, by="test")
            await maint._set(db, "scheduled_enabled", "false", "test")
        maint.invalidate()

        print("6. 紧急令牌")
        r = await c.post("/api/v1/admin/maintenance/regenerate-token", headers=h)
        assert r.status_code == 200, r.text
        token = r.json()["token"]
        assert len(token) >= 60
        async with SessionLocal() as db:
            await maint.enable(db, mode="full", reason="紧急令牌测试", duration_minutes=None, by="test")
        # 错误令牌 → 403
        r = await c.get("/api/v1/admin/maintenance/emergency-close", params={"token": "wrong-token"})
        assert r.status_code == 403
        # URL 参数绕过拦截
        r = await c.get("/api/v1/im/conversations", params={"__emergency": token})
        assert r.status_code == 401, "紧急令牌应绕过维护拦截（未登录 401 而非 503）"
        r = await c.get("/api/v1/user/profile", headers=hn, params={"__emergency": token})
        assert r.status_code == 200, "紧急令牌应放行普通用户请求"
        # 紧急关闭
        r = await c.get("/api/v1/admin/maintenance/emergency-close", params={"token": token})
        assert r.status_code == 200 and r.json()["ok"], r.text
        r = await c.get("/api/v1/public/maintenance")
        assert r.json()["maintenance"] is False

        print("7. 审计记录 + 站内通知")
        # 经 API 开启（写审计 + 通知管理员）
        r = await c.post("/api/v1/admin/maintenance/enable", json={"mode": "full", "reason": "审计通知测试", "duration_minutes": 10}, headers=h)
        assert r.status_code == 200, r.text
        r = await c.get("/api/v1/admin/maintenance/history?limit=20", headers=h)
        actions = {x["action"] for x in r.json()}
        assert "maintenance.enable" in actions and "maintenance.emergency_close" in actions, actions
        # 管理员收到机器人私信
        r = await c.get("/api/v1/im/conversations", headers=h)
        bot_conv = [x for x in r.json()["items"] if x["other"]["uid"] == "bot-harness-official"]
        assert bot_conv and "维护模式通知" in bot_conv[0]["last_message"]["content"], "管理员应收到站内维护通知"
        r = await c.post("/api/v1/admin/maintenance/disable", headers=h)
        assert r.status_code == 200
        r = await c.get("/api/v1/admin/maintenance/history?limit=20", headers=h)
        actions = {x["action"] for x in r.json()}
        assert "maintenance.disable" in actions, actions

        print("8. 服务器重启检测（遗留超 30 分钟自动关闭）")
        async with SessionLocal() as db:
            await maint.enable(db, mode="full", reason="重启检测测试", duration_minutes=None, by="test")
            await maint._set(db, "start_at", (datetime.now(timezone.utc) - timedelta(minutes=45)).isoformat(), "test")
        maint.invalidate()
        async with SessionLocal() as db:
            result = await maint.on_server_start(db)
        assert result.get("action") == "auto_close", result
        # 开启不足 30 分钟 → 保持
        async with SessionLocal() as db:
            await maint.enable(db, mode="full", reason="重启检测测试2", duration_minutes=None, by="test")
            await maint._set(db, "start_at", (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(), "test")
        maint.invalidate()
        async with SessionLocal() as db:
            result = await maint.on_server_start(db)
        assert result.get("action") == "keep", result
        async with SessionLocal() as db:
            await maint.disable(db, by="test")

        print("9. 清理")
        async with SessionLocal() as db:
            await maint.disable(db, by="test")
            u = (await db.execute(select(User).where(User.email == "maintv2@example.com"))).scalar_one_or_none()
            if u:
                from app.models import LoginLog as _LL
                from app.models import RefreshToken as _RT

                await db.execute(_delete(_RT).where(_RT.uid == u.uid))
                await db.execute(_delete(_LL).where(_LL.uid == u.uid))
                await db.delete(u)
            await db.commit()

    print("MAINTENANCE V2 E2E ALL PASSED")


asyncio.run(main())
