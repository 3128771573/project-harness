"""Admin：企业级日志导出（superadmin 专属）

- count：行数预览（超 10 万行提示缩小范围）
- run：导出 CSV/JSON（UTF-8 BOM），返回文件流 + X-Export-SHA256 完整性头
- history：导出操作历史（源于 audit_logs，导出行为本身可审计）
"""
import json
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..deps import get_current_user, require_roles
from ..models import AuditLog, User
from ..schemas import ExportCountOut, ExportHistoryItem, ExportQueryIn
from ..security import ROLE_SUPER_ADMIN
from ..services.audit import record_audit
from ..services.exporter import MAX_ROWS, SOURCE_LABELS, ExportError, query_source, render_csv, render_json, validate_range

router = APIRouter(prefix="/admin/exports", tags=["admin-exports"])

require_super = require_roles(ROLE_SUPER_ADMIN)

# 限流：每人每分钟最多 6 次导出
_RUN_LOG: dict[str, list[float]] = {}


def _check_rate(uid: str):
    now = time.time()
    recent = [t for t in _RUN_LOG.get(uid, []) if now - t < 60]
    if len(recent) >= 6:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="导出过于频繁，请稍后再试")
    recent.append(now)
    _RUN_LOG[uid] = recent


def _filters(p: ExportQueryIn) -> dict:
    return {
        "action": p.action, "actor": p.actor, "keyword": p.keyword, "success": p.success,
        "email": p.email, "method": p.method, "path": p.path, "username": p.username,
        "status_code": p.status_code, "actor_uid": p.actor_uid, "kind": p.kind,
        "status": p.status, "target_type": p.target_type, "to": p.to,
    }


@router.post("/count", response_model=ExportCountOut, summary="行数预览")
async def export_count(
    payload: ExportQueryIn,
    current_user: User = Depends(require_super),
    db: AsyncSession = Depends(get_db),
):
    try:
        validate_range(payload.start, payload.end)
        _, rows = await query_source(db, payload.source, payload.start, payload.end, _filters(payload))
    except ExportError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    capped = len(rows) >= MAX_ROWS
    return ExportCountOut(count=len(rows), capped=capped, max_rows=MAX_ROWS)


@router.post("/run", summary="导出文件（CSV/JSON + SHA-256 完整性头）")
async def export_run(
    payload: ExportQueryIn,
    current_user: User = Depends(require_super),
    db: AsyncSession = Depends(get_db),
):
    _check_rate(current_user.uid)
    try:
        validate_range(payload.start, payload.end)
        columns, rows = await query_source(db, payload.source, payload.start, payload.end, _filters(payload))
    except ExportError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if len(rows) >= MAX_ROWS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"结果超过 {MAX_ROWS} 行上限，请缩小时间范围或增加筛选条件")
    if payload.format == "json":
        data, digest = render_json(payload.source, payload.start.isoformat(), payload.end.isoformat(), columns, rows)
        media = "application/json; charset=utf-8"
        ext = "json"
    else:
        data, digest = render_csv(columns, rows)
        media = "text/csv; charset=utf-8"
        ext = "csv"
    now = datetime.now(timezone.utc)
    filename = f"harness-{payload.source}-{now.strftime('%Y%m%d-%H%M%S')}.{ext}"
    # 导出行为本身写入审计（谁、何时、什么范围、多少行、哈希）
    await record_audit(
        db, actor=current_user, action="audit.export",
        detail=json.dumps({
            "source": payload.source, "start": payload.start.isoformat(), "end": payload.end.isoformat(),
            "fmt": payload.format, "rows": len(rows), "sha256": digest, "filename": filename,
        }, ensure_ascii=False),
    )
    return Response(
        content=data,
        media_type=media,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Export-SHA256": digest,
            "X-Export-Rows": str(len(rows)),
            "X-Export-Source": payload.source,  # 英文标识（HTTP 头须 latin-1），前端映射中文
        },
    )


@router.get("/history", response_model=list[ExportHistoryItem], summary="最近导出记录")
async def export_history(
    limit: int = Query(default=30, ge=1, le=100),
    current_user: User = Depends(require_super),
    db: AsyncSession = Depends(get_db),
):
    rows = (
        await db.execute(
            select(AuditLog).where(AuditLog.action == "audit.export").order_by(AuditLog.created_time.desc()).limit(limit)
        )
    ).scalars().all()
    items = []
    for r in rows:
        meta = {}
        try:
            meta = json.loads(r.detail or "{}")
        except json.JSONDecodeError:
            pass
        items.append(
            ExportHistoryItem(
                id=r.id,
                time_utc=r.created_time,
                actor_name=r.actor_name,
                source=meta.get("source"),
                fmt=meta.get("fmt"),
                rows=meta.get("rows"),
                sha256=meta.get("sha256"),
                detail=r.detail,
            )
        )
    return items
