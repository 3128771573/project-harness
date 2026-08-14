"""访客访问记录服务"""
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import VisitLog
from .loginlog import _parse_device


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
):
    """记录一次访问"""
    db.add(
        VisitLog(
            id=str(uuid.uuid4()),
            path=path[:255],
            method=method[:10] if method else None,
            ip=ip,
            user_agent=user_agent[:512] if user_agent else None,
            device=_parse_device(user_agent),
            uid=uid,
            referer=referer[:512] if referer else None,
            status_code=status_code,
        )
    )
