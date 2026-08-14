"""中间件：访问记录 + 企业级维护模式拦截（四模式 / 紧急令牌 / Retry-After）"""
from datetime import datetime, timezone

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from .database import SessionLocal
from .models import User
from .security import ROLE_ADMIN, ROLE_SUPER_ADMIN, decode_token
from .services.maintenance import snapshot, verify_token
from .services.visitlog import parse_client, record_visit, schedule_location_lookup

# 维护模式下始终放行（路径前缀/精确路径）
PUBLIC_PREFIXES = ("/api/v1/auth/", "/api/v1/public/", "/api/v1/admin/")
PUBLIC_PATHS = {
    "/api/v1/health",
    "/api/v1/captcha",
    "/api/v1/system/visit",
    "/api/v1/system/public/maintenance",
}


def _is_admin_payload(payload: dict | None) -> bool:
    return bool(payload and payload.get("type") == "access" and payload.get("role") in (ROLE_ADMIN, ROLE_SUPER_ADMIN))


async def _is_admin_user(db, uid: str | None) -> bool:
    if not uid:
        return False
    user = await db.get(User, uid)
    return bool(
        user is not None
        and user.is_active
        and not user.is_bot
        and user.role is not None
        and user.role.name in (ROLE_ADMIN, ROLE_SUPER_ADMIN)
    )


class MaintenanceMiddleware(BaseHTTPMiddleware):
    """拦截链：白名单 → 紧急令牌 → 管理员 → 模式判断"""

    async def dispatch(self, request: Request, call_next):
        if request.scope["type"] != "http":
            return await call_next(request)
        path = request.url.path
        if path in PUBLIC_PATHS or path.startswith(PUBLIC_PREFIXES):
            return await call_next(request)

        async with SessionLocal() as db:
            snap = await snapshot(db)
            if snap["mode"] == "none":
                return await call_next(request)
            # 紧急令牌绕过
            token = request.query_params.get("__emergency", "")
            if token and verify_token(token, snap["emergency_token_hash"]):
                return await call_next(request)
            # 管理员放行
            auth = request.headers.get("authorization") or ""
            if auth.startswith("Bearer "):
                payload = decode_token(auth[7:])
                if _is_admin_payload(payload):
                    return await call_next(request)
                if payload and payload.get("type") == "access" and await _is_admin_user(db, payload.get("sub")):
                    return await call_next(request)
                # block_new：已登录普通用户放行
                if snap["mode"] == "block_new" and payload and payload.get("type") == "access":
                    return await call_next(request)

        # 拦截：503 + Retry-After + 防缓存
        headers = {"Cache-Control": "no-cache, no-store, must-revalidate"}
        retry_after = 3600
        try:
            if snap.get("auto_close_at"):
                auto_close = datetime.fromisoformat(snap["auto_close_at"])
                retry_after = max(0, int((auto_close - datetime.now(timezone.utc)).total_seconds()))
        except (ValueError, TypeError):
            pass
        headers["Retry-After"] = str(retry_after)
        return JSONResponse(
            {
                "detail": "系统维护中，请稍后再试",
                "maintenance": True,
                "mode": snap["mode"],
                "reason": snap.get("reason", ""),
                "auto_close_at": snap.get("auto_close_at", ""),
            },
            status_code=503,
            headers=headers,
        )


class VisitLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
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
            pass

        return response
