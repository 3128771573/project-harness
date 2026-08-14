"""群聊（P1）：建群 / 成员管理 / 群消息 / 撤回 / 举报 / 未读 / WS 群房间

权限模型：owner > admin > member
- 群主：全部操作（改群名/公告、邀请、踢人、转让、解散、退群需先转让）
- 管理员：改群名/公告、邀请、踢人（不可踢群主/管理员）
- 成员：发消息、撤回自己的消息、退群
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..deps import get_current_user
from ..models import GroupChat, GroupMember, GroupMessage, Report, User
from ..schemas import (
    GroupCreateIn,
    GroupDetailOut,
    GroupInviteIn,
    GroupKickIn,
    GroupList,
    GroupMemberOut,
    GroupMessageList,
    GroupMessageOut,
    GroupOut,
    GroupTransferIn,
    GroupUpdateIn,
    ImLastMessageOut,
    ImReportIn,
    ImSendIn,
    ImUserOut,
)
from ..services.audit import record_audit
from ..services.ws_manager import manager

router = APIRouter(prefix="/im", tags=["im-groups"])

RECALL_WINDOW_SECONDS = 120


def _user_out(u: User) -> ImUserOut:
    return ImUserOut(uid=u.uid, username=u.username, nickname=u.nickname, avatar=u.avatar)


async def _get_member(db: AsyncSession, gid: str, uid: str) -> GroupMember | None:
    row = await db.execute(
        select(GroupMember).where(GroupMember.group_id == gid, GroupMember.user_id == uid)
    )
    return row.scalar_one_or_none()


async def _require_member(db: AsyncSession, gid: str, uid: str) -> GroupMember:
    member = await _get_member(db, gid, uid)
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="群不存在或你不在群内")
    return member


async def _require_group(db: AsyncSession, gid: str) -> GroupChat:
    group = await db.get(GroupChat, gid)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="群不存在")
    return group


async def _require_owner_or_admin(db: AsyncSession, gid: str, uid: str) -> GroupMember:
    member = await _require_member(db, gid, uid)
    if member.role not in ("owner", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要群主或管理员权限")
    return member


async def _require_owner(db: AsyncSession, gid: str, uid: str) -> GroupMember:
    member = await _require_member(db, gid, uid)
    if member.role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要群主权限")
    return member


def _gm_out(m: GroupMessage) -> dict:
    return {
        "id": m.id,
        "group_id": m.group_id,
        "sender_id": m.sender_id,
        "kind": m.kind,
        "content": m.content if m.status == "active" else "",
        "status": m.status,
        "created_time": m.created_time,
    }


async def _group_out(db: AsyncSession, group: GroupChat, me: str) -> GroupOut:
    member = await _get_member(db, group.id, me)
    my_role = member.role if member else "member"
    member_count = (
        await db.scalar(select(func.count()).select_from(GroupMember).where(GroupMember.group_id == group.id)) or 0
    )
    last = (
        await db.execute(
            select(GroupMessage)
            .where(GroupMessage.group_id == group.id)
            .order_by(GroupMessage.created_time.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    unread = 0
    if member is not None:
        if member.last_read_at is None:
            unread = (
                await db.scalar(
                    select(func.count())
                    .select_from(GroupMessage)
                    .where(GroupMessage.group_id == group.id, GroupMessage.sender_id != me, GroupMessage.status == "active")
                )
                or 0
            )
        else:
            unread = (
                await db.scalar(
                    select(func.count())
                    .select_from(GroupMessage)
                    .where(
                        GroupMessage.group_id == group.id,
                        GroupMessage.sender_id != me,
                        GroupMessage.status == "active",
                        GroupMessage.created_time > member.last_read_at,
                    )
                )
                or 0
            )
    return GroupOut(
        id=group.id,
        name=group.name,
        owner_id=group.owner_id,
        my_role=my_role,
        member_count=member_count,
        announcement=group.announcement,
        last_message=ImLastMessageOut(**_gm_out(last)) if last else None,
        last_message_at=last.created_time if last else None,
        unread=unread,
        created_time=group.created_time,
    )


# ==================== 建群 / 列表 / 详情 ====================

@router.post("/groups", response_model=GroupOut, status_code=status.HTTP_201_CREATED, summary="创建群聊")
async def create_group(
    payload: GroupCreateIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    group = GroupChat(name=payload.name, owner_id=current_user.uid)
    db.add(group)
    await db.flush()
    db.add(GroupMember(group_id=group.id, user_id=current_user.uid, role="owner"))
    added = 0
    seen = {current_user.uid}
    for uid in dict.fromkeys(payload.member_uids):
        if uid in seen or uid == current_user.uid:
            continue
        target = await db.get(User, uid)
        if target is None or target.is_bot or not target.is_active:
            continue
        seen.add(uid)
        db.add(GroupMember(group_id=group.id, user_id=uid, role="member"))
        added += 1
        if added >= group.max_members - 1:
            break
    await db.commit()
    await db.refresh(group)
    await record_audit(db, actor=current_user, action="im.group_create", resource=f"group:{group.id}", detail=f"创建群「{payload.name}」初始成员 {added + 1} 人")
    return await _group_out(db, group, current_user.uid)


@router.get("/groups", response_model=GroupList, summary="我的群列表（按最后消息排序，含未读）")
async def list_groups(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (
        await db.execute(
            select(GroupChat)
            .join(GroupMember, GroupMember.group_id == GroupChat.id)
            .where(GroupMember.user_id == current_user.uid)
        )
    ).scalars().all()
    groups = list(rows)
    items = []
    for g in groups:
        items.append(await _group_out(db, g, current_user.uid))
    items.sort(key=lambda x: x.last_message_at or x.created_time, reverse=True)
    return GroupList(items=items, total=len(items))


@router.get("/groups/{gid}", response_model=GroupDetailOut, summary="群详情（含成员与角色）")
async def group_detail(
    gid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    group = await _require_group(db, gid)
    await _require_member(db, gid, current_user.uid)
    mrows = (
        await db.execute(
            select(GroupMember).where(GroupMember.group_id == gid).order_by(GroupMember.joined_time)
        )
    ).scalars().all()
    uids = [m.user_id for m in mrows]
    users: dict[str, User] = {}
    if uids:
        urows = (await db.execute(select(User).where(User.uid.in_(uids)))).scalars().all()
        users = {u.uid: u for u in urows}
    members = [
        GroupMemberOut(user=_user_out(users[m.user_id]), role=m.role, joined_time=m.joined_time)
        for m in mrows
        if m.user_id in users
    ]
    return GroupDetailOut(
        id=group.id,
        name=group.name,
        owner_id=group.owner_id,
        announcement=group.announcement,
        max_members=group.max_members,
        created_time=group.created_time,
        members=members,
    )


@router.get("/groups/{gid}/members", response_model=list[GroupMemberOut], summary="群成员列表")
async def group_members(
    gid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    group = await _require_group(db, gid)
    await _require_member(db, gid, current_user.uid)
    mrows = (
        await db.execute(
            select(GroupMember).where(GroupMember.group_id == gid).order_by(GroupMember.joined_time)
        )
    ).scalars().all()
    uids = [m.user_id for m in mrows]
    users: dict[str, User] = {}
    if uids:
        urows = (await db.execute(select(User).where(User.uid.in_(uids)))).scalars().all()
        users = {u.uid: u for u in urows}
    return [
        GroupMemberOut(user=_user_out(users[m.user_id]), role=m.role, joined_time=m.joined_time)
        for m in mrows
        if m.user_id in users
    ]


# ==================== 群设置 ====================

@router.put("/groups/{gid}", response_model=GroupOut, summary="修改群名/群公告（群主/管理员）")
async def update_group(
    gid: str,
    payload: GroupUpdateIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    group = await _require_group(db, gid)
    await _require_owner_or_admin(db, gid, current_user.uid)
    if payload.name is not None:
        group.name = payload.name
    if payload.announcement is not None:
        group.announcement = payload.announcement or None
    await db.commit()
    await db.refresh(group)
    await record_audit(db, actor=current_user, action="im.group_update", resource=f"group:{gid}", detail="修改群名/公告")
    return await _group_out(db, group, current_user.uid)


@router.post("/groups/{gid}/invite", response_model=GroupDetailOut, summary="邀请成员（群主/管理员）")
async def invite_members(
    gid: str,
    payload: GroupInviteIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    group = await _require_group(db, gid)
    await _require_owner_or_admin(db, gid, current_user.uid)
    cur_count = (
        await db.scalar(select(func.count()).select_from(GroupMember).where(GroupMember.group_id == gid)) or 0
    )
    invited = 0
    for uid in dict.fromkeys(payload.user_ids):
        if uid == current_user.uid:
            continue
        if await _get_member(db, gid, uid) is not None:
            continue
        target = await db.get(User, uid)
        if target is None or target.is_bot or not target.is_active:
            continue
        if cur_count + invited >= group.max_members:
            break
        db.add(GroupMember(group_id=gid, user_id=uid, role="member"))
        invited += 1
        await manager.broadcast(f"user:{uid}", {"type": "im.group_invited", "group_id": gid, "group_name": group.name})
    await db.commit()
    await record_audit(db, actor=current_user, action="im.group_invite", resource=f"group:{gid}", detail=f"邀请 {invited} 人")
    return await group_detail(gid, current_user, db)


@router.post("/groups/{gid}/kick", response_model=GroupDetailOut, summary="踢出成员（群主/管理员）")
async def kick_member(
    gid: str,
    payload: GroupKickIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    group = await _require_group(db, gid)
    actor = await _require_owner_or_admin(db, gid, current_user.uid)
    target_member = await _get_member(db, gid, payload.user_id)
    if target_member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="该用户不在群内")
    if target_member.role == "owner":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能踢出群主")
    if target_member.role == "admin" and actor.role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有群主能踢出管理员")
    if payload.user_id == current_user.uid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请使用退群")
    await db.delete(target_member)
    await db.commit()
    await record_audit(db, actor=current_user, action="im.group_kick", resource=f"group:{gid}", target_uid=payload.user_id, detail="踢出群成员")
    await manager.broadcast(f"user:{payload.user_id}", {"type": "im.group_kicked", "group_id": gid})
    return await group_detail(gid, current_user, db)


@router.post("/groups/{gid}/leave", status_code=status.HTTP_204_NO_CONTENT, summary="退出群聊")
async def leave_group(
    gid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    group = await _require_group(db, gid)
    member = await _require_member(db, gid, current_user.uid)
    if member.role == "owner":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="群主请先转让群主或解散群")
    await db.delete(member)
    await db.commit()
    await record_audit(db, actor=current_user, action="im.group_leave", resource=f"group:{gid}", detail="退出群聊")
    return None


@router.post("/groups/{gid}/transfer", response_model=GroupDetailOut, summary="转让群主（仅群主）")
async def transfer_owner(
    gid: str,
    payload: GroupTransferIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    group = await _require_group(db, gid)
    await _require_owner(db, gid, current_user.uid)
    target = await _get_member(db, gid, payload.user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="目标用户不在群内")
    actor = await _get_member(db, gid, current_user.uid)
    actor.role = "admin" if actor.role == "owner" else actor.role
    target.role = "owner"
    group.owner_id = target.user_id
    await db.commit()
    await record_audit(db, actor=current_user, action="im.group_transfer", resource=f"group:{gid}", target_uid=target.user_id, detail="转让群主")
    return await group_detail(gid, current_user, db)


@router.delete("/groups/{gid}", status_code=status.HTTP_204_NO_CONTENT, summary="解散群（仅群主）")
async def disband_group(
    gid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    group = await _require_group(db, gid)
    await _require_owner(db, gid, current_user.uid)
    # 按 FK 顺序 bulk 删除（ORM 逐对象 delete 无 relationship 时不保证顺序）
    member_rows = (await db.execute(select(GroupMember.user_id).where(GroupMember.group_id == gid))).all()
    member_uids = [r for (r,) in member_rows]
    await db.execute(delete(GroupMember).where(GroupMember.group_id == gid))
    await db.execute(delete(GroupMessage).where(GroupMessage.group_id == gid))
    await db.execute(delete(GroupChat).where(GroupChat.id == gid))
    await db.commit()
    await record_audit(db, actor=current_user, action="im.group_disband", resource=f"group:{gid}", detail="解散群聊")
    for uid in member_uids:
        await manager.broadcast(f"user:{uid}", {"type": "im.group_disbanded", "group_id": gid})
    return None


# ==================== 群消息 ====================

@router.get("/groups/{gid}/messages", response_model=GroupMessageList, summary="群消息历史（新在前）")
async def list_group_messages(
    gid: str,
    before: str | None = Query(default=None, description="ISO 时间游标"),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    group = await _require_group(db, gid)
    await _require_member(db, gid, current_user.uid)
    q = select(GroupMessage).where(GroupMessage.group_id == gid)
    if before:
        try:
            before_dt = datetime.fromisoformat(before.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="before 参数格式错误")
        q = q.where(GroupMessage.created_time < before_dt)
    q = q.order_by(GroupMessage.created_time.desc()).limit(limit + 1)
    rows = (await db.execute(q)).scalars().all()
    has_more = len(rows) > limit
    items = [GroupMessageOut(**_gm_out(m)) for m in rows[:limit]]
    return GroupMessageList(items=items, has_more=has_more)


@router.post("/groups/{gid}/messages", response_model=GroupMessageOut, status_code=status.HTTP_201_CREATED, summary="发送群消息")
async def send_group_message(
    gid: str,
    payload: ImSendIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    group = await _require_group(db, gid)
    await _require_member(db, gid, current_user.uid)
    msg = GroupMessage(group_id=gid, sender_id=current_user.uid, content=payload.content, kind=payload.kind)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    # 发送者自读
    member = await _get_member(db, gid, current_user.uid)
    if member:
        member.last_read_at = msg.created_time
        await db.commit()
    event = {
        "type": "im.group_message",
        "group_id": gid,
        "message": {
            "id": msg.id, "group_id": gid, "sender_id": msg.sender_id, "kind": msg.kind,
            "content": msg.content, "status": msg.status, "created_time": msg.created_time.isoformat(),
        },
    }
    await manager.broadcast(f"g:{gid}", event)
    member_rows = (await db.execute(select(GroupMember).where(GroupMember.group_id == gid))).scalars().all()
    for m in member_rows:
        await manager.broadcast(f"user:{m.user_id}", {"type": "im.group_update", "group_id": gid})
    return GroupMessageOut(**_gm_out(msg))


@router.post("/groups/{gid}/read", status_code=status.HTTP_204_NO_CONTENT, summary="标记群已读")
async def mark_group_read(
    gid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    group = await _require_group(db, gid)
    member = await _require_member(db, gid, current_user.uid)
    member.last_read_at = datetime.now(timezone.utc)
    await db.commit()
    return None


@router.post("/group-messages/{message_id}/recall", response_model=GroupMessageOut, summary="撤回群消息（2 分钟内）")
async def recall_group_message(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    msg = await db.get(GroupMessage, message_id)
    if msg is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="消息不存在")
    if await _get_member(db, msg.group_id, current_user.uid) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="消息不存在")
    if msg.sender_id != current_user.uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只能撤回自己发送的消息")
    if msg.status != "active":
        return GroupMessageOut(**_gm_out(msg))
    if datetime.now(timezone.utc) - msg.created_time > timedelta(seconds=RECALL_WINDOW_SECONDS):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="超过 2 分钟，无法撤回")
    msg.status = "recalled"
    msg.recalled_at = datetime.now(timezone.utc)
    await db.commit()
    await record_audit(db, actor=current_user, action="im.group_recall", resource=f"group_message:{message_id}", detail="撤回群消息")
    await manager.broadcast(
        f"g:{msg.group_id}",
        {"type": "im.group_recalled", "group_id": msg.group_id, "message_id": message_id},
    )
    return GroupMessageOut(**_gm_out(msg))


@router.post("/group-messages/{message_id}/report", status_code=status.HTTP_204_NO_CONTENT, summary="举报群消息")
async def report_group_message(
    message_id: str,
    payload: ImReportIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    msg = await db.get(GroupMessage, message_id)
    if msg is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="消息不存在")
    db.add(
        Report(
            reporter_id=current_user.uid,
            target_type="group",
            target_id=msg.id,
            reason=payload.reason,
            detail=None,
            status="pending",
        )
    )
    await db.commit()
    await record_audit(db, actor=current_user, action="im.report", target_uid=msg.sender_id, detail=f"举报群消息 {message_id}：{payload.reason}")
    return None
