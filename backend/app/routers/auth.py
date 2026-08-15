from collections import deque
from datetime import datetime, timezone
from time import time as _time

import pyotp
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..deps import get_current_user, get_role_by_name
from ..models import RefreshToken, User
from ..services import ratelimit
from ..services.httputil import client_ip
from ..schemas import (
    CodeLoginRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SendCodeRequest,
    Token,
    UserOut,
)
from ..security import (
    ROLE_USER,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    validate_password_policy,
    verify_password,
)

# 发送验证码的 IP 限速：ip -> 近 1 小时时间戳队列（内存版，单实例）
_send_code_log: dict[str, deque] = {}
_SEND_CODE_HOURLY_LIMIT = 10
from ..services.emailcode import invalidate_codes, send_verification_code, verify_code
from ..services import login_alert
from ..services.loginlog import _parse_device, record_login, update_last_login

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str | None:
    """可信 IP：nginx 注入的 X-Real-IP（客户端不可控）"""
    return client_ip(request)


def _client_ua(request: Request) -> str | None:
    return request.headers.get("user-agent")


def _device_hash(ua: str | None) -> str | None:
    if not ua:
        return None
    import hashlib

    return hashlib.sha256(ua.encode("utf-8")).hexdigest()


# 邮箱登录失败锁定（P2）：email -> 失败时间戳列表，5 次 / 15 分钟
_EMAIL_FAIL_LOG: dict[str, list[float]] = {}
_EMAIL_LOCK_MINUTES = 15
_EMAIL_LOCK_LIMIT = 5

# 登录时序侧信道防护：用户不存在也执行一次密码校验（恒定耗时）
_DUMMY_HASH: str | None = None


def _get_dummy_hash() -> str:
    global _DUMMY_HASH
    if _DUMMY_HASH is None:
        _DUMMY_HASH = hash_password("timing-equalizer-dummy-password")
    return _DUMMY_HASH


async def _issue_tokens(db: AsyncSession, user: User, request: Request) -> Token:
    access = create_access_token(user.uid)
    refresh, jti, expires_at = create_refresh_token(user.uid)
    db.add(
        RefreshToken(
            uid=user.uid,
            jti=jti,
            expires_at=expires_at,
            device=_parse_device(_client_ua(request))[:120],  # 原始 UA 可能超 128 列宽，存解析后的设备名
            device_hash=_device_hash(_client_ua(request)),
            ip=_client_ip(request),
        )
    )
    await db.commit()
    return Token(access_token=access, refresh_token=refresh, user=UserOut.model_validate(user))


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
    ip = _client_ip(request) or "unknown"
    if not ratelimit.check(f"register:{ip}", 5, 60):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="尝试过于频繁，请稍后再试")
    existing = await db.execute(
        select(User).where(or_(User.username == payload.username, User.email == payload.email))
    )
    if existing.scalar_one_or_none():
        # 枚举统一：不暴露存在性（依赖注册限流防轰炸）
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="注册未成功，请检查输入或稍后重试")

    # 邮箱验证码校验（无论 SMTP 是否配置，只要注册就必须验证码）
    if not payload.code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请先获取并填写邮箱验证码")
    if not await verify_code(db, payload.email, payload.code, "register"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码无效或已过期")

    role = await get_role_by_name(db, ROLE_USER)
    user = User(
        username=payload.username,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        role_id=role.id if role else None,
        password_changed_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.flush()
    await invalidate_codes(db, payload.email, "register")
    await record_login(
        db, uid=user.uid, email=user.email, ip=_client_ip(request), user_agent=_client_ua(request),
        method="register", success=True,
    )
    return await _issue_tokens(db, user, request)


@router.post("/send-code", summary="发送邮箱验证码")
async def send_code(payload: SendCodeRequest, request: Request, db: AsyncSession = Depends(get_db)):
    # IP 级限流：同一 IP 每小时最多 10 次（防 SMTP 轰炸）+ 60s 内 5 次（叠加）
    ip = _client_ip(request) or "unknown"
    if not ratelimit.check(f"sendcode:{ip}", 5, 60):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="发送过于频繁，请稍后再试")
    now_ts = _time()
    q = _send_code_log.setdefault(ip, deque())
    while q and q[0] < now_ts - 3600:
        q.popleft()
    if len(q) >= _SEND_CODE_HOURLY_LIMIT:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="发送过于频繁，请稍后再试")
    q.append(now_ts)

    try:
        result = await send_verification_code(db, payload.email, payload.purpose)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return result


