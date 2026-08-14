"""匿名留言板：图形验证码 / 提交留言 / 查询回复 / 管理员管理（含 IP 限流）"""
import secrets
import time
from collections import deque
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import or_

from ..database import get_db
from ..deps import require_roles
from ..models import GuestbookReply, GuestbookTemplate, Message, User
from ..schemas import (
    GuestbookReplyIn,
    GuestbookReplyOut,
    GuestbookTemplateIn,
    GuestbookTemplateOut,
    GuestbookTimelineOut,
    GuestbookVisitorReplyIn,
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


async def _gen_archive_no(db: AsyncSession) -> str:
    """生成档案号 GB-YYYYMMDD-NNN（当日序号，唯一索引防并发）"""
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"GB-{day}-"
    for _ in range(5):
        seq = (
            await db.execute(
                select(func.count()).select_from(Message).where(Message.archive_no.like(prefix + "%"))
            )
        ).scalar_one()
        no = f"{prefix}{seq + 1:03d}"
        exists = (
            await db.execute(select(Message.id).where(Message.archive_no == no))
        ).scalar_one_or_none()
        if not exists:
            return no
    return f"{prefix}{secrets.randbelow(900) + 100:03d}"


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
        archive_no=await _gen_archive_no(db),
        ip=ip,
        user_agent=(request.headers.get("user-agent") or "")[:255],
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return MessageSubmitOut(msg="success", query_code=code, archive_no=msg.archive_no)


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
    if not q:
        # 清理空队列，避免 IP 集合无限增长
        _query_log.pop(ip, None)
        q = deque()
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

    replies = (
        await db.execute(
            select(GuestbookReply)
            .where(GuestbookReply.guestbook_id == msg.id)
            .order_by(GuestbookReply.created_time.asc())
        )
    ).scalars().all()
    return MessageQueryOut(
        data={
            "archive_no": msg.archive_no,
            "nickname": msg.nickname,
            "content": msg.content,
            "created_at": msg.created_time.isoformat() if msg.created_time else None,
            "status": msg.status,
            "reply": msg.reply,
            "replied_at": msg.replied_at.isoformat() if msg.replied_at else None,
            "replies": [
                {
                    "id": r.id,
                    "sender_type": r.sender_type,
                    "sender_name": r.sender_name,
                    "content": r.content,
                    "created_time": r.created_time.isoformat() if r.created_time else None,
                }
                for r in replies
            ],
        }
    )


@router.post("/query/reply", response_model=MessageQueryOut, summary="访客凭查询码追加追问")
async def visitor_reply(
    payload: GuestbookVisitorReplyIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """访客追问：写入时间线（sender_type=visitor），留言状态回到待回复"""
    code = payload.query_code.strip().upper()
    msg = (await db.execute(select(Message).where(Message.query_code == code))).scalar_one_or_none()
    if msg is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="查询码或邮箱错误")
    if msg.email:
        if not payload.email or msg.email.lower() != payload.email.strip().lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="查询码或邮箱错误")
    if msg.status == "closed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该留言已关闭，无法继续追问")
    db.add(
        GuestbookReply(
            guestbook_id=msg.id,
            sender_type="visitor",
            sender_name=msg.nickname or "访客",
            content=payload.content,
        )
    )
    msg.status = "pending"
    msg.is_read = False
    await db.commit()
    # 返回最新时间线
    replies = (
        await db.execute(
            select(GuestbookReply)
            .where(GuestbookReply.guestbook_id == msg.id)
            .order_by(GuestbookReply.created_time.asc())
        )
    ).scalars().all()
    return MessageQueryOut(
        data={
            "archive_no": msg.archive_no,
            "nickname": msg.nickname,
            "content": msg.content,
            "created_at": msg.created_time.isoformat() if msg.created_time else None,
            "status": msg.status,
            "replies": [
                {
                    "id": r.id,
                    "sender_type": r.sender_type,
                    "sender_name": r.sender_name,
                    "content": r.content,
                    "created_time": r.created_time.isoformat() if r.created_time else None,
                }
                for r in replies
            ],
        }
    )


# ---------- 管理员：列表 / 已读 / 回复 / 删除 / 配置 ----------


