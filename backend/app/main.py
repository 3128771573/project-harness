from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import engine
from .models import Base
from .routers import auth, user


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 简单起见 Phase 1 用 create_all；后续迁移到 Alembic
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Project Harness API",
    version="0.5.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")


@app.get("/api/v1/health", tags=["system"])
async def health():
    return {"status": "ok", "service": "harness-backend", "version": "0.5.0"}
