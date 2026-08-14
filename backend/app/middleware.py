"""访问记录中间件：记录每个 API 请求（IP/UA/路径/用户/状态码）"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .database import SessionLocal
from .security import decode_token
from .services.visitlog import parse_client, record_visit

# 不记录的路径（健康检查等噪音）
_SKIP_PREFIXES = ("/api/v1/health",)
_SKIP_EXACT = ("/api/v1/system/visit",)


class VisitLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 只记录 API 请求
        path = request.url.path
        if not path.startswith("/api/"):
            return await call_next(request)
        if any(path.startswith(p) for p in _SKIP_PREFIXES) or path in _SKIP_EXACT:
            return await call_next(request)

        # 解析 token 中的 uid（不强制登录）
        uid = None
        auth = request.headers.get("authorization")
        if auth and auth.lower().startswith("bearer "):
            payload = decode_token(auth[7:])
            if payload and payload.get("type") == "access":
                uid = payload.get("sub")

        ip, ua = parse_client(request)
        referer = request.headers.get("referer")

        response: Response = await call_next(request)

        # 异步写入（独立 session，避免阻塞请求）
        try:
            async with SessionLocal() as db:
                await record_visit(
                    db,
                    path=path,
                    method=request.method,
                    ip=ip,
                    user_agent=ua,
                    uid=uid,
                    referer=referer,
                    status_code=response.status_code,
                )
                await db.commit()
        except Exception:
            pass  # 记录失败不影响请求

        return response
