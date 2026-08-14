"""登录日志记录工具"""
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import LoginLog, User


def _parse_device(user_agent: str | None) -> str:
    if not user_agent:
        return "未知设备"
    ua = user_agent.lower()
    if "mobile" in ua or "android" in ua or "iphone" in ua:
        device = "移动端"
    else:
        device = "电脑"
    if "windows" in ua:
        device += " Windows"
    elif "mac os" in ua or "macintosh" in ua:
        device += " macOS"
    elif "linux" in ua:
        device += " Linux"
    elif "android" in ua:
        device += " Android"
    elif "iphone" in ua or "ios" in ua:
        device += " iOS"
    browser = "Chrome" if "chrome" in ua and "edg" not in ua else "Edge" if "edg" in ua else "Firefox" if "firefox" in ua else "Safari" if "safari" in ua else "其他"
    return f"{device} · {browser}"


async def record_login(
    db: AsyncSession,
    *,
    email: str | None = None,
    uid: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
    success: bool,
    reason: str | None = None,
):
    db.add(
        LoginLog(
            uid=uid,
            email=email,
            ip=ip,
            user_agent=user_agent,
            device=_parse_device(user_agent),
            success=success,
            reason=reason,
        )
    )
    await db.commit()


async def update_last_login(db: AsyncSession, user: User, ip: str | None):
    user.last_login_time = datetime.now(timezone.utc)
    user.last_login_ip = ip
    await db.commit()