@router.post("/forgot-password", summary="请求密码重置（发送邮箱验证码）")
async def forgot_password(
    payload: SendCodeRequest,
    db: AsyncSession = Depends(get_db),
):
    """发送重置密码验证码到邮箱"""
    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = result.scalar_one_or_none()
    if user is None:
        return {"message": "如果该邮箱已注册，验证码已发送", "sent": False}
    resp = await send_verification_code(db, payload.email, "reset")
    return {"message": "验证码已发送到邮箱" if resp["sent"] else resp["message"], "sent": resp["sent"]}


@router.post("/reset-password", summary="使用邮箱验证码设置新密码")
async def reset_password(payload: ResetPasswordRequest, request: Request, db: AsyncSession = Depends(get_db)):
    if not await verify_code(db, payload.email, payload.token, "reset"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码无效或已过期")

    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = result.scalar_one_or_none()
    if user is None:
        # 防枚举：与验证码错误同口径
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码无效或已过期")

    policy_error = validate_password_policy(payload.new_password)
    if policy_error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=policy_error)

    user.password_hash = hash_password(payload.new_password)
    user.password_changed_at = datetime.now(timezone.utc)
    await invalidate_codes(db, payload.email, "reset")

    result = await db.execute(
        select(RefreshToken).where(RefreshToken.uid == user.uid, RefreshToken.revoked.is_(False))
    )
    for t in result.scalars().all():
        t.revoked = True

    await db.commit()
    await record_login(db, uid=user.uid, email=user.email, ip=_client_ip(request), user_agent=_client_ua(request), method="reset", success=True, reason="密码重置")
    return {"message": "密码已重置，请重新登录"}


@router.post("/login-code", response_model=Token, summary="邮箱验证码登录")
async def login_with_code(payload: CodeLoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    ip = _client_ip(request) or "unknown"
    ua = _client_ua(request)
    if not ratelimit.check(f"login:{ip}", 5, 60):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="尝试过于频繁，请稍后再试")
    if not await verify_code(db, payload.email, payload.code, "login"):
        await record_login(db, email=payload.email.lower(), ip=ip, user_agent=ua, method="code", success=False, reason="验证码错误")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码无效或已过期")

    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = result.scalar_one_or_none()
    if user is None:
        # 防枚举：与验证码错误同口径
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码无效或已过期")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")
    if user.is_bot:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="机器人账号不可登录")

    # 两步验证（若已开启）
    used_2fa = False
    if user.totp_enabled:
        if not payload.totp_code:
            raise HTTPException(status_code=status.HTTP_428_PRECONDITION_REQUIRED, detail="需要两步验证码")
        if not pyotp.TOTP(user.totp_secret or "").verify(payload.totp_code.strip(), valid_window=1):
            await record_login(
                db, uid=user.uid, email=user.email, ip=ip, user_agent=ua, method="code", success=False, reason="两步验证码错误"
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="两步验证码错误")
        used_2fa = True

    device = _parse_device(ua)
    is_new = not await login_alert.is_known_login(db, user.uid, ip, device)
    await record_login(db, uid=user.uid, email=user.email, ip=ip, user_agent=ua, method="code", used_2fa=used_2fa, success=True)
    await update_last_login(db, user, ip)
    if is_new:
        login_alert.schedule_login_alert(user.uid, user.email, ip, ua, device)
    return await _issue_tokens(db, user, request)


