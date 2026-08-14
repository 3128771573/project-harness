from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from .config import settings
from .database import SessionLocal, engine
from .middleware import VisitLogMiddleware
from .models import Base, Role
from .routers import admin, ai, auth, security, system, user
from .security import ROLE_ADMIN, ROLE_SUPER_ADMIN, ROLE_USER


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
    yield
    await engine.dispose()


app = FastAPI(
    title="Project Harness API",
    version="0.10.1",
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

# 访问记录中间件（最后添加 = 最外层）
app.add_middleware(VisitLogMiddleware)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")
app.include_router(security.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(system.router, prefix="/api/v1")


@app.get("/api/v1/health", tags=["system"])
async def health():
    return {"status": "ok", "service": "harness-backend", "version": "0.10.1"}
