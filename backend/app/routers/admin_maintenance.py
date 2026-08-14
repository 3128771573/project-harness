"""Admin：企业级维护模式控制（状态/开启/关闭/延长/定时/紧急令牌/操作记录）"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..deps import get_current_user, require_roles
from ..models import AuditLog, User
from ..schemas import (
    MaintenanceEnableIn,
    MaintenanceExtendIn,
    MaintenanceScheduleIn,
    MaintenanceStatusOut,
)
from ..security import ROLE_SUPER_ADMIN
from ..services import maintenance as maint
from ..services.audit import record_audit
from ..services.notify import notify_admins

router = APIRouter(prefix="/admin/maintenance", tags=["admin-maintenance"])

require_super = require_roles(ROLE_SUPER_ADMIN)


def _status_payload(snap: dict) -> MaintenanceStatusOut:
    return MaintenanceStatusOut(
        mode=snap["mode"],
        reason=snap["reason"],
        operator=snap["operator"],
        start_at=snap["start_at"],
        auto_close_at=snap["auto_close_at"],
        max_duration_minutes=snap["max_duration_minutes"],
        remaining_seconds=_remaining(snap["auto_close_at"]),
        emergency_configured=bool(snap["emergency_token_hash"]),
        scheduled_enabled=snap["scheduled_enabled"],
        scheduled_time=snap["scheduled_time"],
        scheduled_duration=snap["scheduled_duration"],
        scheduled_days=snap["scheduled_days"],
    )


def _remaining(auto_close_at: str) -> int:
    if not auto_close_at:
        return 0
    try:
        t = datetime.fromisoformat(auto_close_at)
        return max(0, int((t - datetime.now(timezone.utc)).total_seconds()))
    except ValueError:
        return 0


@router.get("/status", response_model=MaintenanceStatusOut, summary="当前维护状态")
async def get_status(
    current_user: User = Depends(require_super),
    db: AsyncSession = Depends(get_db),
):
    return _status_payload(await maint.snapshot(db))


@router.post("/enable", response_model=MaintenanceStatusOut, summary="开启维护模式")
async def enable_maintenance(
    payload: MaintenanceEnableIn,
    current_user: User = Depends(require_super),
    db: AsyncSession = Depends(get_db),
):
    result = await maint.enable(
        db, mode=payload.mode, reason=payload.reason,
        duration_minutes=payload.duration_minutes, by=current_user.username,
    )
    await record_audit(
        db, actor=current_user, action="maintenance.enable",
        detail=f"mode={payload.mode} reason={payload.reason} duration={payload.duration_minutes or '手动'}",
    )
    snap = await maint.snapshot(db)
    await notify_admins(db, action="enable", snap=snap)
    return _status_payload(snap)


@router.post("/disable", response_model=MaintenanceStatusOut, summary="关闭维护模式")
async def disable_maintenance(
    current_user: User = Depends(require_super),
    db: AsyncSession = Depends(get_db),
):
    snap_before = await maint.snapshot(db)
    await maint.disable(db, by=current_user.username)
    await record_audit(db, actor=current_user, action="maintenance.disable", detail=f"关闭维护（原模式 {snap_before['mode']}）")
    await notify_admins(db, action="disable", snap=snap_before)
    return _status_payload(await maint.snapshot(db))


@router.post("/extend", response_model=MaintenanceStatusOut, summary="延长维护时间")
async def extend_maintenance(
    payload: MaintenanceExtendIn,
    current_user: User = Depends(require_super),
    db: AsyncSession = Depends(get_db),
):
    await maint.extend(db, minutes=payload.minutes, by=current_user.username)
    await record_audit(db, actor=current_user, action="maintenance.extend", detail=f"延长 {payload.minutes} 分钟")
    snap = await maint.snapshot(db)
    await notify_admins(db, action="extend", snap=snap)
    return _status_payload(snap)


@router.post("/schedule", response_model=MaintenanceStatusOut, summary="设置定时维护计划")
async def schedule_maintenance(
    payload: MaintenanceScheduleIn,
    current_user: User = Depends(require_super),
    db: AsyncSession = Depends(get_db),
):
    await maint._set(db, "scheduled_enabled", "true" if payload.enabled else "false", current_user.username)
    await maint._set(db, "scheduled_time", payload.time or "03:00", current_user.username)
    await maint._set(db, "scheduled_duration", str(payload.duration or 60), current_user.username)
    await maint._set(db, "scheduled_days", ",".join(str(d) for d in (payload.days or [])), current_user.username)
    maint.invalidate()
    await record_audit(
        db, actor=current_user, action="maintenance.schedule",
        detail=f"enabled={payload.enabled} time={payload.time} duration={payload.duration} days={payload.days}",
    )
    return _status_payload(await maint.snapshot(db))


# ---------- 紧急令牌 ----------

@router.post("/regenerate-token", summary="重新生成紧急令牌（旧令牌立即失效；明文仅显示一次）")
async def regenerate_token(
    current_user: User = Depends(require_super),
    db: AsyncSession = Depends(get_db),
):
    token, token_hash = maint.generate_token()
    await maint._set(db, "emergency_token_hash", token_hash, current_user.username)
    maint.invalidate()
    await record_audit(db, actor=current_user, action="maintenance.token_regenerate", detail="紧急令牌已重新生成")
    return {"token": token, "note": "请立即保存，明文仅显示这一次"}


@router.get("/emergency-close", summary="紧急关闭（URL 携带令牌，无需登录）")
async def emergency_close(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    snap = await maint.snapshot(db)
    if not maint.verify_token(token, snap["emergency_token_hash"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="紧急令牌无效")
    await maint.disable(db, by="emergency_token")
    await record_audit(
        db, actor=None, action="maintenance.emergency_close",
        detail=f"通过紧急令牌关闭（原模式 {snap['mode']}）",
    )
    await notify_admins(db, action="emergency_close", snap=snap)
    return {"ok": True, "message": "维护模式已通过紧急令牌关闭"}


# ---------- 操作记录 ----------

@router.get("/history", summary="维护操作记录（审计）")
async def maintenance_history(
    limit: int = Query(default=30, ge=1, le=100),
    current_user: User = Depends(require_super),
    db: AsyncSession = Depends(get_db),
):
    rows = (
        await db.execute(
            select(AuditLog)
            .where(AuditLog.action.like("maintenance.%"))
            .order_by(AuditLog.created_time.desc())
            .limit(limit)
        )
    ).scalars().all()
    return [
        {
            "id": r.id,
            "time_utc": r.created_time.isoformat() if r.created_time else None,
            "operator": r.actor_name or "system",
            "action": r.action,
            "detail": r.detail or "",
            "ip": r.ip or "",
        }
        for r in rows
    ]
