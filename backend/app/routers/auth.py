from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..deps import get_current_user, get_role_by_name
from ..models import RefreshToken, User
from ..schemas import ProfileUpdate, RefreshRequest, Token, UserCreate, UserLogin, UserOut
from ..security import (
    ROLE_USER,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


async def _issue_tokens(db: AsyncSession, user: User) -> Token:
    access = create_access_token(user.uid)
    refresh, jti, expires_at = create_refresh_token(user.uid)
    db.add(RefreshToken(uid=user.uid, jti=jti, expires_at=expires_at))
    await db.commit()
    return Token(access_token=access, refresh_token=refresh, user=UserOut.model_validate(user))


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(User).where(or_(User.username == payload.username, User.email == payload.email))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名或邮箱已被注册")

    role = await get_role_by_name(db, ROLE_USER)
    user = User(
        username=payload.username,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        role_id=role.id if role else None,
    )
    db.add(user)
    await db.flush()
    return await _issue_tokens(db, user)


@router.post("/login", response_model=Token)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")
    return await _issue_tokens(db, user)


@router.post("/refresh", response_model=Token)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    data = decode_token(payload.refresh_token)
    if data is None or data.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新凭证无效")

    jti = data.get("jti")
    uid = data.get("sub")
    # 校验 refresh token 是否在库且未吊销
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
    return await _issue_tokens(db, user)


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
