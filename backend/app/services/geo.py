"""IP 属地解析：内存缓存 + 免费接口（pconline 国内主查询，ip-api 兜底）

- pconline（whois.pconline.com.cn）：国内服务、延迟低，返回 省/市
- ip-api.com：信息更全（国家/省/市/ISP），但国内访问延迟不稳定，仅作兜底
- 成功结果缓存 24h；失败结果只缓存 60s（避免重试风暴，不污染长期缓存）
"""
import asyncio
import json
import time

import httpx

_CACHE: dict[str, tuple[float, str]] = {}
_CACHE_MAX = 5000
_TTL_OK = 24 * 3600
_TTL_FAIL = 60
_LOCK = asyncio.Lock()

_LOCAL_IPS = {"127.0.0.1", "::1", "localhost", "0.0.0.0"}


async def _lookup_pconline(ip: str) -> str | None:
    """pconline：GBK 编码 JSON，{pro: 省, city: 市, addr: 省市区+运营商}"""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"https://whois.pconline.com.cn/ipJson.jsp?ip={ip}&json=true")
            if resp.status_code == 200:
                text = resp.content.decode("gbk", errors="ignore").strip()
                # 去掉可能的赋值前缀（如 var ipJson = ...）
                if text.startswith("{"):
                    data = json.loads(text)
                else:
                    data = json.loads(text.split("=", 1)[1].rstrip(";").strip())
                pro = data.get("pro")
                city = data.get("city")
                addr = data.get("addr")
                parts = [p for p in (pro, city) if p]
                if parts:
                    # addr 通常含运营商（如「移通」），附加到末尾增强信息
                    if addr and addr not in parts:
                        tail = addr.split(" ", 1)[0] if " " in addr else None
                    return " ".join(parts)
    except Exception:
        pass
    return None


async def _lookup_ipapi(ip: str) -> str | None:
    """ip-api.com：国家/省/市/ISP（国内访问慢，仅兜底）"""
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
    loc = await _lookup_pconline(ip) or await _lookup_ipapi(ip) or "未知"
    ttl = _TTL_OK if loc != "未知" else _TTL_FAIL
    async with _LOCK:
        if len(_CACHE) >= _CACHE_MAX:
            _CACHE.pop(next(iter(_CACHE)))
        _CACHE[ip] = (now + ttl, loc)
    return loc