@router.get("/admin/messages", response_model=MessageAdminList, summary="留言列表（分页 + 统计 + 筛选）")
async def admin_messages(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    status_filter: str | None = Query(default=None, description="pending / replied / closed"),
    keyword: str | None = Query(default=None, description="按内容/昵称/档案号/查询码模糊搜索"),
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
        await db.execute(select(func.count()).select_from(Message).where(Message.status == "pending"))
    ).scalar_one()
    q = select(Message)
    if status_filter:
        q = q.where(Message.status == status_filter)
    if keyword:
        kw = keyword.strip()
        q = q.where(
            or_(
                Message.content.contains(kw, autoescape=True),
                Message.nickname.contains(kw, autoescape=True),
                Message.archive_no.contains(kw, autoescape=True),
                Message.query_code.contains(kw, autoescape=True),
            )
        )
    result = await db.execute(
        q.order_by(Message.created_time.desc()).limit(page_size).offset((page - 1) * page_size)
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


@router.get("/admin/messages/{mid}/replies", response_model=list[GuestbookReplyOut], summary="留言往来时间线")
async def admin_timeline(
    mid: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    msg = await db.get(Message, mid)
    if msg is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="留言不存在")
    replies = (
        await db.execute(
            select(GuestbookReply)
            .where(GuestbookReply.guestbook_id == mid)
            .order_by(GuestbookReply.created_time.asc())
        )
    ).scalars().all()
    return [GuestbookReplyOut.model_validate(r) for r in replies]


@router.put("/admin/messages/{mid}/reply", summary="回复留言（写入时间线 + 可选邮件通知）")
async def admin_reply(
    mid: str,
    payload: MessageReplyIn,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    import asyncio

    from ..services.mailer import send_email

    msg = await db.get(Message, mid)
    if msg is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="留言不存在")
    if msg.status == "closed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该留言已关闭，请先重新打开")
    now = datetime.now(timezone.utc)
    db.add(
        GuestbookReply(
            guestbook_id=msg.id,
            sender_type="admin",
            sender_name=current_user.username,
            content=payload.reply,
        )
    )
    msg.reply = payload.reply
    msg.replied_at = now
    msg.status = "replied"
    msg.is_read = True
    await db.commit()
    # 邮件通知（SMTP 未配置时静默跳过）
    if msg.email:
        try:
            await asyncio.to_thread(
                send_email,
                msg.email,
                f"【Harness】您的留言 {msg.archive_no or ''} 已回复",
                f"<p>您好，{msg.nickname or '访客'}：</p>"
                f"<p>您于 {msg.created_time.strftime('%Y-%m-%d %H:%M') if msg.created_time else ''} 提交的留言（档案号 <b>{msg.archive_no or ''}</b>）已收到回复：</p>"
                f"<blockquote>{payload.reply.replace(chr(10), '<br>')}</blockquote>"
                f"<p>您可凭查询码 <b>{msg.query_code}</b> 在留言板继续查看与追问。</p>",
            )
        except Exception:
            pass
    from ..services.audit import record_audit

    await record_audit(db, actor=current_user, action="guestbook.reply", resource=f"message:{mid}", detail=f"回复留言 {msg.archive_no}")
    return {"code": 0, "msg": "ok"}


@router.post("/admin/messages/{mid}/close", summary="关闭留言（不再接受追问）")
async def admin_close(
    mid: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    msg = await db.get(Message, mid)
    if msg is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="留言不存在")
    msg.status = "closed"
    await db.commit()
    return {"code": 0, "msg": "ok"}


@router.post("/admin/messages/{mid}/reopen", summary="重新打开留言")
async def admin_reopen(
    mid: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    msg = await db.get(Message, mid)
    if msg is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="留言不存在")
    msg.status = "pending"
    await db.commit()
    return {"code": 0, "msg": "ok"}


# ---------- 快捷回复模板 ----------


@router.get("/admin/messages/templates", response_model=list[GuestbookTemplateOut], summary="回复模板列表")
async def list_templates(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    rows = (
        await db.execute(select(GuestbookTemplate).order_by(GuestbookTemplate.created_time.asc()))
    ).scalars().all()
    return [GuestbookTemplateOut.model_validate(t) for t in rows]


@router.post("/admin/messages/templates", response_model=GuestbookTemplateOut, status_code=status.HTTP_201_CREATED, summary="新增回复模板")
async def create_template(
    payload: GuestbookTemplateIn,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    t = GuestbookTemplate(name=payload.name, content=payload.content)
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return GuestbookTemplateOut.model_validate(t)


@router.delete("/admin/messages/templates/{tid}", status_code=status.HTTP_204_NO_CONTENT, summary="删除回复模板")
async def delete_template(
    tid: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    t = await db.get(GuestbookTemplate, tid)
    if t is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模板不存在")
    await db.delete(t)
    await db.commit()
    return None


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
