"""中间件：访问记录 + 维护模式拦截"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from .database import SessionLocal
from .models import User
from .security import ROLE_ADMIN, ROLE_SUPER_ADMIN, decode_token
from .services.maintenance import is_maintenance
from .services.visitlog import parse_client, record_visit, schedule_location_lookup


class MaintenanceMiddleware(BaseHTTPMiddleware):
    """维护模式：非管理员请求返回 503；公开接口与管理员放行"""

    _PUBLIC_PREFIXES = ("/api/v1/auth/", "/api/v1/public/", "/api/v1/admin/")
    _PUBLIC_PATHS = {
        "/api/v1/health",
        "/api/v1/captcha",
        "/api/v1/system/visit",
    }

    async def dispatch(self, request: Request, call_next):
        if request.scope["type"] != "http":
            return await call_next(request)
        path = request.url.path
        async with SessionLocal() as db:
            if not await is_maintenance(db):
                return await call_next(request)
        # 维护中：公开白名单放行（登录/公开信息/健康检查/验证码）
        if path in self._PUBLIC_PATHS or path.startswith(self._PUBLIC_PREFIXES):
            return await call_next(request)
        # 管理员放行（解析 access token 并校验角色）
        auth = request.headers.get("authorization") or ""
        if auth.startswith("Bearer "):
            payload = decode_token(auth[7:])
            if payload and payload.get("type") == "access":
                async with SessionLocal() as db:
                    user = await db.get(User, payload.get("sub"))
                    if (
                        user is not None
                        and user.is_active
                        and not user.is_bot
                        and user.role is not None
                        and user.role.name in (ROLE_ADMIN, ROLE_SUPER_ADMIN)
                    ):
                        return await call_next(request)
        return JSONResponse({"detail": "系统维护中，请稍后再试"}, status_code=503)


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
