from datetime import datetime, time, timezone

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import case, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..deps import get_current_user, get_role_by_name, require_roles
from ..models import (
    AiHistory,
    AuditLog,
    Conversation,
    Device,
    LoginLog,
    Notice,
    OAuthAccount,
    PasswordReset,
    RefreshToken,
    Role,
    User,
    VisitLog,
)
from ..schemas import (
    AdminLoginLogItem,
    AdminLoginLogList,
    NoticeCreate,
    NoticeList,
    NoticeOut,
    NoticeUpdate,
    AdminResetPasswordRequest,
    AdminStats,
    AiConfigOut,
    AiConfigUpdate,
    AuditLogItem,
    AuditLogList,
    RefreshTokenAdminOut,
    RoleOut,
    SystemSettingsOut,
    SystemSettingsUpdate,
    SystemStatus,
    UserAdminList,
    UserAdminOut,
    UserRoleUpdate,
    UserStatusUpdate,
    UserUsageItem,
    UserUsageList,
    VisitLogItem,
    VisitLogList,
    VisitStats,
)
from ..security import ROLE_ADMIN, ROLE_SUPER_ADMIN
from ..services import monitor
from ..services import settings as settings_svc
from ..services.audit import record_audit

router = APIRouter(prefix="/admin", tags=["admin"])

# 依赖: 仅 admin / super_admin 可访问
require_admin = require_roles(ROLE_ADMIN, ROLE_SUPER_ADMIN)


def _client_ip(request) -> str | None:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else None


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
    request: Request,
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
    await record_audit(
        db,
        actor=current_user,
        action="user.status",
        resource=f"users/{uid}",
        target_uid=uid,
        detail=f"{'禁用' if not payload.is_active else '启用'}用户 {target.username}",
        ip=_client_ip(request),
    )
    return _to_admin_out(target)


