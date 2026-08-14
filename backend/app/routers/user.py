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



# ==================== 账号注销（合规：个人信息删除权） ====================

@router.post("/deactivate", summary="注销账号（需密码确认；私信删除、群消息匿名化）")
async def deactivate_account(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timezone

    from fastapi import HTTPException, status
    from sqlalchemy import delete, update

    from ..models import (
        Block,
        DmConversation,
        DmConversationMember,
        DmMessage,
        GroupChat,
        GroupMember,
        GroupMessage,
        LoginLog,
        OAuthAccount,
        RefreshToken,
        EmailCode,
    )
    from ..security import hash_password, verify_password
    from ..services.audit import record_audit

    password = (body or {}).get("password", "")
    if not verify_password(password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="密码不正确")
    uid = current_user.uid
    # 私信：整库删除该用户参与的会话与消息（含机器人会话）
    conv_ids = [
        cid for (cid,) in (
            await db.execute(
                select(DmConversation.id).where(
                    (DmConversation.user_a == uid) | (DmConversation.user_b == uid)
                )
            )
        ).all()
    ]
    if conv_ids:
        await db.execute(delete(DmMessage).where(DmMessage.conversation_id.in_(conv_ids)))
        await db.execute(delete(DmConversationMember).where(DmConversationMember.conversation_id.in_(conv_ids)))
        await db.execute(delete(DmConversation).where(DmConversation.id.in_(conv_ids)))
    # 群消息匿名化：发送者改为「已注销用户」占位账号（保留群历史）
    placeholder_uid = "00000000-0000-4000-8000-000000000001"
    ph = await db.get(User, placeholder_uid)
    if ph is None:
        ph = User(
            uid=placeholder_uid,
            username="deleted_user",
            email="deleted-user@platformharness.ltd",
            password_hash=hash_password("no-login-" + __import__("secrets").token_hex(24)),
            nickname="已注销用户",
            is_bot=True,
        )
        db.add(ph)
        await db.flush()
    await db.execute(update(GroupMessage).where(GroupMessage.sender_id == uid).values(sender_id=placeholder_uid))
    # 群主身份处理：转让给任一成员；无成员则解散群
    owner_groups = (await db.execute(select(GroupChat).where(GroupChat.owner_id == uid))).scalars().all()
    for grp in owner_groups:
        successor = (
            await db.execute(
                select(GroupMember)
                .where(GroupMember.group_id == grp.id, GroupMember.user_id != uid)
                .order_by(GroupMember.joined_time)
                .limit(1)
            )
        ).scalar_one_or_none()
        if successor is not None:
            grp.owner_id = successor.user_id
            successor.role = "owner"
        else:
            await db.execute(delete(GroupMessage).where(GroupMessage.group_id == grp.id))
            await db.execute(delete(GroupMember).where(GroupMember.group_id == grp.id))
            await db.execute(delete(GroupChat).where(GroupChat.id == grp.id))
    # 退出所有群
    await db.execute(delete(GroupMember).where(GroupMember.user_id == uid))
    # 清理关联数据
    await db.execute(delete(Block).where((Block.uid == uid) | (Block.blocked_uid == uid)))
    await db.execute(delete(RefreshToken).where(RefreshToken.uid == uid))
    await db.execute(delete(LoginLog).where(LoginLog.uid == uid))
    await db.execute(delete(EmailCode).where(EmailCode.email == current_user.email))
    await db.execute(delete(OAuthAccount).where(OAuthAccount.uid == uid))
    # 头像文件删除
    if current_user.avatar and current_user.avatar.startswith("/uploads/"):
        try:
            (Path(settings.UPLOAD_DIR) / current_user.avatar.removeprefix("/uploads/")).unlink(missing_ok=True)
        except Exception:
            pass
    # 清除可识别信息 + 禁用账号
    current_user.is_active = False
    current_user.email = f"deleted-{uid}@platformharness.ltd"
    current_user.username = f"user_{uid[:8]}"
    current_user.nickname = "已注销用户"
    current_user.avatar = None
    current_user.bio = None
    current_user.totp_enabled = False
    current_user.totp_secret = None
    await db.commit()
    await record_audit(db, actor=current_user, action="user.deactivate", detail="用户自助注销（私信删除/群消息匿名化）")
    return {"message": "账号已注销，感谢使用"}


@router.get("/conversations/{cid}/export", summary="导出聊天记录（数据携带权）")
async def export_conversation(
    cid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timezone

    from fastapi import Response

    from ..models import DmConversation as _DmConv
    from ..models import DmConversationMember as _DmMember
    from ..models import DmMessage as _DmMsg

    member = (
        await db.execute(
            select(_DmMember).where(_DmMember.conversation_id == cid, _DmMember.user_id == current_user.uid)
        )
    ).scalar_one_or_none()
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    conv = await db.get(_DmConv, cid)
    other_uid = conv.user_b if conv.user_a == current_user.uid else conv.user_a
    other = await db.get(User, other_uid)
    msgs = (
        await db.execute(
            select(_DmMsg)
            .where(_DmMsg.conversation_id == cid)
            .order_by(_DmMsg.created_time.asc())
        )
    ).scalars().all()
    other_name = (other.nickname or other.username) if other else "已注销用户"
    lines = [
        f"与 {other_name} 的私信记录",
        f"导出时间：{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC",
        "=" * 40,
    ]
    for m in msgs:
        who = "我" if m.sender_id == current_user.uid else other_name
        t = m.created_time.strftime("%Y-%m-%d %H:%M:%S") if m.created_time else ""
        if m.status == "recalled":
            lines.append(f"[{t}] {who}：［已撤回］")
        elif m.status == "removed":
            lines.append(f"[{t}] {who}：［已被管理员删除］")
        elif m.kind == "image":
            lines.append(f"[{t}] {who}：［图片］ {m.content}")
        else:
            lines.append(f"[{t}] {who}：{m.content}")
    content = "\n".join(lines)
    return Response(
        content=content,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="chat-{cid[:8]}.txt"'},
    )

