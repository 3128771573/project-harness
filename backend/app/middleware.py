"""访问记录中间件：兜底记录「直接 URL 访问」的页面请求（SPA 内路由切换由前端 sendBeacon 上报）"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .database import SessionLocal
from .services.visitlog import parse_client, record_visit, schedule_location_lookup


class VisitLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        # 只兜底页面文档请求：跳过 API、静态资源（含扩展名的路径）、favicon
        last = path.rstrip("/").rsplit("/", 1)[-1] if path.rstrip("/") else ""
        if path.startswith("/api/") or "." in last or path in ("/favicon.ico", "/favicon.svg"):
            return await call_next(request)

        ip, ua = parse_client(request)

        response: Response = await call_next(request)

        try:
            async with SessionLocal() as db:
                row = await record_visit(
                    db,
                    path=path,
                    method="PAGE",
                    ip=ip,
                    user_agent=ua,
                    status_code=response.status_code,
                )
                if row is not None:
                    await db.commit()
                    schedule_location_lookup(row.id, ip)
        except Exception:
            pass  # 记录失败不影响请求

        return response
