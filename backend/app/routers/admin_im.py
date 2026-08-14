"""Admin：公告机器人发送（全量广播 / 定向私信 / 发送记录）"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..deps import get_current_user, require_roles
from ..models import DmConversation, DmMessage, User
from ..schemas import BotBroadcastIn, BotDmIn, BotHistoryItem, BotHistoryList, ImUserOut
from ..security import ROLE_ADMIN, ROLE_SUPER_ADMIN
from ..services.audit import record_audit
from ..services.bot import BOT_UID, broadcast_bot, ensure_bot, send_bot_dm

router = APIRouter(prefix="/admin/im", tags=["admin-im"])

require_admin = require_roles(ROLE_ADMIN, ROLE_SUPER_ADMIN)


def _user_out(u: User) -> ImUserOut:
    return ImUserOut(uid=u.uid, username=u.username, nickname=u.nickname, avatar=u.avatar)


@router.post("/broadcast", summary="公告机器人全量广播（私信触达所有活跃用户）")
async def bot_broadcast(
    payload: BotBroadcastIn,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    bot = await ensure_bot(db)
    sent = await broadcast_bot(db, bot, payload.content)
    await record_audit(
        db,
        actor=current_user,
        action="bot.broadcast",
        resource=f"dm_users:{sent}",
        detail=f"机器人全量广播 {sent} 人" + (f"；原因：{payload.reason}" if payload.reason else ""),
    )
    return {"sent": sent}


@router.post("/dm", summary="公告机器人定向私信")
async def bot_dm(
    payload: BotDmIn,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    target = await db.get(User, payload.user_id)
    if target is None or not target.is_active or target.is_bot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="目标用户不存在")
    bot = await ensure_bot(db)
    message = await send_bot_dm(db, bot, target.uid, payload.content)
    await record_audit(
        db,
        actor=current_user,
        action="bot.dm",
        resource=f"dm_message:{message.id}",
        target_uid=target.uid,
        detail="机器人定向私信",
    )
    return {"ok": True, "message_id": message.id}


@router.get("/history", response_model=BotHistoryList, summary="机器人最近发送记录")
async def bot_history(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    rows = (
        await db.execute(
            select(DmMessage)
            .where(DmMessage.sender_id == BOT_UID)
            .order_by(DmMessage.created_time.desc())
            .limit(limit)
        )
    ).scalars().all()
    conv_ids = [m.conversation_id for m in rows]
    convs: dict[str, DmConversation] = {}
    if conv_ids:
        crows = (await db.execute(select(DmConversation).where(DmConversation.id.in_(conv_ids)))).scalars().all()
        convs = {c.id: c for c in crows}
    other_ids = set()
    for m in rows:
        c = convs.get(m.conversation_id)
        if c:
            other_ids.add(c.user_b if c.user_a == BOT_UID else c.user_a)
    users: dict[str, User] = {}
    if other_ids:
        urows = (await db.execute(select(User).where(User.uid.in_(other_ids)))).scalars().all()
        users = {u.uid: u for u in urows}
    items = []
    for m in rows:
        c = convs.get(m.conversation_id)
        if not c:
            continue
        other = users.get(c.user_b if c.user_a == BOT_UID else c.user_a)
        if other is None:
            continue
        items.append(
            BotHistoryItem(
                id=m.id, to=_user_out(other), content=m.content, kind=m.kind, created_time=m.created_time
            )
        )
    return BotHistoryList(items=items, total=len(items))