@router.patch("/users/{uid}/role", response_model=UserAdminOut, summary="修改用户角色")
async def admin_user_role(
    uid: str,
    payload: UserRoleUpdate,
    request: Request,
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
            await record_audit(
                db, actor=current_user, action="user.role.denied", resource=f"users/{uid}",
                target_uid=uid, detail=f"尝试修改 {target.username} 角色为 {payload.role}（无权限）",
                ip=_client_ip(request), success=False,
            )
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有 super_admin 可以管理 admin 角色")

    # 不能修改自己的角色（防止降级自己后失去权限）
    if target.uid == current_user.uid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能修改自己的角色")

    old_role = target_role_name or "none"
    target.role_id = new_role.id
    await db.commit()
    await db.refresh(target)
    await record_audit(
        db,
        actor=current_user,
        action="user.role",
        resource=f"users/{uid}",
        target_uid=uid,
        detail=f"修改 {target.username} 角色: {old_role} -> {payload.role}",
        ip=_client_ip(request),
    )
    return _to_admin_out(target)


@router.get("/system/status", response_model=SystemStatus, summary="系统监控")
async def admin_system_status(current_user: User = Depends(require_admin)):
    import asyncio

    # CPU 采样含 0.4s sleep，放线程池避免阻塞事件循环
    return await asyncio.to_thread(monitor.get_system_status)


# ---------- AI 配置管理 ----------


@router.get("/settings/ai", response_model=AiConfigOut, summary="读取 AI 配置")
async def get_ai_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    cfg = await settings_svc.get_ai_config(db)
    eff = settings_svc.ai_effective(cfg)
    quota_raw = await settings_svc.get_setting(db, "ai.daily_quota", default="10")
    try:
        quota = int(quota_raw)
    except (TypeError, ValueError):
        quota = 10
    return AiConfigOut(
        api_key=None,  # 不回显明文
        api_key_set=settings_svc.ai_configured(cfg),
        base_url=eff["base_url"],
        model=eff["model"],
        daily_quota=quota,
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
    if payload.daily_quota is not None:
        await settings_svc.set_setting(db, "ai.daily_quota", str(payload.daily_quota))
    cfg = await settings_svc.get_ai_config(db)
    eff = settings_svc.ai_effective(cfg)
    quota_raw = await settings_svc.get_setting(db, "ai.daily_quota", default="10")
    try:
        quota = int(quota_raw)
    except (TypeError, ValueError):
        quota = 10
    return AiConfigOut(
        api_key=None,
        api_key_set=settings_svc.ai_configured(cfg),
        base_url=eff["base_url"],
        model=eff["model"],
        daily_quota=quota,
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
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(RefreshToken).where(RefreshToken.uid == uid, RefreshToken.revoked.is_(False)))
    tokens = result.scalars().all()
    for t in tokens:
        t.revoked = True
    await db.commit()
    await record_audit(
        db, actor=current_user, action="user.sessions.revoke", resource=f"users/{uid}",
        target_uid=uid, detail=f"吊销用户 {uid} 全部 {len(tokens)} 个会话", ip=_client_ip(request),
    )
    return None


# ---------- 权限管理 ----------


@router.get("/roles", response_model=list[RoleOut], summary="角色列表")
async def admin_roles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(Role).order_by(Role.created_time))
    return result.scalars().all()


# ---------- 系统设置 ----------


@router.get("/settings", response_model=SystemSettingsOut, summary="读取全局设置")
async def get_system_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    site_name = await settings_svc.get_setting(db, "site.name", default="Harness Platform")
    site_desc = await settings_svc.get_setting(db, "site.description", default="个人智能服务平台")
    allow_register = (await settings_svc.get_setting(db, "site.allow_register", default="true")).lower() == "true"
    maintenance = (await settings_svc.get_setting(db, "site.maintenance", default="false")).lower() == "true"
    model = await settings_svc.get_setting(db, "site.default_ai_model", default="deepseek-chat")
    upload_mb = int(await settings_svc.get_setting(db, "site.upload_limit_mb", default="10"))
    return SystemSettingsOut(
        site_name=site_name,
        site_description=site_desc,
        allow_register=allow_register,
        maintenance_mode=maintenance,
        default_ai_model=model,
        upload_limit_mb=upload_mb,
    )


@router.put("/settings", response_model=SystemSettingsOut, summary="更新全局设置")
async def update_system_settings(
    payload: SystemSettingsUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    data = payload.model_dump(exclude_unset=True)
    mapping = {
        "site_name": "site.name",
        "site_description": "site.description",
        "allow_register": "site.allow_register",
        "maintenance_mode": "site.maintenance",
        "default_ai_model": "site.default_ai_model",
        "upload_limit_mb": "site.upload_limit_mb",
    }
    for field, value in data.items():
        if field in mapping:
            await settings_svc.set_setting(db, mapping[field], str(value).lower() if isinstance(value, bool) else str(value))
    await record_audit(
        db, actor=current_user, action="settings.update", resource="settings",
        detail=f"更新系统设置: {', '.join(data.keys())}", ip=_client_ip(request),
    )
    return await get_system_settings(db, current_user)


# ---------- 安全中心 ----------


@router.get("/login-logs", response_model=AdminLoginLogList, summary="登录日志")
async def admin_login_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    base = select(LoginLog).order_by(LoginLog.created_time.desc())
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    result = await db.execute(base.limit(page_size).offset((page - 1) * page_size))
    return AdminLoginLogList(
        items=[AdminLoginLogItem.model_validate(l) for l in result.scalars().all()], total=total
    )


@router.get("/audit-logs", response_model=AuditLogList, summary="操作审计日志")
async def admin_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    base = select(AuditLog).order_by(AuditLog.created_time.desc())
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    result = await db.execute(base.limit(page_size).offset((page - 1) * page_size))
    return AuditLogList(
        items=[AuditLogItem.model_validate(l) for l in result.scalars().all()], total=total
    )


# ---------- 管理员重置密码 ----------


@router.post("/users/{uid}/reset-password", summary="管理员重置密码")
async def admin_reset_password(
    uid: str,
    payload: AdminResetPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    target = await db.get(User, uid)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    from ..security import hash_password as _hp, validate_password_policy

    policy_error = validate_password_policy(payload.new_password)
    if policy_error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=policy_error)

    target.password_hash = _hp(payload.new_password)
    target.password_changed_at = datetime.now(timezone.utc)
    # 吊销全部会话
    result = await db.execute(select(RefreshToken).where(RefreshToken.uid == uid, RefreshToken.revoked.is_(False)))
    tokens = result.scalars().all()
    for t in tokens:
        t.revoked = True
    await db.commit()
    await record_audit(
        db, actor=current_user, action="user.password.reset", resource=f"users/{uid}",
        target_uid=uid, detail=f"管理员重置用户 {target.username} 密码，吊销 {len(tokens)} 个会话",
        ip=_client_ip(request),
    )
    return {"message": f"已重置 {target.username} 的密码，该用户所有设备已下线"}


@router.delete("/users/{uid}", status_code=status.HTTP_204_NO_CONTENT, summary="删除用户（级联清理关联数据）")
async def admin_delete_user(
    uid: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    target = await db.get(User, uid)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    if target.uid == current_user.uid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除当前登录的账号")
    # 防锁死：不能删除唯一的超级管理员
    if target.role and target.role.name == ROLE_SUPER_ADMIN:
        super_count = (
            await db.execute(
                select(func.count())
                .select_from(User)
                .join(Role, User.role_id == Role.id)
                .where(Role.name == ROLE_SUPER_ADMIN)
            )
        ).scalar_one()
        if super_count <= 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除唯一的超级管理员")

    # 级联清理外键依赖行
    for model in (RefreshToken, LoginLog, AiHistory, Conversation, Device, OAuthAccount, PasswordReset):
        await db.execute(delete(model).where(model.uid == uid))

    # 清理头像文件
    if target.avatar and target.avatar.startswith("/uploads/avatars/"):
        try:
            (Path(settings.UPLOAD_DIR) / target.avatar.removeprefix("/uploads/")).unlink(missing_ok=True)
        except Exception:
            pass

    await db.delete(target)
    await db.commit()
    await record_audit(
        db, actor=current_user, action="user.delete", resource=f"users/{uid}",
        target_uid=uid, detail=f"删除用户 {target.username} ({target.email})",
        ip=_client_ip(request),
    )
    return None


# ---------- 流量访问记录 ----------


@router.get("/visits", response_model=VisitLogList, summary="访客访问记录")
async def admin_visits(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    keyword: str | None = Query(default=None, max_length=64),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    now = datetime.now(timezone.utc)
    today_start = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)

    base = select(VisitLog)
    if keyword:
        like = f"%{keyword}%"
        base = base.where(VisitLog.ip.ilike(like) | VisitLog.path.ilike(like))

    # 统计
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    today_total = (
        await db.execute(
            select(func.count()).select_from(VisitLog).where(VisitLog.created_time >= today_start)
        )
    ).scalar_one()
    unique_ips = (
        await db.execute(select(func.count(func.distinct(VisitLog.ip))).select_from(VisitLog))
    ).scalar_one()
    today_unique_ips = (
        await db.execute(
            select(func.count(func.distinct(VisitLog.ip)))
            .select_from(VisitLog)
            .where(VisitLog.created_time >= today_start)
        )
    ).scalar_one()
    page_views = (
        await db.execute(
            select(func.count()).select_from(VisitLog).where(VisitLog.method == "PAGE")
        )
    ).scalar_one()

    # 列表（关联用户名）
    stmt = (
        select(VisitLog, User.username)
        .outerjoin(User, User.uid == VisitLog.uid)
        .order_by(VisitLog.created_time.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(VisitLog.ip.ilike(like) | VisitLog.path.ilike(like))
    result = await db.execute(stmt)
    rows = result.all()

    items = []
    for v, username in rows:
        item = VisitLogItem.model_validate(v)
        item.username = username
        items.append(item)

    return VisitLogList(
        items=items,
        total=total,
        stats=VisitStats(
            total_visits=total,
            today_visits=today_total,
            unique_ips=unique_ips,
            today_unique_ips=today_unique_ips,
            page_views=page_views,
        ),
    )


# ---------- 公告管理 ----------


@router.get("/notices", response_model=NoticeList, summary="公告列表（含草稿）")
async def list_notices(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    total = (await db.execute(select(func.count()).select_from(Notice))).scalar_one()
    result = await db.execute(
        select(Notice).order_by(Notice.created_time.desc()).limit(page_size).offset((page - 1) * page_size)
    )
    items = result.scalars().all()
    return NoticeList(items=[NoticeOut.model_validate(i) for i in items], total=total)


@router.post("/notices", response_model=NoticeOut, summary="新建公告")
async def create_notice(
    payload: NoticeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    notice = Notice(
        title=payload.title,
        content=payload.content,
        is_published=payload.is_published,
    )
    if payload.is_published:
        notice.published_at = datetime.now(timezone.utc)
    db.add(notice)
    await db.commit()
    await db.refresh(notice)
    return NoticeOut.model_validate(notice)


@router.put("/notices/{nid}", response_model=NoticeOut, summary="更新公告")
async def update_notice(
    nid: str,
    payload: NoticeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    notice = await db.get(Notice, nid)
    if notice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="公告不存在")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(notice, key, value)
    if data.get("is_published") is True and notice.published_at is None:
        notice.published_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(notice)
    return NoticeOut.model_validate(notice)


@router.delete("/notices/{nid}", status_code=status.HTTP_204_NO_CONTENT, summary="删除公告")
async def delete_notice(
    nid: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    notice = await db.get(Notice, nid)
    if notice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="公告不存在")
    await db.delete(notice)
    await db.commit()
