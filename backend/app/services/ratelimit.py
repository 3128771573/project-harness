"""IP 维度限流（单实例内存滑动窗口；多实例需换 Redis）"""
import threading
import time

_store: dict[str, list[float]] = {}
_lock = threading.Lock()


def check(key: str, limit: int, window: float) -> bool:
    """窗口内超过 limit 次返回 False；key 如 'login:{ip}'"""
    now = time.time()
    with _lock:
        q = [t for t in _store.get(key, []) if t > now - window]
        if len(q) >= limit:
            _store[key] = q
            return False
        q.append(now)
        _store[key] = q
        return True


def reset(key: str) -> None:
    """清除某键计数（如登录成功后）"""
    with _lock:
        _store.pop(key, None)