@router.post("/login", response_model=Token)
async def login(payload: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    ip = _client_ip(request) or "unknown"
    ua = _client_ua(request)
    # IP 限流：5 次 / 60s（防字典爆破）
    if not ratelimit.check(f"login:{ip}", 5, 60):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="尝试过于频繁，请稍后再试")
    # 邮箱失败锁定：5 次 / 15 分钟
    from time import time as _now_ts

    now_ts = _now_ts()
    fails = [t for t in _EMAIL_FAIL_LOG.get(payload.email.lower(), []) if now_ts - t < _EMAIL_LOCK_MINUTES * 60]
    if len(fails) >= _EMAIL_LOCK_LIMIT:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="尝试过于频繁，请 15 分钟后再试")
    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = result.scalar_one_or_none()
    if user is not None and user.is_bot:
        await record_login(db, uid=user.uid, email=user.email, ip=ip, user_agent=ua, method="password", success=False, reason="机器人账号不可登录")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="机器人账号不可登录")
    if user is None:
        # 时序侧信道防护：用户不存在也执行一次密码校验（恒定耗时）
        verify_password(payload.password, _get_dummy_hash())
        _EMAIL_FAIL_LOG.setdefault(payload.email.lower(), []).append(now_ts)
        await record_login(
            db, email=payload.email.lower(), ip=ip, user_agent=ua, method="password", success=False, reason="密码错误或账号不存在"
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误")
    if not verify_password(payload.password, user.password_hash):
        _EMAIL_FAIL_LOG.setdefault(payload.email.lower(), []).append(now_ts)
        await record_login(
            db, email=payload.email.lower(), ip=ip, user_agent=ua, method="password", success=False, reason="密码错误或账号不存在"
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误")
    # 登录成功：解除邮箱锁定
    _EMAIL_FAIL_LOG.pop(payload.email.lower(), None)
    ratelimit.reset(f"login:{ip}")
    if not user.is_active:
        await record_login(db, uid=user.uid, email=user.email, ip=ip, user_agent=ua, method="password", success=False, reason="账号已禁用")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")

    # 两步验证（若已开启）
    used_2fa = False
    if user.totp_enabled:
        if not payload.totp_code:
            raise HTTPException(status_code=status.HTTP_428_PRECONDITION_REQUIRED, detail="需要两步验证码")
        if not pyotp.TOTP(user.totp_secret or "").verify(payload.totp_code.strip(), valid_window=1):
            await record_login(
                db, uid=user.uid, email=user.email, ip=ip, user_agent=ua, method="password", success=False, reason="两步验证码错误"
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="两步验证码错误")
        used_2fa = True

    device = _parse_device(ua)
    is_new = not await login_alert.is_known_login(db, user.uid, ip, device)
    await record_login(db, uid=user.uid, email=user.email, ip=ip, user_agent=ua, method="password", used_2fa=used_2fa, success=True)
    await update_last_login(db, user, ip)
    if is_new:
        login_alert.schedule_login_alert(user.uid, user.email, ip, ua, device)
    return await _issue_tokens(db, user, request)


@router.post("/refresh", response_model=Token)
async def refresh(payload: RefreshRequest, request: Request, db: AsyncSession = Depends(get_db)):
    data = decode_token(payload.refresh_token)
    if data is None or data.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新凭证无效")

    jti = data.get("jti")
    uid = data.get("sub")
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.jti == jti, RefreshToken.uid == uid, RefreshToken.revoked.is_(False))
    )
    stored = result.scalar_one_or_none()
    if stored is None or stored.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新凭证已失效")

    # 设备绑定硬校验：UA 哈希不一致 → 判定 token 被盗用，吊销该用户全部刷新凭证
    device_hash = _device_hash(_client_ua(request))
    if stored.device_hash and device_hash and stored.device_hash != device_hash:
        from sqlalchemy import delete as _delete

        await db.execute(_delete(RefreshToken).where(RefreshToken.uid == uid))
        await db.commit()
        from ..services.audit import record_audit

        await record_audit(
            db, actor=None, action="auth.refresh_device_mismatch", target_uid=uid,
            detail="刷新凭证设备指纹不匹配，已吊销全部会话（疑似盗用）",
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新凭证已失效")

    # 轮换: 吊销旧 token，签发新 token
    stored.revoked = True
    user = await db.get(User, uid)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或已禁用")
    await db.flush()
    return await _issue_tokens(db, user, request)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    data = decode_token(payload.refresh_token)
    if data and data.get("type") == "refresh":
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.jti == data.get("jti"), RefreshToken.revoked.is_(False))
        )
        stored = result.scalar_one_or_none()
        if stored:
            stored.revoked = True
            await db.commit()
    return None
