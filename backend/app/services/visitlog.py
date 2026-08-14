"""访客访问记录服务"""
import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import SessionLocal
from ..models import VisitLog
from .geo import resolve_location
from .loginlog import _parse_device

# 同 IP + 同路径 + 同用户 去重窗口（秒）：刷新/重复点击不再重复计数
DEDUP_WINDOW = 60


async def _recent_visit(db: AsyncSession, *, ip: str | None, path: str, uid: str | None) -> bool:
    """窗口内是否已有同 IP 同路径的页面访问记录"""
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=DEDUP_WINDOW)
    stmt = select(VisitLog.id).where(
        VisitLog.path == path,
        VisitLog.created_time >= cutoff,
    )
    if ip:
        stmt = stmt.where(VisitLog.ip == ip)
    if uid:
        stmt = stmt.where(VisitLog.uid == uid)
    else:
        stmt = stmt.where(VisitLog.uid.is_(None))
    row = await db.execute(stmt.limit(1))
    return row.scalar_one_or_none() is not None


def parse_client(request) -> tuple[str | None, str | None]:
    """提取客户端 IP 和 User-Agent"""
    ip = None
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        ip = fwd.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return ip, ua


async def record_visit(
    db: AsyncSession,
    *,
    path: str,
    method: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
    uid: str | None = None,
    referer: str | None = None,
    status_code: int | None = None,
) -> VisitLog | None:
    """记录一次页面访问。窗口内重复（刷新/重复点击）跳过；返回行供属地异步补充。"""
    # 只统计页面访问（PAGE）
    if method != "PAGE":
        return None
    # 去重：窗口内同 IP 同路径不重复记录
    if await _recent_visit(db, ip=ip, path=path, uid=uid):
        return None
    row = VisitLog(
        id=str(uuid.uuid4()),
        path=path[:255],
        method=method[:10] if method else None,
        ip=ip,
        ip_location="未知",
        user_agent=user_agent[:512] if user_agent else None,
        device=_parse_device(user_agent),
        uid=uid,
        referer=referer[:512] if referer else None,
        status_code=status_code,
    )
    db.add(row)
    return row


def schedule_location_lookup(visit_id: str, ip: str | None):
    """后台异步补充 IP 属地（不阻塞请求；查询失败保持「未知」）"""

    async def _run():
        await asyncio.sleep(0.5)  # 等调用方 commit 完成
        loc = await resolve_location(ip)
        if loc == "未知":
            return
        try:
            async with SessionLocal() as s:
                row = await s.get(VisitLog, visit_id)
                if row is not None:
                    row.ip_location = loc
                    await s.commit()
        except Exception:
            pass

    asyncio.create_task(_run())
