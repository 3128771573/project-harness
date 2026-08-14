"""系统公共接口：页面访问上报、访客统计"""
from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..deps import get_optional_user
from ..models import User
from ..services.visitlog import parse_client, record_visit, schedule_location_lookup

router = APIRouter(prefix="/system", tags=["system"])


class VisitReport(BaseModel):
    path: str = Field(max_length=255)
    referer: str | None = Field(default=None, max_length=512)


@router.post("/visit", status_code=status.HTTP_204_NO_CONTENT, summary="上报页面访问（前端路由切换时调用）")
async def report_visit(
    payload: VisitReport,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    ip, ua = parse_client(request)
    row = await record_visit(
        db,
        path=payload.path,
        method="PAGE",
        ip=ip,
        user_agent=ua,
        uid=current_user.uid if current_user else None,
        referer=payload.referer,
    )
    if row is not None:
        await db.commit()
        schedule_location_lookup(row.id, ip)
    return None
