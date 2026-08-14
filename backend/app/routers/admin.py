from datetime import datetime, time, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..deps import get_current_user, get_role_by_name, require_roles
from ..models import AiHistory, Role, User
from ..schemas import AdminStats, SystemStatus, UserAdminList, UserAdminOut, UserRoleUpdate, UserStatusUpdate
from ..security import ROLE_ADMIN, ROLE_SUPER_ADMIN
from ..services import monitor

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
