from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..deps import get_current_user, get_role_by_name
from ..models import RefreshToken, User
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
    verify_password,
)
from ..services.emailcode import invalidate_codes, send_verification_code, verify_code
from ..services.loginlog import record_login, update_last_login

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str | None:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else None


def _client_ua(request: Request) -> str | None:
    return request.headers.get("user-agent")


async def _issue_tokens(db: AsyncSession, user: User, request: Request) -> Token:
    access = create_access_token(user.uid)
    refresh, jti, expires_at = create_refresh_token(user.uid)
    db.add(
        RefreshToken(
            uid=user.uid,
            jti=jti,
            expires_at=expires_at,
            device=_client_ua(request),
            ip=_client_ip(request),
        )
    )
    await db.commit()
    return Token(access_token=access, refresh_token=refresh, user=UserOut.model_validate(user))


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(User).where(or_(User.username == payload.username, User.email == payload.email))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名或邮箱已被注册")

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
        db, uid=user.uid, email=user.email, ip=_client_ip(request), user_agent=_client_ua(request), success=True
    )
    return await _issue_tokens(db, user, request)


@router.post("/send-code", summary="发送邮箱验证码")
async def send_code(payload: SendCodeRequest, db: AsyncSession = Depends(get_db)):
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
    from sqlalchemy import select as _select

    result = await db.execute(_select(User).where(User.email == payload.email.lower()))
    user = result.scalar_one_or_none()
    if user is None:
        return {"message": "如果该邮箱已注册，验证码已发送", "sent": False}
    resp = await send_verification_code(db, payload.email, "reset")
    return {"message": "验证码已发送到邮箱" if resp["sent"] else resp["message"], "sent": resp["sent"]}


@router.post("/reset-password", summary="使用邮箱验证码设置新密码")
async def reset_password(payload: ResetPasswordRequest, request: Request, db: AsyncSession = Depends(get_db)):
    from ..security import hash_password as _hp, validate_password_policy

    if not await verify_code(db, payload.email, payload.token, "reset"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码无效或已过期")

    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户不存在")

    policy_error = validate_password_policy(payload.new_password)
    if policy_error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=policy_error)

    user.password_hash = _hp(payload.new_password)
    user.password_changed_at = datetime.now(timezone.utc)
    await invalidate_codes(db, payload.email, "reset")

    result = await db.execute(
        select(RefreshToken).where(RefreshToken.uid == user.uid, RefreshToken.revoked.is_(False))
    )
    for t in result.scalars().all():
        t.revoked = True

    await db.commit()
    await record_login(db, uid=user.uid, email=user.email, ip=_client_ip(request), user_agent=_client_ua(request), success=True, reason="密码重置")
    return {"message": "密码已重置，请重新登录"}


@router.post("/login-code", response_model=Token, summary="邮箱验证码登录")
async def login_with_code(payload: CodeLoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    ip = _client_ip(request)
    ua = _client_ua(request)
    if not await verify_code(db, payload.email, payload.code, "login"):
        await record_login(db, email=payload.email.lower(), ip=ip, user_agent=ua, success=False, reason="验证码错误")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码无效或已过期")

    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="该邮箱未注册，请先注册")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")

    await record_login(db, uid=user.uid, email=user.email, ip=ip, user_agent=ua, success=True)
    await update_last_login(db, user, ip)
    return await _issue_tokens(db, user, request)


@router.post("/login", response_model=Token)
async def login(payload: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    ip = _client_ip(request)
    ua = _client_ua(request)
    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        await record_login(
            db, email=payload.email.lower(), ip=ip, user_agent=ua, success=False, reason="密码错误或账号不存在"
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误")
    if not user.is_active:
        await record_login(db, uid=user.uid, email=user.email, ip=ip, user_agent=ua, success=False, reason="账号已禁用")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")
    await record_login(db, uid=user.uid, email=user.email, ip=ip, user_agent=ua, success=True)
    await update_last_login(db, user, ip)
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
