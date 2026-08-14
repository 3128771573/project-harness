"""GitHub OAuth（SSO）登录：授权跳转 / 回调解析 / 一次性码兑换 token"""
import json
import re
import secrets
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..deps import get_role_by_name
from ..models import OAuthAccount, User
from ..schemas import OAuthExchangeRequest, OAuthProviderOut, Token
from ..security import ROLE_USER, hash_password
from ..services import login_alert
from ..services.loginlog import _parse_device, record_login, update_last_login
from .auth import _client_ip, _client_ua, _issue_tokens

router = APIRouter(prefix="/auth", tags=["oauth"])

# ---------- 一次性码（OTC）内存存储：otc -> {uid, provider, expires_ts, attempts} ----------
# 单实例部署适用（与 captcha 存储同模式）；多实例需换 Redis/DB
_OTC_TTL_SECONDS = 120
_OTC_MAX_ATTEMPTS = 5
_pending: dict[str, dict] = {}


def _time_now() -> float:
    return datetime.now(timezone.utc).timestamp()


def _clean_pending(now_ts: float):
    expired = [k for k, v in _pending.items() if v["expires_ts"] < now_ts]
    for k in expired:
        _pending.pop(k, None)


def _issue_otc(uid: str, provider: str) -> str:
    otc = secrets.token_urlsafe(24)
    _pending[otc] = {
        "uid": uid,
        "provider": provider,
        "expires_ts": _time_now() + _OTC_TTL_SECONDS,
        "attempts": 0,
    }
    return otc


def _redirect_uri() -> str:
    return f"{settings.PUBLIC_BASE_URL.rstrip('/')}/api/v1/auth/oauth/github/callback"


def _front_redirect(**params) -> RedirectResponse:
    """跳回前端落地页 /oauth/callback?provider=github&..."""
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(f"{settings.PUBLIC_BASE_URL.rstrip('/')}/oauth/callback?{qs}")


# ---------- 提供方能力探测（前端据此显示/隐藏按钮） ----------


@router.get("/oauth/providers", response_model=list[OAuthProviderOut])
async def oauth_providers():
    return [
        OAuthProviderOut(
            provider="github",
            name="GitHub",
            enabled=settings.github_oauth_enabled,
        )
    ]


# ---------- 1. 发起授权 ----------


@router.get("/oauth/github")
async def github_login(request: Request):
    if not settings.github_oauth_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GitHub 登录未启用")
    state = secrets.token_urlsafe(24)
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": _redirect_uri(),
        "scope": "read:user user:email",
        "state": state,
    }
    url = "https://github.com/login/oauth/authorize?" + "&".join(f"{k}={v}" for k, v in params.items())
    resp = RedirectResponse(url, status_code=302)
    resp.set_cookie(
        "oauth_state",
        state,
        max_age=600,
        path="/",
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
    )
    return resp


# ---------- 2. GitHub 回调（GitHub API 调用收敛为模块级函数，测试时 monkeypatch） ----------


async def gh_exchange_code(code: str) -> dict:
    """code 换 access_token；返回 {access_token, ...}"""
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": _redirect_uri(),
            },
            headers={"Accept": "application/json"},
        )
        return r.json()


async def gh_userinfo(access_token: str) -> dict:
    """拉取用户信息；返回 GitHub /user 响应（含 id, login, name, avatar_url, email）"""
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"},
        )
        return r.json()


async def gh_primary_email(access_token: str) -> str | None:
    """拉取邮箱列表，返回主邮箱且已验证的地址；无则 None（防止账号接管）"""
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"},
        )
        try:
            emails = r.json()
        except json.JSONDecodeError:
            return None
        for e in emails:
            if e.get("primary") and e.get("verified") and e.get("email"):
                return e["email"].lower().strip()
        return None


