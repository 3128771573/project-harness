"""站内私信（IM）：会话 / 消息 / 已读 / 撤回 / 隐藏 / 搜索 / 图片 / 文本水印取证 / WebSocket 实时通道

P0 范围：1v1 私信 + 公告机器人 + 文本暗水印取证（superadmin 专属）
群聊 / 拉黑管理 / 举报 / 像素水印 → P1（表结构已建）
"""
import json
import time
import uuid
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import SessionLocal, get_db
from ..deps import get_current_user, require_roles
from ..models import Block, DmConversation, DmConversationMember, DmMessage, GroupMember, GroupMessage, Report, User, WatermarkGrant, WatermarkLog
from ..schemas import (
    BotBroadcastIn,
    BotDmIn,
    BotHistoryItem,
    BotHistoryList,
    ImBlockIn,
    ImBlockOut,
    ImConversationList,
    ImConversationOut,
    ImDecodeTextIn,
    ImDecodeTextOut,
    ImLastMessageOut,
    ImMessageList,
    ImMessageOut,
    ImReportIn,
    ImSendIn,
    ImStartIn,
    ImUnreadOut,
    ImUserOut,
    ImUserSearchOut,
)
from ..security import ROLE_SUPER_ADMIN, decode_token
from ..deps import require_roles as _require_roles_im
from ..services.audit import record_audit
from ..services.bot import ensure_bot, get_or_create_dm, send_dm
from ..services.watermark import decode_text_watermark
from ..services.ws_manager import manager

router = APIRouter(prefix="/im", tags=["im"])

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
IM_MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
RECALL_WINDOW_SECONDS = 120  # 2 分钟内可撤回

# ===== 简易限流（进程内） =====
_MSG_LOG: dict[str, list[float]] = {}  # uid -> 发送时间戳（60 次/分钟）
_DECODE_LOG: dict[str, list[float]] = {}  # uid -> 取证调用（30 次/小时）


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_rate(log: dict[str, list[float]], key: str, limit: int, window: float) -> None:
    now = time.time()
    recent = [t for t in log.get(key, []) if now - t < window]
    if len(recent) >= limit:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="操作过于频繁，请稍后再试")
    recent.append(now)
    log[key] = recent


async def _is_blocked(db: AsyncSession, a: str, b: str) -> bool:
    row = await db.execute(
        select(Block).where(
            ((Block.uid == a) & (Block.blocked_uid == b)) | ((Block.uid == b) & (Block.blocked_uid == a))
        )
    )
    return row.scalar_one_or_none() is not None


async def _get_member(db: AsyncSession, conversation_id: str, uid: str) -> DmConversationMember | None:
    row = await db.execute(
        select(DmConversationMember).where(
            DmConversationMember.conversation_id == conversation_id, DmConversationMember.user_id == uid
        )
    )
    return row.scalar_one_or_none()


def _msg_out(m: DmMessage) -> dict:
    return {
        "id": m.id,
        "sender_id": m.sender_id,
        "kind": m.kind,
        "content": m.content,
        "status": m.status,
        "created_time": m.created_time,
    }


def _mask_email(email: str | None) -> str | None:
    if not email or "@" not in email:
        return email
    local, domain = email.split("@", 1)
    return f"{local[:1]}***@{domain}"


def _user_out(u: User) -> ImUserOut:
    return ImUserOut(uid=u.uid, username=u.username, nickname=u.nickname, avatar=u.avatar)


# ==================== 会话 ====================

@router.post("/conversations", response_model=ImConversationOut, summary="发起/获取与某用户的私信会话（幂等）")
async def start_conversation(
    payload: ImStartIn,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.user_id == current_user.uid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能与自己发起私信")
    target = await db.get(User, payload.user_id)
    if target is None or not target.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    if target.is_bot:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="机器人账号不可发起私信")
    if await _is_blocked(db, current_user.uid, target.uid):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无法与对方建立会话")
    conv = await get_or_create_dm(db, current_user.uid, target.uid)
    # 重新打开已隐藏的会话：解除本人隐藏
    my_member = await _get_member(db, conv.id, current_user.uid)
    if my_member and my_member.hidden:
        my_member.hidden = False
        await db.commit()
    return await _build_conv_out(db, conv, current_user.uid, target)


