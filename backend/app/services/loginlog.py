"""登录日志记录工具"""
import asyncio
import re
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from ..database import SessionLocal
from ..models import LoginLog, User

# 后台任务引用集：防止 asyncio 任务被 GC 中断
_TASKS: set[asyncio.Task] = set()


def _parse_device(user_agent: str | None) -> str:
    """识别设备：设备类型 · 操作系统 · 浏览器（含版本），识别不出写「未知」"""
    if not user_agent:
        return "未知设备"
    ua = user_agent.lower()

    # 爬虫/工具
    if any(k in ua for k in ("bot", "spider", "crawler", "slurp", "bingpreview", "petalbot", "mediapartners", "googlebot")):
        return "爬虫/机器人"

    # 设备类型
    if "ipad" in ua or "tablet" in ua:
        device = "平板"
    elif "iphone" in ua or "ipod" in ua:
        device = "iPhone"
    elif "android" in ua and "mobile" in ua:
        device = "安卓手机"
    elif "android" in ua:
        device = "安卓平板/安卓设备"
    elif "mobile" in ua or "opera mini" in ua:
        device = "移动端"
    elif "windows phone" in ua:
        device = "Windows Phone"
    else:
        device = "桌面端"

    # 操作系统（注意：部分 UA 是 "Windows NT; U; ..." 无版本号，需 None 保护）
    if "windows nt" in ua:
        m = re.search(r"windows nt ([d.]+)", ua)
        ver = {"10.0": "10", "6.3": "8.1", "6.2": "8", "6.1": "7"}.get(m.group(1), "") if m else ""
        os_name = f"Windows{ver}" if ver else "Windows"
    elif "mac os x" in ua or "macintosh" in ua:
        os_name = "macOS"
    elif "android" in ua:
        os_name = "Android"
    elif "iphone" in ua or "ipad" in ua or "ipod" in ua:
        os_name = "iOS"
    elif "linux" in ua or "x11" in ua:
        os_name = "Linux"
    elif "windows phone" in ua:
        os_name = "Windows Phone"
    else:
        os_name = "未知系统"

    # 浏览器（带主版本号）
    browser = "其他"
    if "micromessenger" in ua:
        browser = "微信"
    elif "edg/" in ua:
        m = re.search(r"edg/(d+)", ua)
        browser = f"Edge {m.group(1)}" if m else "Edge"
    elif "chrome/" in ua:
        m = re.search(r"chrome/(d+)", ua)
        browser = f"Chrome {m.group(1)}" if m else "Chrome"
    elif "firefox/" in ua:
        m = re.search(r"firefox/(d+)", ua)
        browser = f"Firefox {m.group(1)}" if m else "Firefox"
    elif "safari/" in ua:
        m = re.search(r"safari/(d+)", ua)
        browser = f"Safari {m.group(1)}" if m else "Safari"
    elif "opera" in ua or "opr/" in ua:
        browser = "Opera"

    return f"{device} · {os_name} · {browser}"


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
    row = LoginLog(
        uid=uid,
        email=email,
        ip=ip,
        ip_location="未知",
        user_agent=user_agent,
        device=_parse_device(user_agent),
        success=success,
        reason=reason,
    )
    db.add(row)
    await db.commit()
    schedule_login_location(row.id, ip)


def schedule_login_location(log_id: str, ip: str | None):
    """后台异步补充登录日志 IP 属地"""

    async def _run():
        await asyncio.sleep(0.5)
        from .geo import resolve_location

        loc = await resolve_location(ip)
        if loc == "未知":
            return
        try:
            async with SessionLocal() as s:
                row = await s.get(LoginLog, log_id)
                if row is not None:
                    row.ip_location = loc
                    await s.commit()
        except Exception:
            pass

    task = asyncio.create_task(_run())
    _TASKS.add(task)
    task.add_done_callback(_TASKS.discard)


async def update_last_login(db: AsyncSession, user: User, ip: str | None):
    user.last_login_time = datetime.now(timezone.utc)
    user.last_login_ip = ip
    await db.commit()