@router.get("/oauth/github/callback")
async def github_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    if not settings.github_oauth_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GitHub 登录未启用")
    if error:
        return _front_redirect(provider="github", error="denied")
    if not code or not state:
        return _front_redirect(provider="github", error="invalid")
    # state 校验（防 CSRF）
    cookie_state = request.cookies.get("oauth_state")
    if not cookie_state or cookie_state != state:
        return _front_redirect(provider="github", error="state")

    token_data = await gh_exchange_code(code)
    access_token = token_data.get("access_token")
    if not access_token:
        return _front_redirect(provider="github", error="token")

    gh_user = await gh_userinfo(access_token)
    gh_id = str(gh_user.get("id") or "")
    if not gh_id:
        return _front_redirect(provider="github", error="userinfo")

    email = await gh_primary_email(access_token)

    # ---- 账号解析：已绑定 → 同邮箱（verified）→ 新建 ----
    bound = (
        await db.execute(
            select(OAuthAccount).where(
                OAuthAccount.provider == "github", OAuthAccount.provider_sub == gh_id
            )
        )
    ).scalar_one_or_none()

    if bound is not None:
        user = await db.get(User, bound.uid)
    else:
        user = None
        if email:
            user = (
                await db.execute(select(User).where(User.email == email))
            ).scalar_one_or_none()
        if user is not None:
            # 绑定到既有账号（仅当邮箱 verified 才可能走到这里）
            db.add(
                OAuthAccount(
                    uid=user.uid,
                    provider="github",
                    provider_sub=gh_id,
                    email=email,
                    nickname=gh_user.get("name") or gh_user.get("login"),
                    avatar=gh_user.get("avatar_url"),
                )
            )
        else:
            user = await _create_oauth_user(db, gh_user, gh_id, email)

    if user is None or not user.is_active:
        return _front_redirect(provider="github", error="disabled")

    await db.commit()
    otc = _issue_otc(user.uid, "github")
    return _front_redirect(provider="github", code=otc)


async def _create_oauth_user(db: AsyncSession, gh_user: dict, gh_id: str, email: str | None) -> User:
    """自动注册：username 去重、无验证邮箱时用占位邮箱（保持 users.email 唯一/非空）"""
    base = re.sub(r"[^a-zA-Z0-9_]", "", gh_user.get("login") or "") or f"user{gh_id[:8]}"
    base = base[:24]
    if len(base) < 3:
        base = (base + "user")[:32]
    username = base
    for _ in range(5):
        exists = (
            await db.execute(select(User.id).where(User.username == username))
        ).scalar_one_or_none()
        if exists is None:
            break
        username = f"{base}_{secrets.token_hex(2)}"
    else:
        username = f"{base}_{secrets.token_hex(4)}"

    role = await get_role_by_name(db, ROLE_USER)
    gh_name = gh_user.get("name") or gh_user.get("login")
    user = User(
        username=username,
        email=(email or f"gh{gh_id}@oauth.local").lower(),
        password_hash=hash_password(secrets.token_urlsafe(24)),  # 随机密码，不可用密码登录
        nickname=gh_name[:64] if gh_name else None,
        avatar=gh_user.get("avatar_url"),
        role_id=role.id if role else None,
        # password_changed_at 保持 None：标记「无真实密码」，解绑保护用
    )
    db.add(user)
    await db.flush()
    db.add(
        OAuthAccount(
            uid=user.uid,
            provider="github",
            provider_sub=gh_id,
            email=user.email,
            nickname=user.nickname,
            avatar=user.avatar,
        )
    )
    return user


# ---------- 3. 前端兑换 token（含 2FA 二次校验） ----------


@router.post("/oauth/exchange", response_model=Token)
async def oauth_exchange(payload: OAuthExchangeRequest, request: Request, db: AsyncSession = Depends(get_db)):
    now_ts = _time_now()
    _clean_pending(now_ts)
    entry = _pending.pop(payload.code, None)  # 先取出：防止同一 OTC 并发重复使用
    if entry is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="登录凭据无效或已过期，请重新登录")
    if entry["expires_ts"] < now_ts:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="登录凭据已过期，请重新登录")
    if entry["attempts"] >= _OTC_MAX_ATTEMPTS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="尝试次数过多，请重新登录")

    user = await db.get(User, entry["uid"])
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")

    ip = _client_ip(request)
    ua = _client_ua(request)

    # 2FA：开启时校验 TOTP（未通过不消耗 OTC，允许重试，最多 5 次）
    if user.totp_enabled:
        if not payload.totp_code:
            _pending[payload.code] = entry  # 放回，等前端补 TOTP
            raise HTTPException(status_code=status.HTTP_428_PRECONDITION_REQUIRED, detail="需要两步验证码")
        import pyotp

        if not pyotp.TOTP(user.totp_secret or "").verify(payload.totp_code.strip(), valid_window=1):
            entry["attempts"] += 1
            _pending[payload.code] = entry
            await record_login(
                db, uid=user.uid, email=user.email, ip=ip, user_agent=ua, success=False, reason="两步验证码错误"
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="两步验证码错误")

    # 签发 token（复用 auth.py：refresh 入库、设备解析）
    tokens = await _issue_tokens(db, user, request)

    # 登录记录 + 新设备告警（与密码登录完全一致）
    device = _parse_device(ua)
    is_new = not await login_alert.is_known_login(db, user.uid, ip, device)
    await record_login(db, uid=user.uid, email=user.email, ip=ip, user_agent=ua, success=True, reason="GitHub 登录")
    await update_last_login(db, user, ip)
    if is_new:
        login_alert.schedule_login_alert(user.uid, user.email, ip, ua, device)
    return tokens
