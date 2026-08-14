"""匿名留言板：图形验证码 / 提交留言 / 查询回复 / 管理员管理（含 IP 限流）"""
import secrets
import time
from collections import deque
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..deps import require_roles
from ..models import Message, User
from ..schemas import (
    MessageAdminList,
    MessageAdminOut,
    MessageConfigIn,
    MessageConfigOut,
    MessageCreate,
    MessageQueryIn,
    MessageQueryOut,
    MessageReplyIn,
    MessageSubmitOut,
)
from ..security import ROLE_ADMIN, ROLE_SUPER_ADMIN
from ..services import settings as settings_svc
from ..services.captcha import create_captcha, verify_captcha

router = APIRouter(tags=["guestbook"])
require_admin = require_roles(ROLE_ADMIN, ROLE_SUPER_ADMIN)

# 查询接口限速：ip -> 近 60 秒时间戳队列（内存版，单实例部署适用）
_query_log: dict[str, deque] = {}

# 查询码字符集（去易混淆字符）
CODE_CHARSET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

SETTING_DAILY = "guestbook.daily_limit"
SETTING_TTL = "guestbook.captcha_ttl"
SETTING_RATE = "guestbook.query_rate"


class ReadIn(BaseModel):
    is_read: bool = True


def _client_ip(request: Request) -> str | None:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else None


def _gen_query_code() -> str:
    return "MSG-" + "".join(secrets.choice(CODE_CHARSET) for _ in range(8))


async def _cfg(db: AsyncSession) -> tuple[int, int, int]:
    daily_raw = await settings_svc.get_setting(db, SETTING_DAILY, default="3")
    ttl_raw = await settings_svc.get_setting(db, SETTING_TTL, default="120")
    rate_raw = await settings_svc.get_setting(db, SETTING_RATE, default="5")
    try:
        daily = int(daily_raw)
    except (TypeError, ValueError):
        daily = 3
    try:
        ttl = int(ttl_raw)
    except (TypeError, ValueError):
        ttl = 120
    try:
        rate = int(rate_raw)
    except (TypeError, ValueError):
        rate = 5
    return daily, ttl, rate


# ---------- 公开：验证码 / 提交 / 查询 ----------


@router.get("/captcha", summary="获取图形验证码（image/png，Cookie 关联，点击刷新）")
async def get_captcha(db: AsyncSession = Depends(get_db)):
    _, ttl, _ = await _cfg(db)
    captcha_id, png = create_captcha(ttl=ttl)
    # 注意：必须在同一个 Response 对象上设置 Cookie 与返回内容
    resp = Response(content=png, media_type="image/png")
    resp.set_cookie("captcha_id", captcha_id, max_age=ttl, path="/", httponly=False, samesite="lax")
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return resp


@router.post("/messages", response_model=MessageSubmitOut, summary="提交留言")
async def submit_message(
    payload: MessageCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    daily, _, _ = await _cfg(db)

    # 图形验证码（单次有效，无论成败）
    captcha_id = request.cookies.get("captcha_id")
    if not verify_captcha(captcha_id, payload.captcha):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码错误或已过期")

    # IP 限流：24 小时内最多 daily 次
    ip = _client_ip(request)
    if ip:
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        cnt = (
            await db.execute(
                select(func.count()).select_from(Message).where(
                    Message.ip == ip, Message.created_time >= since
                )
            )
        ).scalar_one()
        if cnt >= daily:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="您今日提交次数已达上限，请 24 小时后再试",
            )

    # 生成唯一查询码（先查重，避免唯一索引冲突）
    for _ in range(5):
        code = _gen_query_code()
        exists = (
            await db.execute(select(Message.id).where(Message.query_code == code))
        ).scalar_one_or_none()
        if not exists:
            break
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="查询码生成失败")

    msg = Message(
        nickname=payload.nickname,
        email=payload.email,
        content=payload.content,
        query_code=code,
        ip=ip,
        user_agent=(request.headers.get("user-agent") or "")[:255],
    )
    db.add(msg)
    await db.commit()
    return MessageSubmitOut(msg="success", query_code=code)


