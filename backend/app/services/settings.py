"""动态配置服务：从 app_settings 表读取/写入，未配置时回退到环境变量"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings as env_settings
from ..models import AppSetting

# AI 配置 key 前缀
AI_KEY = "ai.api_key"
AI_BASE_URL = "ai.base_url"
AI_MODEL = "ai.model"

_DEFAULTS = {
    AI_KEY: env_settings.AI_API_KEY,
    AI_BASE_URL: env_settings.AI_BASE_URL,
    AI_MODEL: env_settings.AI_MODEL,
}


async def _get(db: AsyncSession, key: str) -> str | None:
    result = await db.execute(select(AppSetting).where(AppSetting.key == key))
    row = result.scalar_one_or_none()
    if row is not None:
        return row.value
    return _DEFAULTS.get(key)


async def get_ai_config(db: AsyncSession) -> dict:
    """返回当前生效的 AI 配置（DB 优先，缺省回退 env）"""
    return {
        "api_key": await _get(db, AI_KEY),
        "base_url": await _get(db, AI_BASE_URL),
        "model": await _get(db, AI_MODEL),
    }


async def set_ai_config(db: AsyncSession, api_key: str | None, base_url: str | None, model: str | None) -> dict:
    """写入 AI 配置。None 表示恢复默认（删除 DB 记录，回退 env）"""
    for key, val in ((AI_KEY, api_key), (AI_BASE_URL, base_url), (AI_MODEL, model)):
        result = await db.execute(select(AppSetting).where(AppSetting.key == key))
        row = result.scalar_one_or_none()
        if val is None:
            # 恢复默认：删除 DB 记录
            if row is not None:
                await db.delete(row)
        else:
            if row is None:
                db.add(AppSetting(key=key, value=val))
            else:
                row.value = val
    await db.commit()
    return await get_ai_config(db)


def ai_configured(cfg: dict) -> bool:
    return bool(cfg.get("api_key"))


def ai_effective(cfg: dict) -> dict:
    """返回实际使用的调用参数（含默认回退）"""
    return {
        "api_key": cfg.get("api_key") or "",
        "base_url": cfg.get("base_url") or env_settings.AI_BASE_URL,
        "model": cfg.get("model") or env_settings.AI_MODEL,
    }
