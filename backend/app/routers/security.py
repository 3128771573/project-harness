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
from ..services.emailcode import invalidate_codes, send_verification_code, verify_code

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


@router.post("/forgot-password", summary="请求密码重置（发送邮箱验证码）")
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """发送重置密码验证码到邮箱"""
    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = result.scalar_one_or_none()
    if user is None:
        # 不暴露邮箱是否注册（防枚举）
        return {"message": "如果该邮箱已注册，验证码已发送", "sent": False}

    resp = await send_verification_code(db, payload.email, "reset")
    return {"message": "验证码已发送到邮箱" if resp["sent"] else resp["message"], "sent": resp["sent"]}


@router.post("/reset-password", summary="使用邮箱验证码设置新密码")
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    # payload.token 现在承载验证码
    if not await verify_code(db, payload.email, payload.token, "reset"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码无效或已过期")

    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户不存在")

    policy_error = validate_password_policy(payload.new_password)
    if policy_error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=policy_error)

    user.password_hash = hash_password(payload.new_password)
    user.password_changed_at = datetime.now(timezone.utc)
    await invalidate_codes(db, payload.email, "reset")

    # 吊销所有会话
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.uid == user.uid, RefreshToken.revoked.is_(False))
    )
    for t in result.scalars().all():
        t.revoked = True

    await db.commit()
    return {"message": "密码已重置，请重新登录"}
