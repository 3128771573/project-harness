from datetime import datetime, time, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..deps import get_current_user, get_role_by_name, require_roles
from ..models import AiHistory, RefreshToken, Role, User
from ..schemas import (
    AdminStats,
    AiConfigOut,
    AiConfigUpdate,
    RefreshTokenAdminOut,
    SystemStatus,
    UserAdminList,
    UserAdminOut,
    UserRoleUpdate,
    UserStatusUpdate,
    UserUsageItem,
    UserUsageList,
)
from ..security import ROLE_ADMIN, ROLE_SUPER_ADMIN
from ..services import monitor
from ..services import settings as settings_svc

router = APIRouter(prefix="/admin", tags=["admin"])

# 依赖: 仅 admin / super_admin 可访问
require_admin = require_roles(ROLE_ADMIN, ROLE_SUPER_ADMIN)


def _to_admin_out(user: User) -> UserAdminOut:
    return UserAdminOut(
        uid=user.uid,
        username=user.username,
        email=user.email,
        role=user.role.name if user.role else None,
        is_active=user.is_active,
        created_time=user.created_time,
    )


@router.get("/ping", summary="管理员权限测试")
async def admin_ping(current_user: User = Depends(require_admin)):
    return {"message": "管理员访问成功", "uid": current_user.uid, "role": current_user.role.name if current_user.role else None}


@router.get("/stats", response_model=AdminStats, summary="平台统计")
async def admin_stats(db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar_one()

    # 今日零点 (UTC)
    now = datetime.now(timezone.utc)
    today_start = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)

    today_new = (
        await db.execute(select(func.count()).select_from(User).where(User.created_time >= today_start))
    ).scalar_one()
    total_ai = (await db.execute(select(func.count()).select_from(AiHistory))).scalar_one()
    today_ai = (
        await db.execute(select(func.count()).select_from(AiHistory).where(AiHistory.created_time >= today_start))
    ).scalar_one()

    return AdminStats(
        total_users=total_users,
        today_new_users=today_new,
        total_ai_calls=total_ai,
        today_ai_calls=today_ai,
    )


