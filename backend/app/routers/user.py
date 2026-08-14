import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..deps import get_current_user
from ..models import OAuthAccount, User
from ..schemas import OAuthAccountOut, ProfileUpdate, UserOut

router = APIRouter(prefix="/user", tags=["user"])

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def _to_out(user: User) -> UserOut:
    return UserOut.model_validate(user)


@router.get("/profile", response_model=UserOut)
async def get_profile(current_user: User = Depends(get_current_user)):
    return _to_out(current_user)


@router.put("/profile", response_model=UserOut)
async def update_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(current_user, field, value)
    await db.commit()
    await db.refresh(current_user)
    return _to_out(current_user)


@router.post("/avatar", response_model=UserOut)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅支持 jpg/png/webp/gif 图片")

    # 限制大小: 先写入临时读，超过限制拒绝
    content = await file.read()
    if len(content) > settings.MAX_AVATAR_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="头像不能超过 2MB")

    ext = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}[file.content_type]
    filename = f"{current_user.uid}_{uuid.uuid4().hex[:8]}.{ext}"

    avatar_dir = Path(settings.UPLOAD_DIR) / "avatars"
    avatar_dir.mkdir(parents=True, exist_ok=True)
    (avatar_dir / filename).write_bytes(content)

    # 通过 nginx 公开访问路径
    current_user.avatar = f"/uploads/avatars/{filename}"
    await db.commit()
    await db.refresh(current_user)
    return _to_out(current_user)


@router.get("/oauth-accounts", response_model=list[OAuthAccountOut], summary="我的第三方绑定列表")
async def my_oauth_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(OAuthAccount).where(OAuthAccount.uid == current_user.uid).order_by(OAuthAccount.created_time)
    )
    return [OAuthAccountOut.model_validate(a) for a in result.scalars().all()]


@router.post("/oauth/{provider}/unbind", summary="解绑第三方登录")
async def unbind_oauth(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if provider != "github":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不支持的第三方平台")
    result = await db.execute(
        select(OAuthAccount).where(OAuthAccount.uid == current_user.uid, OAuthAccount.provider == provider)
    )
    acc = result.scalar_one_or_none()
    if acc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未绑定该平台")
    # 防锁死：这是唯一登录方式且从未设置真实密码 → 拒绝解绑
    others = (
        await db.execute(
            select(OAuthAccount.id).where(OAuthAccount.uid == current_user.uid, OAuthAccount.id != acc.id)
        )
    ).scalar_one_or_none()
    if others is None and current_user.password_changed_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="这是您唯一的登录方式，请先在「修改密码」中设置密码后再解绑",
        )
    await db.delete(acc)
    await db.commit()
    return {"message": "已解绑"}
