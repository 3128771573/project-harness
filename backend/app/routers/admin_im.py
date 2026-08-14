"""Admin：公告机器人发送 + 举报审核 + 水印取证授权管理"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..deps import get_current_user, require_roles
from ..models import DmConversation, DmMessage, GroupMessage, Report, SensitiveWord, User, WatermarkGrant
from ..schemas import (
    BotBroadcastIn,
    BotDmIn,
    BotHistoryItem,
    BotHistoryList,
    ImUserOut,
    ReportAdminItem,
    ReportAdminList,
    ReportHandleIn,
    SensitiveWordIn,
    SensitiveWordList,
    SensitiveWordOut,
    WatermarkGrantIn,
    WatermarkGrantOut,
)
from ..security import ROLE_ADMIN, ROLE_SUPER_ADMIN
from ..services.audit import record_audit
from ..services.bot import BOT_UID, broadcast_bot, ensure_bot, send_bot_dm

router = APIRouter(prefix="/admin/im", tags=["admin-im"])

require_admin = require_roles(ROLE_ADMIN, ROLE_SUPER_ADMIN)
require_super = require_roles(ROLE_SUPER_ADMIN)


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



# ==================== 举报审核（P1） ====================

@router.get("/reports", response_model=ReportAdminList, summary="举报列表（默认待处理）")
async def list_reports(
    status_filter: str | None = Query(default=None, description="pending / handled / ignored"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    q = select(Report)
    if status_filter:
        q = q.where(Report.status == status_filter)
    total = (await db.scalar(select(func.count()).select_from(q.subquery()))) or 0
    rows = (
        await db.execute(q.order_by(Report.created_time.desc()).offset((page - 1) * page_size).limit(page_size))
    ).scalars().all()
    # 批量取举报者与消息
    reporter_ids = {r.reporter_id for r in rows}
    msg_ids = {r.target_id for r in rows}
    users: dict[str, User] = {}
    if reporter_ids:
        urows = (await db.execute(select(User).where(User.uid.in_(reporter_ids)))).scalars().all()
        users = {u.uid: u for u in urows}
    dm_msgs: dict[str, DmMessage] = {}
    gm_msgs: dict[str, GroupMessage] = {}
    if msg_ids:
        dm_rows = (await db.execute(select(DmMessage).where(DmMessage.id.in_(msg_ids)))).scalars().all()
        dm_msgs = {m.id: m for m in dm_rows}
        gm_rows = (await db.execute(select(GroupMessage).where(GroupMessage.id.in_(msg_ids)))).scalars().all()
        gm_msgs = {m.id: m for m in gm_rows}
    sender_ids = {m.sender_id for m in dm_msgs.values()} | {m.sender_id for m in gm_msgs.values()} | {r.sender_uid for r in rows if r.sender_uid}
    senders: dict[str, User] = {}
    if sender_ids:
        srows = (await db.execute(select(User).where(User.uid.in_(sender_ids)))).scalars().all()
        senders = {u.uid: u for u in srows}
    items = []
    for r in rows:
        msg = dm_msgs.get(r.target_id) or gm_msgs.get(r.target_id)
        sender_uid = (msg.sender_id if msg else None) or r.sender_uid
        sender = senders.get(sender_uid) if sender_uid else None
        items.append(
            ReportAdminItem(
                id=r.id,
                reporter=_user_out(users[r.reporter_id]) if r.reporter_id in users else ImUserOut(uid=r.reporter_id, username="已注销"),
                target_type=r.target_type,
                target_id=r.target_id,
                reason=r.reason,
                status=r.status,
                created_time=r.created_time,
                message_content=msg.content if msg and msg.status == "active" else ("（消息已撤回/删除）" if msg else None),
                message_sender=_user_out(sender) if sender else None,
            )
        )
    return ReportAdminList(items=items, total=total)


@router.post("/reports/{report_id}/handle", summary="处理举报（删除消息/封禁用户/忽略）+ 机器人私信告知")
async def handle_report(
    report_id: str,
    payload: ReportHandleIn,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    rep = await db.get(Report, report_id)
    if rep is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="举报不存在")
    if rep.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该举报已处理")
    result_note = ""
    if payload.action == "delete":
        msg = await db.get(DmMessage, rep.target_id)
        if msg is None:
            msg = await db.get(GroupMessage, rep.target_id)
        if msg is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="消息已不存在")
        msg.status = "removed"
        result_note = "消息已删除"
    elif payload.action == "ban":
        msg = await db.get(DmMessage, rep.target_id)
        if msg is None:
            msg = await db.get(GroupMessage, rep.target_id)
        sender_uid = (msg.sender_id if msg else None) or rep.sender_uid
        if sender_uid is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="无法定位发送者（消息已不存在且无记录）")
        target_user = await db.get(User, sender_uid)
        if target_user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="发送者账号已不存在")
        target_user.is_active = False
        result_note = "发送者账号已封禁"
    elif payload.action == "ignore":
        result_note = "已忽略"
    rep.status = "handled"
    rep.handled_by = current_user.uid
    rep.handled_at = datetime.now(timezone.utc)
    await db.commit()
    await record_audit(
        db, actor=current_user, action="im.report_handle", resource=f"report:{report_id}",
        detail=f"action={payload.action} note={payload.note or ''} {result_note}",
    )
    # 机器人私信告知举报者处理结果
    try:
        bot = await ensure_bot(db)
        await send_bot_dm(
            db, bot, rep.reporter_id,
            f"【举报处理结果】您举报的内容已处理：{result_note}" + (f"（备注：{payload.note}）" if payload.note else ""),
        )
    except Exception:
        pass
    return {"ok": True, "result": result_note}


# ==================== 水印取证授权（P1，superadmin） ====================

@router.get("/watermark/grants", response_model=list[WatermarkGrantOut], summary="授权列表")
async def list_grants(
    current_user: User = Depends(require_super),
    db: AsyncSession = Depends(get_db),
):
    rows = (
        await db.execute(select(WatermarkGrant).order_by(WatermarkGrant.created_time.desc()))
    ).scalars().all()
    uids = {g.user_id for g in rows}
    users: dict[str, User] = {}
    if uids:
        urows = (await db.execute(select(User).where(User.uid.in_(uids)))).scalars().all()
        users = {u.uid: u for u in urows}
    out = []
    for g in rows:
        if g.user_id not in users:
            continue
        out.append(
            WatermarkGrantOut(
                id=g.id,
                user=_user_out(users[g.user_id]),
                quota_type=g.quota_type,
                max_uses=g.max_uses,
                used_count=g.used_count,
                expires_at=g.expires_at,
                revoked=g.revoked,
                created_time=g.created_time,
            )
        )
    return out


@router.post("/watermark/grants", response_model=WatermarkGrantOut, status_code=status.HTTP_201_CREATED, summary="授予取证权限")
async def create_grant(
    payload: WatermarkGrantIn,
    current_user: User = Depends(require_super),
    db: AsyncSession = Depends(get_db),
):
    target = await db.get(User, payload.user_id)
    if target is None or target.is_bot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    if payload.quota_type == "times" and (payload.max_uses is None or payload.max_uses < 1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="按次授权需要填写次数")
    grant = WatermarkGrant(
        user_id=target.uid,
        granted_by=current_user.uid,
        quota_type=payload.quota_type,
        max_uses=payload.max_uses if payload.quota_type == "times" else (1 if payload.quota_type == "one_time" else None),
        expires_at=payload.expires_at,
    )
    db.add(grant)
    await db.commit()
    await db.refresh(grant)
    await record_audit(
        db, actor=current_user, action="im.watermark_grant", target_uid=target.uid,
        detail=f"quota_type={payload.quota_type} max_uses={grant.max_uses} expires={payload.expires_at or '永久'}",
    )
    return WatermarkGrantOut(
        id=grant.id, user=_user_out(target), quota_type=grant.quota_type, max_uses=grant.max_uses,
        used_count=grant.used_count, expires_at=grant.expires_at, revoked=grant.revoked, created_time=grant.created_time,
    )


@router.post("/watermark/grants/{grant_id}/revoke", summary="吊销授权")
async def revoke_grant(
    grant_id: str,
    current_user: User = Depends(require_super),
    db: AsyncSession = Depends(get_db),
):
    grant = await db.get(WatermarkGrant, grant_id)
    if grant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="授权不存在")
    grant.revoked = True
    await db.commit()
    await record_audit(db, actor=current_user, action="im.watermark_revoke", resource=f"grant:{grant_id}", target_uid=grant.user_id)
    return {"ok": True}



# ==================== 敏感词库（合规 FR8.3） ====================

@router.get("/sensitive-words", response_model=SensitiveWordList, summary="敏感词列表")
async def list_sensitive_words(
    q: str | None = Query(default=None, max_length=64),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    qb = select(SensitiveWord)
    if q:
        qb = qb.where(SensitiveWord.word.contains(q, autoescape=True))
    total = (await db.scalar(select(func.count()).select_from(qb.subquery()))) or 0
    rows = (
        await db.execute(qb.order_by(SensitiveWord.created_time.desc()).offset((page - 1) * page_size).limit(page_size))
    ).scalars().all()
    return SensitiveWordList(items=[SensitiveWordOut.model_validate(w) for w in rows], total=total)


@router.post("/sensitive-words", response_model=SensitiveWordOut, status_code=status.HTTP_201_CREATED, summary="新增敏感词")
async def create_sensitive_word(
    payload: SensitiveWordIn,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from ..services.moderation import invalidate_cache

    exists = (
        await db.execute(select(SensitiveWord).where(SensitiveWord.word == payload.word))
    ).scalar_one_or_none()
    if exists is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该词已存在")
    w = SensitiveWord(word=payload.word, category=payload.category)
    db.add(w)
    await db.commit()
    await db.refresh(w)
    invalidate_cache()
    await record_audit(db, actor=current_user, action="im.sensitive_word_add", detail=f"新增敏感词：{payload.word}")
    return SensitiveWordOut.model_validate(w)


@router.delete("/sensitive-words/{word_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除敏感词")
async def delete_sensitive_word(
    word_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from ..services.moderation import invalidate_cache

    w = await db.get(SensitiveWord, word_id)
    if w is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="词不存在")
    await db.delete(w)
    await db.commit()
    invalidate_cache()
    await record_audit(db, actor=current_user, action="im.sensitive_word_del", detail=f"删除敏感词：{w.word}")
    return None


@router.post("/sensitive-words/{word_id}/toggle", response_model=SensitiveWordOut, summary="启用/停用敏感词")
async def toggle_sensitive_word(
    word_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from ..services.moderation import invalidate_cache

    w = await db.get(SensitiveWord, word_id)
    if w is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="词不存在")
    w.enabled = not w.enabled
    await db.commit()
    await db.refresh(w)
    invalidate_cache()
    await record_audit(db, actor=current_user, action="im.sensitive_word_toggle", detail=f"{'启用' if w.enabled else '停用'}敏感词：{w.word}")
    return SensitiveWordOut.model_validate(w)


