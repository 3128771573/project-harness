"""企业级维护模式服务：配置读写（maintenance_config）/ 四模式 / 自动关闭 / 定时维护 / 紧急令牌

模式：none / full / block_new / scheduled / admin_only
自动恢复三级保险：倒计时(auto_close_at) > 超时兜底(max_duration_minutes) > 重启检测
缓存：状态 60s TTL + 变更主动失效
"""
import hashlib
import secrets
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import MaintenanceConfig

MODES = ("full", "block_new", "scheduled", "admin_only")
MODE_LABELS = {
    "full": "全站维护",
    "block_new": "仅拦截新访客",
    "scheduled": "定时维护",
    "admin_only": "仅管理员模式",
}

_CACHE: dict = {"data": None, "ts": 0.0}
_CACHE_TTL = 60  # 秒（规格：状态缓存 TTL 60s，变更主动清除实时生效）


async def _get(db: AsyncSession, key: str, default: str = "") -> str:
    row = (
        await db.execute(select(MaintenanceConfig).where(MaintenanceConfig.config_key == key))
    ).scalar_one_or_none()
    return row.config_value if row is not None and row.config_value is not None else default


async def _set(db: AsyncSession, key: str, value: str, by: str | None = None) -> None:
    row = (
        await db.execute(select(MaintenanceConfig).where(MaintenanceConfig.config_key == key))
    ).scalar_one_or_none()
    if row is None:
        db.add(MaintenanceConfig(config_key=key, config_value=value, updated_by=by))
    else:
        row.config_value = value
        row.updated_by = by
    await db.commit()


async def snapshot(db: AsyncSession) -> dict:
    """维护状态快照（带 60s 缓存）"""
    now = time.time()
    if now - _CACHE["ts"] <= _CACHE_TTL and _CACHE["data"] is not None:
        return _CACHE["data"]
    data = {
        "mode": await _get(db, "mode", "none"),
        "reason": await _get(db, "reason", ""),
        "operator": await _get(db, "operator", ""),
        "start_at": await _get(db, "start_at", ""),
        "auto_close_at": await _get(db, "auto_close_at", ""),
        "max_duration_minutes": int(await _get(db, "max_duration_minutes", "120") or 120),
        "emergency_token_hash": await _get(db, "emergency_token_hash", ""),
        "scheduled_enabled": (await _get(db, "scheduled_enabled", "false")).lower() == "true",
        "scheduled_time": await _get(db, "scheduled_time", "03:00"),
        "scheduled_duration": int(await _get(db, "scheduled_duration", "60") or 60),
        "scheduled_days": await _get(db, "scheduled_days", ""),
    }
    _CACHE["data"] = data
    _CACHE["ts"] = now
    return data


def invalidate() -> None:
    _CACHE["ts"] = 0.0


async def is_maintenance(db: AsyncSession) -> bool:
    return (await snapshot(db))["mode"] != "none"


def mode_label(mode: str) -> str:
    return MODE_LABELS.get(mode, mode or "未维护")


# ---------- 开关与配置 ----------

async def enable(db: AsyncSession, *, mode: str, reason: str, duration_minutes: int | None, by: str) -> dict:
    """开启维护模式：记录开启人/时间/原因/倒计时"""
    now = datetime.now(timezone.utc)
    await _set(db, "mode", mode, by)
    await _set(db, "reason", reason[:200], by)
    await _set(db, "operator", by, by)
    await _set(db, "start_at", now.isoformat(), by)
    if duration_minutes and duration_minutes > 0:
        auto_close = now + timedelta(minutes=duration_minutes)
        await _set(db, "auto_close_at", auto_close.isoformat(), by)
    else:
        await _set(db, "auto_close_at", "", by)
    invalidate()
    return {"mode": mode, "auto_close_at": await _get(db, "auto_close_at", "")}


async def disable(db: AsyncSession, *, by: str, action: str = "maintenance.disable") -> dict:
    """关闭维护模式"""
    await _set(db, "mode", "none", by)
    await _set(db, "auto_close_at", "", by)
    invalidate()
    return {"mode": "none"}


