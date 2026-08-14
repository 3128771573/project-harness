"""IP 属地解析：内存缓存 + 免费查询（百度千帆优先，ip-api.com 兜底；缓存后基本不触发外部请求）"""
import asyncio
import time

import httpx

_CACHE: dict[str, tuple[float, str]] = {}
_CACHE_MAX = 5000
_TTL = 24 * 3600
_LOCK = asyncio.Lock()

_LOCAL_IPS = {"127.0.0.1", "::1", "localhost", "0.0.0.0"}


async def _lookup_baidu(ip: str) -> str | None:
    """百度千帆免费接口：country/province/city/district/isp"""
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.get(
                "https://qifu-api.baidubce.com/ip/geo/v1/district", params={"ip": ip}
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == "Success":
                    d = data.get("data") or {}
                    parts = [
                        str(d.get(k)) for k in ("country", "province", "city", "district", "isp") if d.get(k)
                    ]
                    if parts:
                        return " ".join(parts)
    except Exception:
        pass
    return None


async def _lookup_ipapi(ip: str) -> str | None:
    """ip-api.com 兜底（国内服务器可能不通）"""
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.get(
                f"http://ip-api.com/json/{ip}",
                params={"lang": "zh-CN", "fields": "status,country,regionName,city,isp"},
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success":
                    parts = [str(data.get(k)) for k in ("country", "regionName", "city", "isp") if data.get(k)]
                    if parts:
                        return " ".join(parts)
    except Exception:
        pass
    return None


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
    loc = await _lookup_baidu(ip) or await _lookup_ipapi(ip) or "未知"
    async with _LOCK:
        if len(_CACHE) >= _CACHE_MAX:
            _CACHE.pop(next(iter(_CACHE)))
        _CACHE[ip] = (now + _TTL, loc)
    return loc
