import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select, text

from .config import settings
from .database import SessionLocal, engine
from .errors import validation_error_handler
from .middleware import MaintenanceMiddleware, VisitLogMiddleware
from .models import Base, Notice, Role, VisitLog
from .routers import admin, admin_export, admin_im, ai, auth, guestbook, im, im_groups, iot, oauth, security, system, user
from .services.bot import ensure_bot
from .services.cleanup import cleanup_loop
from .services.iot_mqtt import mqtt_worker
from .security import ROLE_ADMIN, ROLE_SUPER_ADMIN, ROLE_USER

# 版本号集中管理
APP_VERSION = "0.10.1"

# 进程启动时间（用于公开统计接口的「稳定运行时长」）
START_TIME = datetime.now(timezone.utc)

# 安全校验：生产环境禁止使用默认 JWT 密钥（fail-fast）
if settings.JWT_SECRET in ("", "change-me-in-prod-please"):
    raise RuntimeError(
        "JWT_SECRET 未配置或仍为默认值：请在生产环境 .env 中设置随机密钥（如 openssl rand -hex 32）"
    )


async def seed_roles():
    """启动时确保基础角色存在"""
    async with SessionLocal() as db:
        for name in (ROLE_USER, ROLE_ADMIN, ROLE_SUPER_ADMIN):
            result = await db.execute(select(Role).where(Role.name == name))
            if result.scalar_one_or_none() is None:
                db.add(Role(name=name))
        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Phase 1 用 create_all；后续迁移到 Alembic
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_roles()
    # 确保公告机器账号存在（uid 固定保留）
    async with SessionLocal() as db:
        await ensure_bot(db)
    # 启动 MQTT 遥测订阅（任务挂在 app.state 防止被 GC；broker 未就绪会自动重连）
    app.state.mqtt_task = asyncio.create_task(mqtt_worker())
    # 启动每日过期数据清理
    app.state.cleanup_task = asyncio.create_task(cleanup_loop())
    yield
    app.state.mqtt_task.cancel()
    app.state.cleanup_task.cancel()
    await engine.dispose()


app = FastAPI(
    title="Project Harness API",
    version=APP_VERSION,
    lifespan=lifespan,
)

# 校验错误 → 友好中文提示
app.add_exception_handler(RequestValidationError, validation_error_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 访问记录中间件
app.add_middleware(VisitLogMiddleware)
# 维护模式中间件（最外层：最先拦截）——注意：后添加的中间件更靠外
app.add_middleware(MaintenanceMiddleware)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")
app.include_router(security.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(system.router, prefix="/api/v1")
app.include_router(iot.router, prefix="/api/v1")
app.include_router(guestbook.router, prefix="/api/v1")
app.include_router(oauth.router, prefix="/api/v1")
app.include_router(im.router, prefix="/api/v1")
app.include_router(im_groups.router, prefix="/api/v1")
app.include_router(admin_im.router, prefix="/api/v1")
app.include_router(admin_export.router, prefix="/api/v1")


@app.get("/api/v1/health", tags=["system"])
async def health():
    return {"status": "ok", "service": "harness-backend", "version": APP_VERSION}


@app.get("/api/v1/public/stats", tags=["system"])
async def public_stats():
    """公开站点统计：版本 / 启动时间 / 稳定运行时长 / 累计页面访问（仅 PAGE，API/刷新/重复点击不计）"""
    async with SessionLocal() as db:
        visits = (
            await db.scalar(
                select(func.count()).select_from(VisitLog).where(VisitLog.method == "PAGE")
            )
            or 0
        )
    now = datetime.now(timezone.utc)
    return {
        "version": app.version,
        "started_at": START_TIME.isoformat(),
        "uptime_seconds": max(0, int((now - START_TIME).total_seconds())),
        "visits": visits,
    }


@app.get("/api/v1/public/maintenance", tags=["system"])
async def public_maintenance():
    """公开维护状态（维护页 / 路由守卫轮询；维护模式白名单放行）"""
    from .services import settings as settings_svc
    from .services.maintenance import is_maintenance

    async with SessionLocal() as db:
        return {
            "maintenance": await is_maintenance(db),
            "message": await settings_svc.get_setting(db, "site.maintenance_message", default="系统正在升级维护，请稍后再试。"),
        }


@app.get("/api/v1/public/notices", tags=["system"])
async def public_notices(limit: int = 5):
    """已发布的公告（最新在前），供前台横幅与铃铛使用"""
    async with SessionLocal() as db:
        result = await db.execute(
            select(Notice)
            .where(Notice.is_published.is_(True))
            .order_by(Notice.published_at.desc())
            .limit(limit)
        )
        items = result.scalars().all()
    return {
        "items": [
            {"id": n.id, "title": n.title, "content": n.content, "published_at": n.published_at}
            for n in items
        ],
        "total": len(items),
    }


@app.get("/api/v1/public/status", tags=["system"])
async def public_status():
    """公开服务状态：数据库连通性 / 版本 / 访问统计（Status 页真实数据源）"""
    db_ok = True
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    async with SessionLocal() as db:
        page_only = VisitLog.method == "PAGE"
        total_visits = (
            await db.scalar(select(func.count()).select_from(VisitLog).where(page_only)) or 0
        )
        today_visits = (
            await db.scalar(
                select(func.count())
                .select_from(VisitLog)
                .where(page_only, VisitLog.created_time >= today_start)
            )
        ) or 0
    return {
        "version": app.version,
        "db": db_ok,
        "uptime_seconds": max(0, int((now - START_TIME).total_seconds())),
        "visits": total_visits,
        "today_visits": today_visits,
        "checked_at": now.isoformat(),
    }
