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
    TwoFactorDisableRequest,
    TwoFactorSetupOut,
    TwoFactorSetupRequest,
    TwoFactorStatus,
    TwoFactorVerifyRequest,
)
from ..security import (
    generate_reset_token,
    hash_token,
    hash_password,
    validate_password_policy,
    verify_password,
)
from ..services.emailcode import invalidate_codes, send_verification_code, verify_code
from ..services.login_alert import is_known_login

router = APIRouter(prefix="/user", tags=["user"])

# ---------- 两步验证（TOTP） ----------


def _totp_uri(secret: str, email: str) -> str:
    """生成 otpauth URI（iPhone 密码本 / Google Authenticator 等标准扫码格式）"""
    from urllib.parse import quote

    issuer = "Harness Platform"
    label = quote(f"{issuer}:{email}", safe="")
    return f"otpauth://totp/{label}?secret={secret}&issuer={quote(issuer)}"


def _qr_svg_data_uri(uri: str) -> str:
    """生成二维码 SVG 并转为 data URI（前端 <img> 直接展示，免鉴权头问题）"""
    import base64

    import qrcode
    from qrcode.image.svg import SvgPathImage

    img = qrcode.make(uri, image_factory=SvgPathImage)
    svg = img.to_string()
    if isinstance(svg, str):
        svg = svg.encode("utf-8")
    return "data:image/svg+xml;base64," + base64.b64encode(svg).decode("ascii")


@router.get("/2fa/status", response_model=TwoFactorStatus, summary="两步验证状态")
async def two_factor_status(current_user: User = Depends(get_current_user)):
    return TwoFactorStatus(enabled=bool(current_user.totp_enabled))


@router.post("/2fa/setup", response_model=TwoFactorSetupOut, summary="开启两步验证（生成密钥与二维码）")
async def two_factor_setup(
    payload: TwoFactorSetupRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.totp_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="两步验证已开启")
    if not verify_password(payload.password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="密码错误")
    import pyotp

    secret = current_user.totp_secret or pyotp.random_base32()
    current_user.totp_secret = secret
    await db.commit()
    uri = _totp_uri(secret, current_user.email)
    return TwoFactorSetupOut(secret=secret, uri=uri, qr_data_uri=_qr_svg_data_uri(uri))


@router.post("/2fa/verify", response_model=TwoFactorStatus, summary="验证并启用两步验证")
async def two_factor_verify(
    payload: TwoFactorVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.totp_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请先完成设置")
    if current_user.totp_enabled:
        return TwoFactorStatus(enabled=True)
    import pyotp

    if not pyotp.TOTP(current_user.totp_secret).verify(payload.code.strip(), valid_window=1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码错误")
    current_user.totp_enabled = True
    await db.commit()
    return TwoFactorStatus(enabled=True)


@router.post("/2fa/disable", response_model=TwoFactorStatus, summary="关闭两步验证（需密码 + 验证码）")
async def two_factor_disable(
    payload: TwoFactorDisableRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.totp_enabled:
        return TwoFactorStatus(enabled=False)
    if not verify_password(payload.password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="密码错误")
    import pyotp

    if not pyotp.TOTP(current_user.totp_secret or "").verify(payload.code.strip(), valid_window=1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码错误")
    current_user.totp_secret = None
    current_user.totp_enabled = False
    await db.commit()
    return TwoFactorStatus(enabled=False)


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
    rows = result.scalars().all()
    items = []
    for l in rows:
        item = LoginLogItem.model_validate(l)
        # 新设备标记：此前 30 天内是否有同 IP 或同设备类型的成功登录
        if l.success:
            item.is_new_device = not await is_known_login(db, current_user.uid, l.ip, l.device, before=l.created_time)
        items.append(item)
    return LoginLogList(items=items, total=len(items))


