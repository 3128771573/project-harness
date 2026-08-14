from fastapi import APIRouter, Depends

from ..deps import get_current_user, require_roles
from ..models import User
from ..schemas import UserOut
from ..security import ROLE_ADMIN, ROLE_SUPER_ADMIN

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/ping", summary="管理员权限测试")
async def admin_ping(current_user: User = Depends(require_roles(ROLE_ADMIN, ROLE_SUPER_ADMIN))):
    return {"message": "管理员访问成功", "uid": current_user.uid, "role": current_user.role.name if current_user.role else None}


@router.get("/users/me", response_model=UserOut, summary="管理员查看自己信息")
async def admin_me(current_user: User = Depends(require_roles(ROLE_ADMIN, ROLE_SUPER_ADMIN))):
    return current_user
