"""维护模式：读 AppSetting site.maintenance（进程内短缓存，避免每请求查库）"""
import time

from sqlalchemy.ext.asyncio import AsyncSession

from .settings import get_setting

_CACHE: dict = {"mode": None, "ts": 0.0}
_CACHE_TTL = 2.0  # 秒（开关变更最多 2s 生效）


async def is_maintenance(db: AsyncSession) -> bool:
    now = time.time()
    if now - _CACHE["ts"] > _CACHE_TTL:
        mode = (await get_setting(db, "site.maintenance", default="false")).lower() == "true"
        _CACHE["mode"] = mode
        _CACHE["ts"] = now
    return bool(_CACHE["mode"])


def invalidate() -> None:
    _CACHE["ts"] = 0.0
