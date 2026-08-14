"""Project Harness API 集成测试

在 CI 中用真实 PostgreSQL 运行（见 .github/workflows/ci.yml）。
本地运行: 需要 PostgreSQL 服务，设置 DATABASE_URL 环境变量。
"""
import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# 必须在导入 app 前设置环境变量
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://harness:harness_dev_pw@localhost:5432/harness_test",
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["JWT_SECRET"] = "test-secret-for-ci"
os.environ["AI_API_KEY"] = ""  # mock 模式
os.environ["UPLOAD_DIR"] = "/tmp/harness-test-uploads"

from app.main import app  # noqa: E402
from app.database import get_db  # noqa: E402


@pytest.fixture
async def client():
    engine = create_async_engine(TEST_DATABASE_URL)

    # httpx ASGITransport 不会触发 lifespan，手动建表 + 种子角色
    from sqlalchemy import select

    from app.models import Base, Role

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionTest = async_sessionmaker(engine, expire_on_commit=False)
    async with SessionTest() as session:
        for name in ("user", "admin", "super_admin"):
            exists = await session.execute(select(Role).where(Role.name == name))
            if exists.scalar_one_or_none() is None:
                session.add(Role(name=name))
        await session.commit()

    async def override_get_db():
        async with SessionTest() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
    await engine.dispose()
    # 释放模块级全局 engine（测试中直接改库时使用），避免 loop 关闭时连接池残留
    from app.database import engine as global_engine

    if global_engine is not engine:
        await global_engine.dispose()


async def _register(client, username, email=None, password="TestPass123", with_code=True):
    """注册 helper：先获取邮箱验证码（dev_code），再带 code 注册"""
    email = email or f"{username}@test.com"
    if with_code:
        send = await client.post(
            "/api/v1/auth/send-code",
            json={"email": email, "purpose": "register"},
        )
        assert send.status_code == 200, send.text
        data = send.json()
        code = data.get("dev_code")
        assert code, f"应返回 dev_code（开发模式），实际: {data}"
    else:
        code = None

    payload = {"username": username, "email": email, "password": password}
    if code:
        payload["code"] = code
    resp = await client.post("/api/v1/auth/register", json=payload)
    return resp


@pytest.fixture
async def auth_user(client):
    """注册一个普通用户并返回 (token, user)"""
    import uuid

    suf = uuid.uuid4().hex[:8]
    resp = await _register(client, f"tester_{suf}")
    assert resp.status_code == 201, resp.text
    data = resp.json()
    return data["access_token"], data["user"]


# ---------- auth ----------


async def test_health(client):
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_register_login_refresh(client):
    import uuid

    suf = uuid.uuid4().hex[:8]
    reg = await _register(client, f"u_{suf}", email=f"e_{suf}@test.com", password="Secret123")
    assert reg.status_code == 201, reg.text
    data = reg.json()
    assert data["access_token"] and data["refresh_token"]
    assert data["user"]["role"] == "user"
    assert data["user"]["uid"]

    # 重复注册（同一邮箱，需新验证码）
    dup = await _register(client, f"u_{suf}", email=f"e_{suf}@test.com", password="Secret123")
    assert dup.status_code == 409

    # 登录
    login = await client.post(
        "/api/v1/auth/login", json={"email": f"e_{suf}@test.com", "password": "Secret123"}
    )
    assert login.status_code == 200

    # 错误密码
    bad = await client.post(
        "/api/v1/auth/login", json={"email": f"e_{suf}@test.com", "password": "WrongPass"}
    )
    assert bad.status_code == 401

    # refresh 轮换
    rf = await client.post("/api/v1/auth/refresh", json={"refresh_token": data["refresh_token"]})
    assert rf.status_code == 200
    new_refresh = rf.json()["refresh_token"]

    # 旧 refresh 已吊销
    old = await client.post("/api/v1/auth/refresh", json={"refresh_token": data["refresh_token"]})
    assert old.status_code == 401

    # 新 refresh 可用
    ok = await client.post("/api/v1/auth/refresh", json={"refresh_token": new_refresh})
    assert ok.status_code == 200


# ---------- user ----------


