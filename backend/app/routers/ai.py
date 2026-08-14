import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..deps import get_current_user
from ..models import AiHistory, User
from ..schemas import AiChatRequest, AiChatResponse, AiHistoryItem, AiHistoryList

router = APIRouter(prefix="/ai", tags=["ai"])


async def _call_ai(question: str) -> str:
    """调用 OpenAI 兼容的 AI API；未配置 key 时进入 mock 模式"""
    if not settings.AI_API_KEY:
        return (
            "（Mock 模式回复）我已收到你的问题："
            f"「{question[:80]}」\n\n"
            "当前 AI_API_KEY 未配置，系统运行在演示模式。"
            "在 .env 中设置 AI_API_KEY 后即可接入真实大模型。"
        )

    url = f"{settings.AI_BASE_URL.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {settings.AI_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": settings.AI_MODEL,
        "messages": [{"role": "user", "content": question}],
        "temperature": 0.7,
    }
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except httpx.HTTPError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"AI 服务调用失败: {e}")


@router.post("/chat", response_model=AiChatResponse)
async def chat(
    payload: AiChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    answer = await _call_ai(payload.question)

    history = AiHistory(
        uid=current_user.uid,
        question=payload.question,
        answer=answer,
        model=settings.AI_MODEL if settings.AI_API_KEY else "mock",
    )
    db.add(history)
    await db.commit()

    return AiChatResponse(answer=answer, model=history.model)


@router.get("/models", response_model=list[str])
async def list_models():
    if settings.AI_API_KEY:
        return [settings.AI_MODEL]
    return ["mock"]


@router.get("/history", response_model=AiHistoryList)
async def history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    base = select(AiHistory).where(AiHistory.uid == current_user.uid)
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()

    result = await db.execute(
        base.order_by(AiHistory.created_time.desc()).limit(limit).offset(offset)
    )
    items = result.scalars().all()
    return AiHistoryList(items=[AiHistoryItem.model_validate(i) for i in items], total=total)