@router.get("/conversations", response_model=ImConversationList, summary="我的会话列表（按最近消息排序）")
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (
        await db.execute(
            select(DmConversation)
            .join(DmConversationMember, DmConversationMember.conversation_id == DmConversation.id)
            .where(DmConversationMember.user_id == current_user.uid, DmConversationMember.hidden.is_(False))
            .order_by(DmConversation.last_message_at.desc().nullslast(), DmConversation.created_time.desc())
        )
    ).scalars().all()
    convs = list(rows)
    # 批量取对端用户与最后一条消息
    other_ids = [c.user_b if c.user_a == current_user.uid else c.user_a for c in convs]
    users: dict[str, User] = {}
    if other_ids:
        urows = (await db.execute(select(User).where(User.uid.in_(other_ids)))).scalars().all()
        users = {u.uid: u for u in urows}
    last_map: dict[str, DmMessage] = {}
    if convs:
        lrows = (
            await db.execute(
                select(DmMessage)
                .where(DmMessage.conversation_id.in_([c.id for c in convs]))
                .order_by(DmMessage.created_time.desc())
            )
        ).scalars().all()
        for m in lrows:
            last_map.setdefault(m.conversation_id, m)
    items = []
    for c in convs:
        other = users.get(c.user_b if c.user_a == current_user.uid else c.user_a)
        if other is None:
            continue
        items.append(await _build_conv_out(db, c, current_user.uid, other, last_map=last_map))
    return ImConversationList(items=items, total=len(items))