async def extend(db: AsyncSession, *, minutes: int, by: str) -> dict:
    """延长维护：重置 auto_close_at"""
    now = datetime.now(timezone.utc)
    auto_close = now + timedelta(minutes=minutes)
    await _set(db, "auto_close_at", auto_close.isoformat(), by)
    invalidate()
    return {"auto_close_at": auto_close.isoformat()}


# ---------- 紧急令牌 ----------

def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_token() -> tuple[str, str]:
    """生成 64 位随机令牌：返回 (明文, 哈希)。明文仅此一次返回，之后只存哈希"""
    token = secrets.token_urlsafe(48)  # ~64 chars
    return token, _hash_token(token)


def verify_token(token: str, token_hash: str) -> bool:
    if not token or not token_hash:
        return False
    return secrets.compare_digest(_hash_token(token), token_hash)


# ---------- 自动恢复（维护循环，每 10s 执行） ----------

async def maintenance_tick(db: AsyncSession) -> dict:
    """执行一次自动恢复检查；返回本次动作（供审计/通知）"""
    snap = await snapshot(db)
    mode = snap["mode"]
    if mode == "none":
        # 定时维护检查
        if snap["scheduled_enabled"]:
            return await _maybe_start_scheduled(db, snap)
        return {}
    now = datetime.now(timezone.utc)
    started = None
    try:
        started = datetime.fromisoformat(snap["start_at"]) if snap["start_at"] else None
    except ValueError:
        started = None
    # 1) 倒计时自动关闭
    if snap["auto_close_at"]:
        try:
            auto_close = datetime.fromisoformat(snap["auto_close_at"])
            if now >= auto_close:
                await disable(db, by="system", action="maintenance.auto_close")
                return {"action": "auto_close", "detail": f"倒计时结束自动关闭（mode={mode}）"}
        except ValueError:
            pass
    # 2) 超时兜底（默认 120 分钟）
    if started is not None:
        elapsed = (now - started).total_seconds() / 60
        if elapsed > snap["max_duration_minutes"]:
            await disable(db, by="system", action="maintenance.auto_close")
            return {"action": "auto_close", "detail": f"超过最大时长 {snap['max_duration_minutes']} 分钟自动关闭（mode={mode}）"}
    return {}


async def _maybe_start_scheduled(db: AsyncSession, snap: dict) -> dict:
    """定时维护：到达计划时间自动开启 scheduled 模式"""
    now = datetime.now(timezone.utc)
    now_local = now.replace(tzinfo=None)  # 配置按服务器本地时间解释
    try:
        hh, mm = snap["scheduled_time"].split(":")
        target_minute = int(hh) * 60 + int(mm)
    except (ValueError, AttributeError):
        return {}
    current_minute = now_local.hour * 60 + now_local.minute
    if current_minute != target_minute:
        return {}
    if snap["scheduled_days"]:
        days = {int(x) for x in snap["scheduled_days"].split(",") if x.strip().isdigit()}
        if (now_local.weekday() + 1) % 7 not in days:  # 0=周日
            return {}
    await enable(db, mode="scheduled", reason="定时维护（自动开启）", duration_minutes=snap["scheduled_duration"], by="system")
    return {"action": "scheduled_start", "detail": f"定时维护自动开启，时长 {snap['scheduled_duration']} 分钟"}


async def on_server_start(db: AsyncSession) -> dict:
    """服务器重启后的遗留维护检测：开启超过 30 分钟则自动关闭，否则保持并记录"""
    snap = await snapshot(db)
    if snap["mode"] == "none":
        return {}
    started = None
    try:
        started = datetime.fromisoformat(snap["start_at"]) if snap["start_at"] else None
    except ValueError:
        started = None
    if started is not None:
        elapsed = (datetime.now(timezone.utc) - started).total_seconds() / 60
        if elapsed > 30:
            await disable(db, by="system", action="maintenance.auto_close")
            return {"action": "auto_close", "detail": f"服务器重启检测到遗留维护状态（开启 {int(elapsed)} 分钟）已自动关闭"}
        return {"action": "keep", "detail": f"服务器重启，维护模式保持开启（开启 {int(elapsed)} 分钟 < 30 分钟阈值）"}
    return {}
