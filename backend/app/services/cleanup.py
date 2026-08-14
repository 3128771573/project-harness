"""过期数据清理任务：启动时执行一次，之后每 24 小时执行"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, or_

from ..database import SessionLocal
from ..models import AiHistory, DeviceTelemetry, EmailCode, LoginLog, RefreshToken, VisitLog

logger = logging.getLogger("cleanup")
_INTERVAL = 24 * 3600


async def cleanup_expired() -> dict:
    """按保留策略批量删除过期数据，返回各表删除行数"""
    now = datetime.now(timezone.utc)
    stats: dict[str, int] = {}

    async with SessionLocal() as db:
        # refresh_tokens：已吊销或已过期，且创建超过 90 天
        stats["refresh_tokens"] = (
            await db.execute(
                delete(RefreshToken).where(
                    or_(RefreshToken.revoked.is_(True), RefreshToken.expires_at < now),
                    RefreshToken.created_time < now - timedelta(days=90),
                )
            )
        ).rowcount or 0

        # email_codes：7 天
        stats["email_codes"] = (
            await db.execute(
                delete(EmailCode).where(EmailCode.created_time < now - timedelta(days=7))
            )
        ).rowcount or 0

        # visit_logs：365 天
        stats["visit_logs"] = (
            await db.execute(
                delete(VisitLog).where(VisitLog.created_time < now - timedelta(days=365))
            )
        ).rowcount or 0

        # login_logs：365 天
        stats["login_logs"] = (
            await db.execute(
                delete(LoginLog).where(LoginLog.created_time < now - timedelta(days=365))
            )
        ).rowcount or 0

        # device_telemetry：90 天（前端只展示最近 120 条）
        stats["device_telemetry"] = (
            await db.execute(
                delete(DeviceTelemetry).where(DeviceTelemetry.created_time < now - timedelta(days=90))
            )
        ).rowcount or 0

        # ai_history：365 天（会话本身保留，历史问答按年清理）
        stats["ai_history"] = (
            await db.execute(
                delete(AiHistory).where(AiHistory.created_time < now - timedelta(days=365))
            )
        ).rowcount or 0

        await db.commit()

    return stats


async def cleanup_loop() -> None:
    """常驻任务：启动清理一次，之后每 24h 清理一次"""
    while True:
        try:
            stats = await cleanup_expired()
            logger.info("过期数据清理完成: %s", stats)
        except Exception:
            logger.exception("过期数据清理失败")
        await asyncio.sleep(_INTERVAL)