@router.get("/users", response_model=UserAdminList, summary="用户列表（分页）")
async def admin_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    keyword: str | None = Query(default=None, max_length=64),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    base = select(User)
    if keyword:
        like = f"%{keyword}%"
        base = base.where(User.username.ilike(like) | User.email.ilike(like))

    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    result = await db.execute(
        base.order_by(User.created_time.desc()).limit(page_size).offset((page - 1) * page_size)
    )
    users = result.scalars().all()
    return UserAdminList(
        items=[_to_admin_out(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch("/users/{uid}/status", response_model=UserAdminOut, summary="禁用/启用用户")
async def admin_user_status(
    uid: str,
    payload: UserStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    target = await db.get(User, uid)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    if target.uid == current_user.uid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能禁用自己")
    target.is_active = payload.is_active
    await db.commit()
    await db.refresh(target)
    return _to_admin_out(target)


@router.patch("/users/{uid}/role", response_model=UserAdminOut, summary="修改用户角色")
async def admin_user_role(
    uid: str,
    payload: UserRoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    target = await db.get(User, uid)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    new_role = await get_role_by_name(db, payload.role)
    if new_role is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="角色不存在")

    target_role_name = target.role.name if target.role else None

    # super_admin 保护：修改 admin 及以上角色的用户需要 super_admin
    if target_role_name in (ROLE_ADMIN, ROLE_SUPER_ADMIN) or payload.role in (ROLE_ADMIN, ROLE_SUPER_ADMIN):
        if current_user.role.name != ROLE_SUPER_ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有 super_admin 可以管理 admin 角色")

    # 不能修改自己的角色（防止降级自己后失去权限）
    if target.uid == current_user.uid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能修改自己的角色")

    target.role_id = new_role.id
    await db.commit()
    await db.refresh(target)
    return _to_admin_out(target)


@router.get("/system/status", response_model=SystemStatus, summary="系统监控")
async def admin_system_status(current_user: User = Depends(require_admin)):
    return monitor.get_system_status()


# ---------- AI 配置管理 ----------


@router.get("/settings/ai", response_model=AiConfigOut, summary="读取 AI 配置")
async def get_ai_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    cfg = await settings_svc.get_ai_config(db)
    eff = settings_svc.ai_effective(cfg)
    return AiConfigOut(
        api_key=None,  # 不回显明文
        api_key_set=settings_svc.ai_configured(cfg),
        base_url=eff["base_url"],
        model=eff["model"],
    )


@router.put("/settings/ai", response_model=AiConfigOut, summary="更新 AI 配置")
async def update_ai_config(
    payload: AiConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    # 读取当前配置
    cfg = await settings_svc.get_ai_config(db)
    new_key = payload.api_key if payload.api_key else (None if payload.clear_api_key else cfg.get("api_key"))
    await settings_svc.set_ai_config(db, api_key=new_key, base_url=payload.base_url, model=payload.model)
    cfg = await settings_svc.get_ai_config(db)
    eff = settings_svc.ai_effective(cfg)
    return AiConfigOut(
        api_key=None,
        api_key_set=settings_svc.ai_configured(cfg),
        base_url=eff["base_url"],
        model=eff["model"],
    )


@router.post("/settings/ai/test", summary="测试 AI 连接")
async def test_ai_connection(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    import httpx

    cfg = await settings_svc.get_ai_config(db)
    eff = settings_svc.ai_effective(cfg)
    if not settings_svc.ai_configured(cfg):
        return {"ok": False, "message": "未配置 API Key，当前为 Mock 模式"}
    url = f"{eff['base_url'].rstrip('/')}/models"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                url, headers={"Authorization": f"Bearer {eff['api_key']}"}
            )
            if resp.status_code == 200:
                return {"ok": True, "message": f"连接成功，可用模型: {len(resp.json().get('data', []))} 个"}
            return {"ok": False, "message": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except Exception as e:
        return {"ok": False, "message": f"连接失败: {e}"}


# ---------- 用户用量统计 ----------


@router.get("/usage", response_model=UserUsageList, summary="每位用户的 AI 使用量")
async def admin_usage(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    now = datetime.now(timezone.utc)
    today_start = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)

    # 每用户统计: 总调用 + 今日调用 + 最近使用
    today_case = case((AiHistory.created_time >= today_start, 1), else_=0)
    stmt = (
        select(
            User.uid,
            User.username,
            User.email,
            func.count(AiHistory.id).label("total_calls"),
            func.coalesce(func.sum(today_case), 0).label("today_calls"),
            func.max(AiHistory.created_time).label("last_used"),
        )
        .outerjoin(AiHistory, AiHistory.uid == User.uid)
        .group_by(User.uid, User.username, User.email)
        .order_by(func.count(AiHistory.id).desc())
    )
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    total_calls = (await db.execute(select(func.count()).select_from(AiHistory))).scalar_one()
    result = await db.execute(stmt.limit(page_size).offset((page - 1) * page_size))
    rows = result.all()
    items = [
        UserUsageItem(
            uid=r.uid,
            username=r.username,
            email=r.email,
            total_calls=r.total_calls or 0,
            today_calls=r.today_calls or 0,
            last_used=r.last_used,
        )
        for r in rows
    ]
    return UserUsageList(items=items, total=total_users, total_calls=total_calls)


# ---------- Token 使用管理 ----------


@router.get("/tokens", response_model=list[RefreshTokenAdminOut], summary="查看各用户的活跃刷新令牌")
async def admin_tokens(
    include_revoked: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    stmt = select(RefreshToken, User.username).join(User, User.uid == RefreshToken.uid)
    if not include_revoked:
        stmt = stmt.where(RefreshToken.revoked.is_(False))
    stmt = stmt.order_by(RefreshToken.created_time.desc()).limit(200)
    result = await db.execute(stmt)
    rows = result.all()
    return [
        RefreshTokenAdminOut(
            id=t.id,
            uid=t.uid,
            username=username,
            created_time=t.created_time,
            expires_at=t.expires_at,
            revoked=t.revoked,
        )
        for t, username in rows
    ]


@router.delete("/tokens/{token_id}", status_code=status.HTTP_204_NO_CONTENT, summary="吊销指定刷新令牌")
async def revoke_token(
    token_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    token = await db.get(RefreshToken, token_id)
    if token is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="令牌不存在")
    token.revoked = True
    await db.commit()
    return None


@router.delete("/tokens/user/{uid}", status_code=status.HTTP_204_NO_CONTENT, summary="吊销某用户全部令牌")
async def revoke_user_tokens(
    uid: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(RefreshToken).where(RefreshToken.uid == uid, RefreshToken.revoked.is_(False)))
    tokens = result.scalars().all()
    for t in tokens:
        t.revoked = True
    await db.commit()
    return None