async def test_profile_update(client, auth_user):
    token, user = auth_user
    headers = {"Authorization": f"Bearer {token}"}

    prof = await client.get("/api/v1/user/profile", headers=headers)
    assert prof.status_code == 200
    assert prof.json()["role"] == "user"

    upd = await client.put(
        "/api/v1/user/profile", headers=headers, json={"nickname": "测试昵称", "bio": "hello"}
    )
    assert upd.status_code == 200
    assert upd.json()["nickname"] == "测试昵称"
    assert upd.json()["bio"] == "hello"


# ---------- ai (mock 模式) ----------


async def test_ai_chat_and_history(client, auth_user):
    token, user = auth_user
    headers = {"Authorization": f"Bearer {token}"}

    chat = await client.post("/api/v1/ai/chat", headers=headers, json={"question": "你好"})
    assert chat.status_code == 200
    assert chat.json()["model"] == "mock"
    assert chat.json()["answer"]

    hist = await client.get("/api/v1/ai/history", headers=headers)
    assert hist.status_code == 200
    assert hist.json()["total"] >= 1
    assert hist.json()["items"][0]["question"] == "你好"


# ---------- rbac ----------


async def test_rbac_admin_protected(client, auth_user):
    token, user = auth_user
    headers = {"Authorization": f"Bearer {token}"}

    ping = await client.get("/api/v1/admin/ping", headers=headers)
    assert ping.status_code == 403

    stats = await client.get("/api/v1/admin/stats", headers=headers)
    assert stats.status_code == 403

    users = await client.get("/api/v1/admin/users", headers=headers)
    assert users.status_code == 403

    sys_status = await client.get("/api/v1/admin/system/status", headers=headers)
    assert sys_status.status_code == 403


async def test_admin_endpoints_as_admin(client):
    """直接把用户提升为 admin 后验证 admin 接口（通过数据库或注册后改角色）"""
    import uuid

    suf = uuid.uuid4().hex[:8]
    reg = await _register(client, f"adm_{suf}", email=f"adm_{suf}@test.com", password="AdminPass123")
    assert reg.status_code == 201, reg.text
    token = reg.json()["access_token"]
    uid = reg.json()["user"]["uid"]

    # 通过 user 接口无法提升；此处直接从 DB 改（CI 中测试库可直接操作）
    from app.database import engine

    from sqlalchemy import text

    async with engine.begin() as conn:
        await conn.execute(
            text(
                "UPDATE users SET role_id=(SELECT id FROM roles WHERE name='admin') WHERE uid=:uid"
            ),
            {"uid": uid},
        )

    headers = {"Authorization": f"Bearer {token}"}
    ping = await client.get("/api/v1/admin/ping", headers=headers)
    assert ping.status_code == 200
    assert ping.json()["message"] == "管理员访问成功"

    stats = await client.get("/api/v1/admin/stats", headers=headers)
    assert stats.status_code == 200
    assert "total_users" in stats.json()

    users = await client.get("/api/v1/admin/users", headers=headers)
    assert users.status_code == 200
    assert "items" in users.json()

    sys_status = await client.get("/api/v1/admin/system/status", headers=headers)
    assert sys_status.status_code == 200
    data = sys_status.json()
    assert "cpu" in data and "memory" in data and "disk" in data and "uptime" in data


async def test_super_admin_guard(client):
    """只有 super_admin 能修改 admin 角色的用户"""
    import uuid

    suf = uuid.uuid4().hex[:8]

    # 普通用户 adminA
    reg_a = await _register(client, f"a_{suf}", email=f"a_{suf}@test.com", password="Pass12345")
    assert reg_a.status_code == 201, reg_a.text
    uid_a = reg_a.json()["user"]["uid"]

    # adminB（提升为 admin）
    reg_b = await _register(client, f"b_{suf}", email=f"b_{suf}@test.com", password="Pass12345")
    assert reg_b.status_code == 201, reg_b.text
    token_b = reg_b.json()["access_token"]
    uid_b = reg_b.json()["user"]["uid"]

    from sqlalchemy import text

    from app.database import engine

    async with engine.begin() as conn:
        await conn.execute(
            text(
                "UPDATE users SET role_id=(SELECT id FROM roles WHERE name='admin') WHERE uid=:uid"
            ),
            {"uid": uid_b},
        )

    # adminB 尝试把 adminA 提升为 admin -> 403
    headers_b = {"Authorization": f"Bearer {token_b}"}
    resp = await client.patch(f"/api/v1/admin/users/{uid_a}/role", headers=headers_b, json={"role": "admin"})
    assert resp.status_code == 403
