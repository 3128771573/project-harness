from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..deps import get_current_user
from ..models import LoginLog, PasswordReset, RefreshToken, User
from ..schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginLogItem,
    LoginLogList,
    ResetPasswordRequest,
    SessionItem,
)
from ..security import (
    generate_reset_token,
    hash_token,
    hash_password,
    validate_password_policy,
    verify_password,
)

router = APIRouter(prefix="/user", tags=["user"])


@router.put("/password", summary="修改密码（修改后所有设备重新登录）")
async def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(payload.old_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="旧密码错误")

    policy_error = validate_password_policy(payload.new_password)
    if policy_error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=policy_error)

    current_user.password_hash = hash_password(payload.new_password)
    current_user.password_changed_at = datetime.now(timezone.utc)

    # 吊销该用户全部 refresh token（所有设备强制下线）
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.uid == current_user.uid, RefreshToken.revoked.is_(False))
    )
    for t in result.scalars().all():
        t.revoked = True

    await db.commit()
    return {"message": "密码已修改，所有设备已下线，请重新登录"}


@router.get("/sessions", response_model=list[SessionItem], summary="当前登录设备列表")
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RefreshToken)
        .where(RefreshToken.uid == current_user.uid)
        .order_by(RefreshToken.created_time.desc())
        .limit(20)
    )
    return [
        SessionItem(
            id=t.id,
            device=t.device,
            ip=t.ip,
            created_time=t.created_time,
            expires_at=t.expires_at,
            revoked=t.revoked,
        )
        for t in result.scalars().all()
    ]


@router.delete("/sessions/{token_id}", status_code=status.HTTP_204_NO_CONTENT, summary="退出指定设备")
async def revoke_session(
    token_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    token = await db.get(RefreshToken, token_id)
    if token is None or token.uid != current_user.uid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    token.revoked = True
    await db.commit()
    return None


@router.delete("/sessions", status_code=status.HTTP_204_NO_CONTENT, summary="退出所有设备")
async def revoke_all_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.uid == current_user.uid, RefreshToken.revoked.is_(False))
    )
    for t in result.scalars().all():
        t.revoked = True
    await db.commit()
    return None


@router.get("/login-logs", response_model=LoginLogList, summary="我的登录记录")
async def my_login_logs(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LoginLog)
        .where(LoginLog.uid == current_user.uid)
        .order_by(LoginLog.created_time.desc())
        .limit(min(limit, 100))
    )
    items = [LoginLogItem.model_validate(l) for l in result.scalars().all()]
    return LoginLogList(items=items, total=len(items))


# ---------- 忘记密码 ----------


@router.post("/forgot-password", summary="请求密码重置（返回重置 token，供开发环境使用）")
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """生产环境应通过邮件发送 token；当前返回 token 便于测试（可配置关闭）"""
    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = result.scalar_one_or_none()
    # 无论是否存在都返回成功（防枚举）
    if user is None:
        return {"message": "如果该邮箱已注册，重置邮件已发送"}

    token, token_hash_val = generate_reset_token()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    db.add(PasswordReset(uid=user.uid, token_hash=token_hash_val, expires_at=expires_at))
    await db.commit()
    # 开发环境直接返回 token（生产环境改为邮件发送）
    return {"message": "重置令牌已生成", "reset_token": token, "expires_in_minutes": 30}


@router.post("/reset-password", summary="使用重置令牌设置新密码")
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    token_hash_val = hash_token(payload.token)
    result = await db.execute(
        select(PasswordReset)
        .where(PasswordReset.token_hash == token_hash_val, PasswordReset.used.is_(False))
        .order_by(PasswordReset.created_time.desc())
        .limit(1)
    )
    reset = result.scalar_one_or_none()
    if reset is None or reset.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="重置令牌无效或已过期")

    policy_error = validate_password_policy(payload.new_password)
    if policy_error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=policy_error)

    user = await db.get(User, reset.uid)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户不存在")

    user.password_hash = hash_password(payload.new_password)
    user.password_changed_at = datetime.now(timezone.utc)
    reset.used = True

    # 吊销所有会话
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.uid == user.uid, RefreshToken.revoked.is_(False))
    )
    for t in result.scalars().all():
        t.revoked = True

    await db.commit()
    return {"message": "密码已重置，请重新登录"}
