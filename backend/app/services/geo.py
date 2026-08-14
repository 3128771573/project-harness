"""IP 属地解析：内存缓存 + ip-api.com 免费查询（国内访问延迟偏高，超时放宽到 8s）

- 成功结果缓存 24h；失败结果只缓存 60s（避免重试风暴，也不污染长期缓存）
"""
import asyncio
import time

import httpx

_CACHE: dict[str, tuple[float, str]] = {}
_CACHE_MAX = 5000
_TTL_OK = 24 * 3600
_TTL_FAIL = 60
_LOCK = asyncio.Lock()

_LOCAL_IPS = {"127.0.0.1", "::1", "localhost", "0.0.0.0"}


async def _lookup_ipapi(ip: str) -> str:
    """ip-api.com：国家/省/市/ISP，免费无需 Key（限频 45/min，有缓存基本不触发）"""
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(
                f"http://ip-api.com/json/{ip}",
                params={"lang": "zh-CN", "fields": "status,country,regionName,city,isp"},
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success":
                    parts = [
                        str(data.get(k)) for k in ("country", "regionName", "city", "isp") if data.get(k)
                    ]
                    if parts:
                        return " ".join(parts)
    except Exception:
        pass
    return "未知"


async def resolve_location(ip: str | None) -> str:
    """解析 IP 属地；查不到返回「未知」"""
    if not ip:
        return "未知"
    if ip in _LOCAL_IPS:
        return "本机"
    now = time.time()
    hit = _CACHE.get(ip)
    if hit and hit[0] > now:
        return hit[1]
    loc = await _lookup_ipapi(ip)
    ttl = _TTL_OK if loc != "未知" else _TTL_FAIL
    async with _LOCK:
        if len(_CACHE) >= _CACHE_MAX:
            _CACHE.pop(next(iter(_CACHE)))
        _CACHE[ip] = (now + ttl, loc)
    return loc
