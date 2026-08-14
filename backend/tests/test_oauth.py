"""GitHub OAuth 登录测试（monkeypatch GitHub API，不发起真实外呼）"""
import pytest
import pyotp
from sqlalchemy import select

from app.routers import oauth as oauth_mod

from tests.test_api import client, _register  # noqa: F401  (fixture 与 helper 复用)


@pytest.fixture
def gh_enabled(monkeypatch):
    monkeypatch.setattr(oauth_mod.settings, "GITHUB_CLIENT_ID", "test-client")
    monkeypatch.setattr(oauth_mod.settings, "GITHUB_CLIENT_SECRET", "test-secret")
    monkeypatch.setattr(oauth_mod.settings, "PUBLIC_BASE_URL", "http://test")
    return None


@pytest.fixture
def gh_api(monkeypatch, gh_enabled):
    async def fake_exchange(code):
        return {"access_token": "gh_token_1"}

    async def fake_userinfo(token):
        return {"id": 12345, "login": "dev_user", "name": "Dev User",
                "avatar_url": "https://avatars.githubusercontent.com/u/12345"}

    async def fake_email(token):
        return "dev@example.com"

    monkeypatch.setattr(oauth_mod, "gh_exchange_code", fake_exchange)
    monkeypatch.setattr(oauth_mod, "gh_userinfo", fake_userinfo)
    monkeypatch.setattr(oauth_mod, "gh_primary_email", fake_email)
    return None


async def test_oauth_providers_disabled_by_default(client):
    r = await client.get("/api/v1/auth/oauth/providers")
    assert r.status_code == 200
    assert r.json()[0]["enabled"] is False


async def test_full_oauth_login_flow(client, gh_api):
    r = await client.get(
        "/api/v1/auth/oauth/github/callback",
        params={"code": "c1", "state": "s1"},
        cookies={"oauth_state": "s1"},
    )
    assert r.status_code == 307
    assert "code=" in r.headers["location"]
    otc = r.headers["location"].split("code=")[1]

    r = await client.post("/api/v1/auth/oauth/exchange", json={"code": otc})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["access_token"] and data["refresh_token"]
    assert data["user"]["username"] == "dev_user"
    assert data["user"]["email"] == "dev@example.com"

    # 二次登录同一 GitHub 账号 → 命中绑定，不新建
    r = await client.get(
        "/api/v1/auth/oauth/github/callback",
        params={"code": "c2", "state": "s2"},
        cookies={"oauth_state": "s2"},
    )
    assert r.status_code == 307
    otc2 = r.headers["location"].split("code=")[1]
    r = await client.post("/api/v1/auth/oauth/exchange", json={"code": otc2})
    assert r.status_code == 200
    assert r.json()["user"]["username"] == "dev_user"


async def test_oauth_state_mismatch(client, gh_api):
    r = await client.get(
        "/api/v1/auth/oauth/github/callback",
        params={"code": "c1", "state": "wrong"},
        cookies={"oauth_state": "right"},
    )
    assert r.status_code == 307
    assert "error=state" in r.headers["location"]


async def test_oauth_exchange_requires_2fa(client, gh_api):
    # 注册站内账号（同 GitHub 邮箱）→ 开启 2FA → OAuth 绑定后必须过 TOTP
    await _register(client, "tfauser", email="dev@example.com")
    import os

    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.models import User

    # 直接用 DB 开启 2FA（测试态，绕过 UI 流程）
    engine = create_async_engine(
        os.environ.get("TEST_DATABASE_URL", "postgresql+asyncpg://harness:harness_dev_pw@localhost:5432/harness_test")
    )
    SessionX = async_sessionmaker(engine, expire_on_commit=False)
    async with SessionX() as s:
        u = (await s.execute(select(User).where(User.email == "dev@example.com"))).scalar_one()
        secret = pyotp.random_base32()
        u.totp_secret = secret
        u.totp_enabled = True
        await s.commit()
    await engine.dispose()

    # OAuth 登录（此时 gh_api 的 email=dev@example.com 与站内账号相同 → 绑定既有账号）
    r = await client.get(
        "/api/v1/auth/oauth/github/callback",
        params={"code": "c1", "state": "s1"},
        cookies={"oauth_state": "s1"},
    )
    assert r.status_code == 307
    otc = r.headers["location"].split("code=")[1]

    # 不带 TOTP → 428
    r = await client.post("/api/v1/auth/oauth/exchange", json={"code": otc})
    assert r.status_code == 428

    # 错误 TOTP → 401 且 OTC 保留可重试
    r = await client.post("/api/v1/auth/oauth/exchange", json={"code": otc, "totp_code": "000000"})
    assert r.status_code == 401

    # 正确 TOTP → 200
    code = pyotp.TOTP(secret).now()
    r = await client.post("/api/v1/auth/oauth/exchange", json={"code": otc, "totp_code": code})
    assert r.status_code == 200, r.text
    assert r.json()["user"]["email"] == "dev@example.com"