@router.post("/query", response_model=MessageQueryOut, summary="凭查询码查询留言与回复")
async def query_message(
    payload: MessageQueryIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    _, _, rate = await _cfg(db)

    # 查询限速：同 IP 每分钟 rate 次
    ip = _client_ip(request) or "unknown"
    now_ts = time.time()
    q = _query_log.setdefault(ip, deque())
    while q and q[0] < now_ts - 60:
        q.popleft()
    if len(q) >= rate:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="查询过于频繁，请一分钟后再试"
        )
    q.append(now_ts)

    code = payload.query_code.strip().upper()
    msg = (await db.execute(select(Message).where(Message.query_code == code))).scalar_one_or_none()
    if msg is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="查询码或邮箱错误")
    if msg.email:
        if not payload.email or msg.email.lower() != payload.email.strip().lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="查询码或邮箱错误")

    return MessageQueryOut(
        data={
            "nickname": msg.nickname,
            "content": msg.content,
            "created_at": msg.created_time.isoformat() if msg.created_time else None,
            "reply": msg.reply,
            "replied_at": msg.replied_at.isoformat() if msg.replied_at else None,
        }
    )


# ---------- 管理员：列表 / 已读 / 回复 / 删除 / 配置 ----------


@router.get("/admin/messages", response_model=MessageAdminList, summary="留言列表（分页 + 统计）")
async def admin_messages(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    total = (await db.execute(select(func.count()).select_from(Message))).scalar_one()
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today = (
        await db.execute(
            select(func.count()).select_from(Message).where(Message.created_time >= today_start)
        )
    ).scalar_one()
    pending = (
        await db.execute(select(func.count()).select_from(Message).where(Message.reply.is_(None)))
    ).scalar_one()
    result = await db.execute(
        select(Message).order_by(Message.created_time.desc()).limit(page_size).offset((page - 1) * page_size)
    )
    items = [MessageAdminOut.model_validate(m) for m in result.scalars().all()]
    return MessageAdminList(
        items=items,
        total=total,
        stats={"total": total, "today": today, "pending": pending},
    )


@router.put("/admin/messages/{mid}/read", summary="标记已读/未读")
async def admin_toggle_read(
    mid: str,
    payload: ReadIn,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    msg = await db.get(Message, mid)
    if msg is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="留言不存在")
    msg.is_read = payload.is_read
    await db.commit()
    return {"code": 0, "msg": "ok"}


@router.put("/admin/messages/{mid}/reply", summary="回复留言")
async def admin_reply(
    mid: str,
    payload: MessageReplyIn,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    msg = await db.get(Message, mid)
    if msg is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="留言不存在")
    msg.reply = payload.reply
    msg.replied_at = datetime.now(timezone.utc)
    msg.is_read = True
    await db.commit()
    return {"code": 0, "msg": "ok"}


@router.delete("/admin/messages/{mid}", status_code=status.HTTP_204_NO_CONTENT, summary="删除留言")
async def admin_delete_message(
    mid: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    msg = await db.get(Message, mid)
    if msg is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="留言不存在")
    await db.delete(msg)
    await db.commit()


@router.get("/admin/messages/config", response_model=MessageConfigOut, summary="留言板配置")
async def get_config(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    daily, ttl, rate = await _cfg(db)
    return MessageConfigOut(daily_limit=daily, captcha_ttl=ttl, query_rate=rate)


@router.put("/admin/messages/config", response_model=MessageConfigOut, summary="更新留言板配置")
async def update_config(
    payload: MessageConfigIn,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await settings_svc.set_setting(db, SETTING_DAILY, str(payload.daily_limit))
    await settings_svc.set_setting(db, SETTING_TTL, str(payload.captcha_ttl))
    await settings_svc.set_setting(db, SETTING_RATE, str(payload.query_rate))
    return MessageConfigOut(
        daily_limit=payload.daily_limit, captcha_ttl=payload.captcha_ttl, query_rate=payload.query_rate
    )
