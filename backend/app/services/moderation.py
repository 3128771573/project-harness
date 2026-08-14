"""内容审核：敏感词拦截（自建词库，命中即拒绝发送并审计）

FR8.3：自建词库，命中自动拦截；管理员可增删启停（admin/im/sensitive-words）
"""
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import SensitiveWord

_WORD_CACHE: dict = {"words": [], "ts": 0.0}
_CACHE_TTL = 60  # 秒


async def get_enabled_words(db: AsyncSession) -> list[str]:
    """启用词列表（60s 缓存，增删词后调用 invalidate）"""
    now = time.time()
    if now - _WORD_CACHE["ts"] > _CACHE_TTL:
        rows = await db.execute(select(SensitiveWord.word).where(SensitiveWord.enabled.is_(True)))
        _WORD_CACHE["words"] = [w for (w,) in rows.all()]
        _WORD_CACHE["ts"] = now
    return _WORD_CACHE["words"]


def invalidate_cache() -> None:
    _WORD_CACHE["words"] = []
    _WORD_CACHE["ts"] = 0.0


async def check_content(db: AsyncSession, content: str) -> str | None:
    """内容检查：命中返回违规词，未命中返回 None"""
    for w in await get_enabled_words(db):
        if w and w in content:
            return w
    return None
