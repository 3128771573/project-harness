"""审计日志记录"""
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AuditLog, User


async def record_audit(
    db: AsyncSession,
    *,
    actor: User | None,
    action: str,
    resource: str | None = None,
    target_uid: str | None = None,
    detail: str | None = None,
    ip: str | None = None,
    success: bool = True,
):
    db.add(
        AuditLog(
            actor_uid=actor.uid if actor else None,
            actor_name=actor.username if actor else "system",
            action=action,
            resource=resource,
            target_uid=target_uid,
            detail=detail,
            ip=ip,
            success=success,
        )
    )
    await db.commit()
