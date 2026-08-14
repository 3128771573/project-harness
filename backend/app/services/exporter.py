"""企业级日志导出服务：六数据源统一查询 + CSV/JSON 渲染 + SHA-256 完整性

数据源：audit（操作审计）/ login（登录日志）/ visit（访问记录）/
        watermark（水印取证）/ report（举报）/ bot（机器人消息）
约束：时间范围必填且跨度 ≤ 90 天；单次导出 ≤ 100,000 行；CSV 输出 UTF-8 BOM（Excel 兼容）
"""
import csv
import io
import json
from datetime import datetime, timezone
from hashlib import sha256

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    AuditLog,
    DmConversation,
    DmMessage,
    LoginLog,
    Report,
    User,
    VisitLog,
    WatermarkLog,
)
from ..services.bot import BOT_UID

MAX_ROWS = 100_000
MAX_SPAN_DAYS = 90
SOURCE_LABELS = {
    "audit": "操作审计",
    "login": "登录日志",
    "visit": "访问记录",
    "watermark": "水印取证",
    "report": "举报记录",
    "bot": "机器人消息",
}


class ExportError(ValueError):
    pass


# ---------- CSV 渲染 ----------

def _csv_escape(v) -> str:
    if v is None:
        return ""
    s = str(v)
    if any(c in s for c in ',"\n\r'):
        return '"' + s.replace('"', '""') + '"'
    return s


def _fmt(dt: datetime | None) -> str:
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def render_csv(columns: list[str], rows: list[list]) -> tuple[bytes, str]:
    buf = io.StringIO()
    buf.write("\ufeff")  # UTF-8 BOM：Excel 直接打开不乱码
    buf.write(",".join(_csv_escape(c) for c in columns) + "\r\n")
    for row in rows:
        buf.write(",".join(_csv_escape(v) for v in row) + "\r\n")
    data = buf.getvalue().encode("utf-8")
    return data, sha256(data).hexdigest()


def render_json(source: str, start: str, end: str, columns: list[str], rows: list[list]) -> tuple[bytes, str]:
    payload = {
        "source": source,
        "source_label": SOURCE_LABELS.get(source, source),
        "range_start": start,
        "range_end": end,
        "exported_at": _fmt(datetime.now(timezone.utc)),
        "row_count": len(rows),
        "columns": columns,
        "rows": rows,
    }
    data = json.dumps(payload, ensure_ascii=False, indent=1).encode("utf-8")
    return data, sha256(data).hexdigest()


# ---------- 查询构建 ----------

async def _resolve_username(db: AsyncSession, uid: str | None) -> str:
    if not uid:
        return ""
    u = await db.get(User, uid)
    return (u.nickname or u.username) if u else "已注销用户"