async def _build_conv_out(
    db: AsyncSession,
    conv: DmConversation,
    me: str,
    other: User,
    last_map: dict[str, DmMessage] | None = None,
) -> ImConversationOut:
    my_member = await _get_member(db, conv.id, me)
    other_member = await _get_member(db, conv.id, other.uid)
    last_read_at = my_member.last_read_at if my_member else None
    unread = 0
    if last_read_at is None:
        unread = (
            await db.scalar(
                select(func.count())
                .select_from(DmMessage)
                .where(
                    DmMessage.conversation_id == conv.id,
                    DmMessage.sender_id != me,
                    DmMessage.status == "active",
                )
            )
            or 0
        )
    else:
        unread = (
            await db.scalar(
                select(func.count())
                .select_from(DmMessage)
                .where(
                    DmMessage.conversation_id == conv.id,
                    DmMessage.sender_id != me,
                    DmMessage.status == "active",
                    DmMessage.created_time > last_read_at,
                )
            )
            or 0
        )
    last = last_map.get(conv.id) if last_map else None
    if last is None:
        last = (
            await db.execute(
                select(DmMessage)
                .where(DmMessage.conversation_id == conv.id)
                .order_by(DmMessage.created_time.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
    return ImConversationOut(
        id=conv.id,
        other=_user_out(other),
        last_message=ImLastMessageOut(**_msg_out(last)) if last else None,
        unread=unread,
        other_last_read_at=other_member.last_read_at if other_member else None,
        last_message_at=conv.last_message_at,
        created_time=conv.created_time,
    )


@router.get("/conversations/{conversation_id}/messages", response_model=ImMessageList, summary="会话历史（新在前）")
async def list_messages(
    conversation_id: str,
    before: str | None = Query(default=None, description="ISO 时间，只取更早的消息"),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if await _get_member(db, conversation_id, current_user.uid) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    q = select(DmMessage).where(DmMessage.conversation_id == conversation_id)
    if before:
        try:
            before_dt = datetime.fromisoformat(before.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="before 参数格式错误")
        q = q.where(DmMessage.created_time < before_dt)
    q = q.order_by(DmMessage.created_time.desc()).limit(limit + 1)
    rows = (await db.execute(q)).scalars().all()
    has_more = len(rows) > limit
    items = [ImMessageOut(**_msg_out(m)) for m in rows[:limit]]
    return ImMessageList(items=items, has_more=has_more)


@router.post("/conversations/{conversation_id}/messages", response_model=ImMessageOut, summary="发送私信消息")
async def send_message(
    conversation_id: str,
    payload: ImSendIn,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if await _get_member(db, conversation_id, current_user.uid) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    conv = await db.get(DmConversation, conversation_id)
    other_uid = conv.user_b if conv.user_a == current_user.uid else conv.user_a
    if await _is_blocked(db, current_user.uid, other_uid):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无法发送消息（拉黑状态下双向禁止）")
    _check_rate(_MSG_LOG, current_user.uid, 60, 60)
    if payload.kind == "text":
        from ..services.moderation import check_content

        hit = await check_content(db, payload.content)
        if hit:
            await record_audit(db, actor=current_user, action="im.moderation_blocked", resource=f"word:{hit}", detail="敏感词拦截（私信）")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="内容包含违规内容，请修改后发送")
    message = await send_dm(db, conv, current_user.uid, payload.content, kind=payload.kind)
    # 发送即自读
    my_member = await _get_member(db, conversation_id, current_user.uid)
    if my_member:
        my_member.last_read_at = message.created_time
        await db.commit()
    return ImMessageOut(**_msg_out(message))


@router.post("/conversations/{conversation_id}/read", summary="标记会话已读")
async def mark_read(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await _get_member(db, conversation_id, current_user.uid)
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    member.last_read_at = datetime.now(timezone.utc)
    await db.commit()
    conv = await db.get(DmConversation, conversation_id)
    other_uid = conv.user_b if conv.user_a == current_user.uid else conv.user_a
    # 通知对方刷新「已读」标记
    await manager.broadcast(
        f"user:{other_uid}",
        {"type": "im.read", "conversation_id": conversation_id, "reader_uid": current_user.uid},
    )
    return {"ok": True}


@router.post("/messages/{message_id}/recall", response_model=ImMessageOut, summary="撤回消息（2 分钟内）")
async def recall_message(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    message = await db.get(DmMessage, message_id)
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="消息不存在")
    if await _get_member(db, message.conversation_id, current_user.uid) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="消息不存在")
    if message.sender_id != current_user.uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只能撤回自己发送的消息")
    if message.status == "recalled":
        return ImMessageOut(**_msg_out(message))
    if message.created_time is None or datetime.now(timezone.utc) - message.created_time > timedelta(seconds=RECALL_WINDOW_SECONDS):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="超过 2 分钟，无法撤回")
    message.status = "recalled"
    message.recalled_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(message)
    conv = await db.get(DmConversation, message.conversation_id)
    other_uid = conv.user_b if conv.user_a == current_user.uid else conv.user_a
    await record_audit(
        db,
        actor=current_user,
        action="im.recall",
        resource=f"dm_message:{message_id}",
        target_uid=other_uid,
        detail="撤回私信消息（审计保留元数据）",
    )
    await manager.broadcast(
        f"conv:{message.conversation_id}",
        {"type": "im.recalled", "conversation_id": message.conversation_id, "message_id": message_id},
    )
    return ImMessageOut(**_msg_out(message))


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除会话（仅隐藏本人视图）")
async def hide_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await _get_member(db, conversation_id, current_user.uid)
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    member.hidden = True
    await db.commit()
    await record_audit(db, actor=current_user, action="im.hide_conversation", resource=f"dm_conversation:{conversation_id}")
    return None


# ==================== 拉黑管理 ====================

@router.post("/blocks", response_model=ImBlockOut, status_code=status.HTTP_201_CREATED, summary="拉黑用户（双向互发禁止）")
async def block_user(
    payload: ImBlockIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.user_id == current_user.uid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能拉黑自己")
    target = await db.get(User, payload.user_id)
    if target is None or target.is_bot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    exists = (
        await db.execute(select(Block).where(Block.uid == current_user.uid, Block.blocked_uid == payload.user_id))
    ).scalar_one_or_none()
    if exists is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="已拉黑该用户")
    b = Block(uid=current_user.uid, blocked_uid=target.uid)
    db.add(b)
    await db.commit()
    await db.refresh(b)
    await record_audit(db, actor=current_user, action="im.block", target_uid=target.uid, detail="拉黑用户")
    return ImBlockOut(id=b.id, blocked=_user_out(target), created_time=b.created_time)


@router.get("/blocks", response_model=list[ImBlockOut], summary="我的拉黑列表")
async def list_blocks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (
        await db.execute(select(Block).where(Block.uid == current_user.uid).order_by(Block.created_time.desc()))
    ).scalars().all()
    out = []
    for b in rows:
        target = await db.get(User, b.blocked_uid)
        if target is not None:
            out.append(ImBlockOut(id=b.id, blocked=_user_out(target), created_time=b.created_time))
    return out


@router.delete("/blocks/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="取消拉黑")
async def unblock_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    b = (
        await db.execute(select(Block).where(Block.uid == current_user.uid, Block.blocked_uid == user_id))
    ).scalar_one_or_none()
    if b is not None:
        await db.delete(b)
        await db.commit()
        await record_audit(db, actor=current_user, action="im.unblock", target_uid=user_id, detail="取消拉黑")
    return None


# ==================== 举报（P0 落数据，P1 Admin 审核页） ====================

@router.post("/messages/{message_id}/report", status_code=status.HTTP_204_NO_CONTENT, summary="举报消息（进入审核队列）")
async def report_message(
    message_id: str,
    payload: ImReportIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    msg = await db.get(DmMessage, message_id)
    if msg is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="消息不存在")
    db.add(
        Report(
            reporter_id=current_user.uid,
            target_type="dm",
            target_id=msg.id,
            sender_uid=msg.sender_id,
            reason=payload.reason,
            detail=None,
            status="pending",
        )
    )
    await db.commit()
    await record_audit(db, actor=current_user, action="im.report", target_uid=msg.sender_id, detail=f"举报消息 {message_id}：{payload.reason}")
    return None


@router.get("/unread", response_model=ImUnreadOut, summary="总未读数（铃铛角标）")
async def unread_total(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    members = (
        await db.execute(
            select(DmConversationMember).where(
                DmConversationMember.user_id == current_user.uid, DmConversationMember.hidden.is_(False)
            )
        )
    ).scalars().all()
    total = 0
    for member in members:
        if member.last_read_at is None:
            n = (
                await db.scalar(
                    select(func.count())
                    .select_from(DmMessage)
                    .where(
                        DmMessage.conversation_id == member.conversation_id,
                        DmMessage.sender_id != current_user.uid,
                        DmMessage.status == "active",
                    )
                )
                or 0
            )
        else:
            n = (
                await db.scalar(
                    select(func.count())
                    .select_from(DmMessage)
                    .where(
                        DmMessage.conversation_id == member.conversation_id,
                        DmMessage.sender_id != current_user.uid,
                        DmMessage.status == "active",
                        DmMessage.created_time > member.last_read_at,
                    )
                )
                or 0
            )
        total += n
    # 群未读（同样计入铃铛角标）
    group_members = (
        await db.execute(select(GroupMember).where(GroupMember.user_id == current_user.uid))
    ).scalars().all()
    for gm in group_members:
        if gm.last_read_at is None:
            n = (
                await db.scalar(
                    select(func.count())
                    .select_from(GroupMessage)
                    .where(GroupMessage.group_id == gm.group_id, GroupMessage.sender_id != current_user.uid, GroupMessage.status == "active")
                )
                or 0
            )
        else:
            n = (
                await db.scalar(
                    select(func.count())
                    .select_from(GroupMessage)
                    .where(
                        GroupMessage.group_id == gm.group_id,
                        GroupMessage.sender_id != current_user.uid,
                        GroupMessage.status == "active",
                        GroupMessage.created_time > gm.last_read_at,
                    )
                )
                or 0
            )
        total += n
    return ImUnreadOut(total=total)


# ==================== 用户搜索 / 图片 ====================

@router.get("/users", response_model=ImUserSearchOut, summary="搜索可私信用户（排除机器人/自己/拉黑）")
async def search_users(
    q: str = Query(min_length=1, max_length=32),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    like = f"%{q}%"
    rows = (
        await db.execute(
            select(User)
            .where(
                User.uid != current_user.uid,
                User.is_bot.is_(False),
                User.is_active.is_(True),
                (User.username.contains(q, autoescape=True))
                | (User.nickname.contains(q, autoescape=True))
                | (User.email.contains(q, autoescape=True)),
            )
            .order_by(User.username)
            .limit(10)
        )
    ).scalars().all()
    blocked_uids = set()
    bres = await db.execute(
        select(Block.uid, Block.blocked_uid).where(
            (Block.uid == current_user.uid) | (Block.blocked_uid == current_user.uid)
        )
    )
    for bu, bbu in bres.all():
        blocked_uids.add(bu if bu != current_user.uid else bbu)
    items = [_user_out(u) for u in rows if u.uid not in blocked_uids]
    return ImUserSearchOut(items=items)


@router.post("/upload", summary="上传聊天图片（≤5MB，白名单格式）")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅支持 jpg/png/webp/gif 图片")
    content = await file.read()
    if len(content) > IM_MAX_IMAGE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="图片不能超过 5MB")
    # 真实图像内容校验 + 重编码剥离附加 payload（安全基线 §1.5）
    import io

    from PIL import Image

    try:
        img = Image.open(io.BytesIO(content))
        img.verify()
        img = Image.open(io.BytesIO(content))
        out = io.BytesIO()
        img.convert("RGB" if img.mode not in ("RGB", "RGBA") else img.mode).save(out, format="PNG")
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件不是有效图片")
    filename = f"{current_user.uid}_{uuid.uuid4().hex[:8]}.png"  # 统一转 PNG
    img_dir = Path(settings.UPLOAD_DIR) / "im"
    img_dir.mkdir(parents=True, exist_ok=True)
    (img_dir / filename).write_bytes(out.getvalue())
    return {"url": f"/uploads/im/{filename}"}


# ==================== 文本水印取证（superadmin 专属，P1 接入授权体系） ====================

async def _watermark_authorized(db: AsyncSession, user: User) -> tuple[bool, WatermarkGrant | None]:
    """水印取证授权：superadmin 直用；其他用户需有效授权（一次性/按次/长期）"""
    if user.role and user.role.name == ROLE_SUPER_ADMIN:
        return True, None
    now = datetime.now(timezone.utc)
    rows = await db.execute(
        select(WatermarkGrant).where(
            WatermarkGrant.user_id == user.uid,
            WatermarkGrant.revoked.is_(False),
            (WatermarkGrant.expires_at.is_(None)) | (WatermarkGrant.expires_at > now),
        )
    )
    for grant in rows.scalars().all():
        if grant.quota_type == "permanent":
            return True, grant
        if grant.quota_type == "times" and grant.max_uses is not None and grant.used_count < grant.max_uses:
            return True, grant
        if grant.quota_type == "one_time" and grant.used_count < 1:
            return True, grant
    return False, None


@router.post("/decode-text", response_model=ImDecodeTextOut, summary="解码复制文本中的零宽水印（superadmin 或获授权用户）")
async def decode_text_forensics(
    payload: ImDecodeTextIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _check_rate(_DECODE_LOG, current_user.uid, 30, 3600)
    authorized, grant = await _watermark_authorized(db, current_user)
    if not authorized:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权使用水印取证工具（需 superadmin 授权）")
    input_hash = sha256(payload.text.encode("utf-8")).hexdigest()
    result = decode_text_watermark(payload.text)
    is_superadmin = bool(current_user.role and current_user.role.name == ROLE_SUPER_ADMIN)
    if result is None:
        await record_audit(
            db, actor=current_user, action="im.watermark_decode_text", detail=f"input_sha256={input_hash} matched=false"
        )
        db.add(WatermarkLog(actor_id=current_user.uid, kind="text", input_hash=input_hash, matched_uid=None, consumed=False))
        await db.commit()
        return ImDecodeTextOut(matched=False, note="未识别到有效水印（可能已被清理零宽字符）")
    user = await db.get(User, result["uid"])
    if user is None or user.is_bot:
        await record_audit(
            db, actor=current_user, action="im.watermark_decode_text", detail=f"input_sha256={input_hash} matched_uid={result['uid']} user_gone=true"
        )
        db.add(WatermarkLog(actor_id=current_user.uid, kind="text", input_hash=input_hash, matched_uid=result["uid"], consumed=False))
        await db.commit()
        return ImDecodeTextOut(matched=False, note="水印有效但发送者账号已不存在")
    # 仅成功识别消耗授权额度（superadmin 不消耗）
    consumed = False
    if grant is not None and not is_superadmin:
        grant.used_count += 1
        consumed = True
    out_user = ImUserOut(
        uid=user.uid, username=user.username, nickname=user.nickname, avatar=user.avatar
    )
    db.add(WatermarkLog(
        actor_id=current_user.uid, kind="text", input_hash=input_hash,
        matched_uid=user.uid, consumed=consumed,
    ))
    await record_audit(
        db,
        actor=current_user,
        action="im.watermark_decode_text",
        target_uid=user.uid,
        detail=f"input_sha256={input_hash} matched=true message_id={result['message_id']} ts={result['ts']} consumed={consumed}",
    )
    return ImDecodeTextOut(
        matched=True,
        user=out_user,
        message_id=result["message_id"],
        ts=result["ts"],
        note="水印解码成功：发送者为 " + (user.nickname or user.username),
    )


# ==================== WebSocket 实时通道 ====================

@router.websocket("/ws")
async def im_ws(websocket: WebSocket):
    """实时私信推送：?token=<access_token>；客户端发 {type:join|leave, conversation_id} 进出会话房间"""
    token = websocket.query_params.get("token")
    uid = None
    if token:
        payload = decode_token(token)
        if payload and payload.get("type") == "access":
            uid = payload.get("sub")
    if not uid:
        await websocket.close(code=4401)
        return
    async with SessionLocal() as db:
        from ..services.maintenance import snapshot as _snap

        user = await db.get(User, uid)
        if user is None or not user.is_active or user.is_bot:
            await websocket.close(code=4401)
            return
        snap = await _snap(db)
        if snap["mode"] != "none":
            is_admin = bool(user.role and user.role.name in (ROLE_ADMIN, ROLE_SUPER_ADMIN))
            # 非管理员：full/scheduled/admin_only 拦截；block_new 允许已登录用户
            if not is_admin and snap["mode"] != "block_new":
                await websocket.close(code=1013)  # try again later：维护中
                return
    ok = await manager.connect(websocket, f"user:{uid}", uid)
    if not ok:
        return
    joined: set[str] = set()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except Exception:
                continue
            op = data.get("type")
            if op == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}, ensure_ascii=False))
                continue
            cid = data.get("conversation_id")
            gid = data.get("group_id")
            if op == "join" and cid:
                async with SessionLocal() as db:
                    member = await _get_member(db, cid, uid)
                if member is not None:
                    manager.join(websocket, f"conv:{cid}")
                    joined.add(cid)
            elif op == "join" and gid:
                async with SessionLocal() as db:
                    from ..models import GroupMember as _GM

                    gm = await db.execute(
                        select(_GM).where(_GM.group_id == gid, _GM.user_id == uid)
                    )
                    gmember = gm.scalar_one_or_none()
                if gmember is not None:
                    manager.join(websocket, f"g:{gid}")
                    joined.add(f"g:{gid}")
            elif op == "leave" and cid and cid in joined:
                manager.leave(websocket, f"conv:{cid}")
                joined.discard(cid)
            elif op == "leave" and gid and f"g:{gid}" in joined:
                manager.leave(websocket, f"g:{gid}")
                joined.discard(f"g:{gid}")
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        manager.disconnect(websocket, f"user:{uid}", uid)
        for cid in joined:
            manager.leave(websocket, f"conv:{cid}")
