"""公告机器账号「Harness 官方」：全量广播 / 定向私信 / 会话复用

- uid 固定保留（bot-harness-official），不可登录、不可被搜索、不可被发起私信
- 消息由服务端代码驱动（管理员操作触发），全程审计
"""
import secrets
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import DmConversation, DmConversationMember, DmMessage, User
from ..security import hash_password
from .ws_manager import manager

BOT_UID = "bot-harness-official"
BOT_EMAIL = "bot@platformharness.ltd"
BOT_USERNAME = "harness_official"
BOT_NICKNAME = "Harness 官方"


async def ensure_bot(db: AsyncSession) -> User:
    """启动时确保机器人账号存在（幂等）"""
    user = await db.get(User, BOT_UID)
    if user is None:
        user = (
            await db.execute(select(User).where(User.email == BOT_EMAIL))
        ).scalar_one_or_none()
    if user is None:
        user = User(
            uid=BOT_UID,
            email=BOT_EMAIL,
            username=BOT_USERNAME,
            nickname=BOT_NICKNAME,
            password_hash=hash_password("bot-no-login-" + secrets.token_hex(24)),
            is_bot=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    elif not user.is_bot:
        user.is_bot = True
        await db.commit()
        await db.refresh(user)
    return user


async def get_or_create_dm(db: AsyncSession, uid_a: str, uid_b: str):
    """获取或创建 1v1 会话（user_a < user_b 规范排序，幂等）"""
    a, b = sorted([uid_a, uid_b])
    conv = (
        await db.execute(
            select(DmConversation).where(DmConversation.user_a == a, DmConversation.user_b == b)
        )
    ).scalar_one_or_none()
    if conv is None:
        conv = DmConversation(user_a=a, user_b=b)
        db.add(conv)
        await db.flush()
        db.add(DmConversationMember(conversation_id=conv.id, user_id=a))
        db.add(DmConversationMember(conversation_id=conv.id, user_id=b))
        await db.commit()
        await db.refresh(conv)
    else:
        # 幂等兜底：确保双方成员行存在（历史数据安全）
        for uid in (a, b):
            member = (
                await db.execute(
                    select(DmConversationMember).where(
                        DmConversationMember.conversation_id == conv.id,
                        DmConversationMember.user_id == uid,
                    )
                )
            ).scalar_one_or_none()
            if member is None:
                db.add(DmConversationMember(conversation_id=conv.id, user_id=uid))
        await db.commit()
    return conv


async def send_dm(db: AsyncSession, conv: DmConversation, sender_id: str, content: str, kind: str = "text") -> DmMessage:
    """写入私信消息并推送 WS（用户房间 + 会话房间）"""
    message = DmMessage(conversation_id=conv.id, sender_id=sender_id, content=content, kind=kind)
    db.add(message)
    conv.last_message_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(message)
    payload = {
        "type": "im.message",
        "conversation_id": conv.id,
        "message": {
            "id": message.id,
            "sender_id": message.sender_id,
            "kind": message.kind,
            "content": message.content,
            "status": message.status,
            "created_time": message.created_time.isoformat(),
        },
    }
    await manager.broadcast(f"conv:{conv.id}", payload)
    await manager.broadcast(f"user:{conv.user_a}", {"type": "im.conv_update", "conversation_id": conv.id})
    await manager.broadcast(f"user:{conv.user_b}", {"type": "im.conv_update", "conversation_id": conv.id})
    return message


async def send_bot_dm(db: AsyncSession, bot: User, target_uid: str, content: str) -> DmMessage:
    """机器人定向私信"""
    conv = await get_or_create_dm(db, bot.uid, target_uid)
    return await send_dm(db, conv, bot.uid, content)


async def broadcast_bot(db: AsyncSession, bot: User, content: str) -> int:
    """机器人全量广播：向所有活跃非机器人用户发送私信，返回发送人数"""
    rows = await db.execute(
        select(User.uid).where(User.is_active.is_(True), User.is_bot.is_(False))
    )
    uids = [r for (r,) in rows.all()]
    for uid in uids:
        await send_bot_dm(db, bot, uid, content)
    return len(uids)