async def query_source(db: AsyncSession, source: str, start: datetime, end: datetime, f: dict) -> tuple[list[str], list[list]]:
    """返回 (列头, 行数据)。f 为筛选条件 dict。"""
    if source == "audit":
        cols = ["time_utc", "actor_name", "actor_uid", "action", "resource", "target_uid", "detail", "ip", "success"]
        q = select(AuditLog).where(AuditLog.created_time >= start, AuditLog.created_time <= end)
        if f.get("action"):
            q = q.where(AuditLog.action.contains(f["action"]))
        if f.get("actor"):
            q = q.where(AuditLog.actor_name.contains(f["actor"]))
        if f.get("keyword"):
            kw = f["keyword"]
            q = q.where((AuditLog.detail.contains(kw)) | (AuditLog.resource.contains(kw)) | (AuditLog.action.contains(kw)))
        if f.get("success") is not None:
            q = q.where(AuditLog.success.is_(bool(f["success"])))
        rows = []
        for r in (await db.execute(q.order_by(AuditLog.created_time.desc()).limit(MAX_ROWS))).scalars().all():
            rows.append([_fmt(r.created_time), r.actor_name or "", r.actor_uid or "", r.action, r.resource or "",
                         r.target_uid or "", r.detail or "", r.ip or "", "1" if r.success else "0"])
        return cols, rows

    if source == "login":
        cols = ["time_utc", "email", "uid", "ip", "ip_location", "device", "method", "used_2fa", "success", "reason"]
        q = select(LoginLog).where(LoginLog.created_time >= start, LoginLog.created_time <= end)
        if f.get("email"):
            q = q.where(LoginLog.email.contains(f["email"]))
        if f.get("method"):
            q = q.where(LoginLog.method == f["method"])
        if f.get("success") is not None:
            q = q.where(LoginLog.success.is_(bool(f["success"])))
        rows = []
        for r in (await db.execute(q.order_by(LoginLog.created_time.desc()).limit(MAX_ROWS))).scalars().all():
            rows.append([_fmt(r.created_time), r.email or "", r.uid or "", r.ip or "", r.ip_location or "",
                         r.device or "", r.method or "", "1" if r.used_2fa else "0", "1" if r.success else "0", r.reason or ""])
        return cols, rows

    if source == "visit":
        cols = ["time_utc", "uid", "username", "ip", "ip_location", "device", "path", "method", "referer", "status_code"]
        q = select(VisitLog).where(VisitLog.created_time >= start, VisitLog.created_time <= end)
        if f.get("path"):
            q = q.where(VisitLog.path.contains(f["path"]))
        if f.get("username"):
            q = q.where(VisitLog.username.contains(f["username"]))
        if f.get("status_code"):
            try:
                q = q.where(VisitLog.status_code == int(f["status_code"]))
            except (TypeError, ValueError):
                pass
        rows = []
        for r in (await db.execute(q.order_by(VisitLog.created_time.desc()).limit(MAX_ROWS))).scalars().all():
            rows.append([_fmt(r.created_time), r.uid or "", r.username or "", r.ip or "", r.ip_location or "",
                         r.device or "", r.path, r.method or "", r.referer or "", str(r.status_code or "")])
        return cols, rows

    if source == "watermark":
        cols = ["time_utc", "actor_uid", "actor_username", "kind", "input_hash", "matched_uid", "matched_username", "confidence", "consumed"]
        q = select(WatermarkLog).where(WatermarkLog.created_time >= start, WatermarkLog.created_time <= end)
        if f.get("actor_uid"):
            q = q.where(WatermarkLog.actor_id == f["actor_uid"])
        if f.get("kind"):
            q = q.where(WatermarkLog.kind == f["kind"])
        rows = []
        for r in (await db.execute(q.order_by(WatermarkLog.created_time.desc()).limit(MAX_ROWS))).scalars().all():
            rows.append([_fmt(r.created_time), r.actor_id, await _resolve_username(db, r.actor_id), r.kind,
                         r.input_hash or "", r.matched_uid or "", await _resolve_username(db, r.matched_uid),
                         "" if r.confidence is None else f"{r.confidence:.3f}", "1" if r.consumed else "0"])
        return cols, rows

    if source == "report":
        cols = ["time_utc", "reporter_uid", "reporter_username", "target_type", "target_id", "sender_uid", "reason", "status", "handled_by", "handled_at"]
        q = select(Report).where(Report.created_time >= start, Report.created_time <= end)
        if f.get("status"):
            q = q.where(Report.status == f["status"])
        if f.get("target_type"):
            q = q.where(Report.target_type == f["target_type"])
        rows = []
        for r in (await db.execute(q.order_by(Report.created_time.desc()).limit(MAX_ROWS))).scalars().all():
            rows.append([_fmt(r.created_time), r.reporter_id, await _resolve_username(db, r.reporter_id),
                         r.target_type, r.target_id, r.sender_uid or "", r.reason, r.status,
                         r.handled_by or "", _fmt(r.handled_at)])
        return cols, rows

    if source == "bot":
        cols = ["time_utc", "to_uid", "to_username", "kind", "content"]
        q = (
            select(DmMessage, DmConversation)
            .join(DmConversation, DmConversation.id == DmMessage.conversation_id)
            .where(DmMessage.sender_id == BOT_UID, DmMessage.created_time >= start, DmMessage.created_time <= end)
        )
        if f.get("to"):
            urows = await db.execute(select(User.uid).where(User.username.contains(f["to"])))
            uids = [r for (r,) in urows.all()]
            if uids:
                q = q.where((DmConversation.user_a.in_(uids)) | (DmConversation.user_b.in_(uids)))
        rows = []
        result = await db.execute(q.order_by(DmMessage.created_time.desc()).limit(MAX_ROWS))
        for msg, conv in result.all():
            to_uid = conv.user_b if conv.user_a == BOT_UID else conv.user_a
            rows.append([_fmt(msg.created_time), to_uid, await _resolve_username(db, to_uid), msg.kind, msg.content])
        return cols, rows

    raise ExportError(f"不支持的数据源：{source}")


def validate_range(start: datetime, end: datetime):
    if end < start:
        raise ExportError("结束时间不能早于开始时间")
    span = (end - start).total_seconds() / 86400
    if span > MAX_SPAN_DAYS:
        raise ExportError(f"时间范围不能超过 {MAX_SPAN_DAYS} 天")
