import asyncio
import json
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..deps import get_current_user
from ..models import AiHistory, Conversation, User
from ..schemas import (
    AiChatRequest,
    AiChatResponse,
    AiHistoryItem,
    AiHistoryList,
    ConversationCreate,
    ConversationList,
    ConversationOut,
    ConversationUpdate,
)
from ..security import ROLE_ADMIN, ROLE_SUPER_ADMIN
from ..services import settings as settings_svc

router = APIRouter(prefix="/ai", tags=["ai"])

# 每日配额 key（0 = 不限制；管理员豁免）
QUOTA_KEY = "ai.daily_quota"
DEFAULT_QUOTA = 10


async def _today_usage_count(db: AsyncSession, uid: str) -> int:
    """今日（UTC 零点起）该用户的 AI 调用次数"""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return (
        await db.execute(
            select(func.count()).select_from(AiHistory).where(
                AiHistory.uid == uid, AiHistory.created_time >= today_start
            )
        )
    ).scalar_one() or 0


async def _quota_of(db: AsyncSession) -> int:
    raw = await settings_svc.get_setting(db, QUOTA_KEY, default=str(DEFAULT_QUOTA))
    try:
        return int(raw)
    except (TypeError, ValueError):
        return DEFAULT_QUOTA


def _is_admin(user: User) -> bool:
    return bool(user.role and user.role.name in (ROLE_ADMIN, ROLE_SUPER_ADMIN))


async def _get_own_conv(db: AsyncSession, uid: str, cid: str) -> Conversation:
    """获取当前用户自己的会话，否则 404"""
    conv = await db.get(Conversation, cid)
    if conv is None or conv.uid != uid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    return conv


MOCK_REASONING = "（演示思考过程）用户的问题是技术类提问。我将拆解问题、检索相关知识、组织语言回答。"


def _mock_answer(question: str) -> str:
    return (
        "（Mock 模式回复）我已收到你的问题：\n\n"
        f"「{question[:80]}」\n\n"
        "> 当前未配置 AI_API_KEY，系统运行在演示模式。\n\n"
        "**在 `.env` 或后台「AI 配置」中填入密钥后**，即可接入真实大模型，并获得流式输出与深度思考能力。\n\n"
        "```python\n# 示例：配置后你将收到\nprint('Hello Harness ✨')\n```\n\n"
        "支持 **Markdown**、`行内代码`、$E=mc^2$ 与 $$\\frac{1}{2}+\\frac{1}{3}=\\frac{5}{6}$$ 渲染。"
    )


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


async def _call_ai_real_stream(
    question: str, model: str, reasoning: bool, db: AsyncSession
) -> AsyncGenerator[tuple[str, str], None]:
    """调用 OpenAI 兼容接口流式输出，yield (type, content)，type ∈ {reasoning, content}"""
    cfg = await settings_svc.get_ai_config(db)
    eff = settings_svc.ai_effective(cfg)
    if not settings_svc.ai_configured(cfg):
        return

    url = f"{eff['base_url'].rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {eff['api_key']}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": question}],
        "temperature": 0.7,
        "stream": True,
    }
    if reasoning:
        # 部分兼容接口支持 thinking 参数；不强制，reasoner 模型本身会输出 reasoning_content
        payload["reasoning_effort"] = "medium"

    try:
        async with httpx.AsyncClient(timeout=180) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                if resp.status_code != 200:
                    body = (await resp.aread()).decode("utf-8", "ignore")[:300]
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"AI 服务返回 {resp.status_code}: {body}",
                    )
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    choices = chunk.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    reasoning_content = delta.get("reasoning_content")
                    if reasoning_content:
                        yield "reasoning", reasoning_content
                    content = delta.get("content")
                    if content:
                        yield "content", content
    except httpx.HTTPError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"AI 服务调用失败: {e}")


async def _stream_generator(
    payload: AiChatRequest,
    current_user: User,
    db: AsyncSession,
    conv: Conversation,
) -> AsyncGenerator[str, None]:
    """SSE 生成器：流式输出 + 结束后保存历史（挂会话）"""
    full_answer: list[str] = []
    model_used = "mock"

    cfg = await settings_svc.get_ai_config(db)
    eff = settings_svc.ai_effective(cfg)
    configured = settings_svc.ai_configured(cfg)

    if not configured:
        # Mock 流式：模拟思考 + 分块输出
        model_used = "mock"
        if payload.reasoning:
            for i in range(0, len(MOCK_REASONING), 12):
                yield _sse({"type": "reasoning", "content": MOCK_REASONING[i : i + 12]})
                await asyncio.sleep(0.02)
        text = _mock_answer(payload.question)
        for i in range(0, len(text), 8):
            chunk = text[i : i + 8]
            full_answer.append(chunk)
            yield _sse({"type": "content", "content": chunk})
            await asyncio.sleep(0.015)
    else:
        model_used = eff["model"]
        if payload.reasoning:
            # 深度思考：切换到 reasoner 模型
            model_used = await settings_svc.get_setting(db, "ai.reasoner_model", default="deepseek-reasoner")
        try:
            async for etype, chunk in _call_ai_real_stream(payload.question, model_used, payload.reasoning, db):
                if etype == "content":
                    full_answer.append(chunk)
                yield _sse({"type": etype, "content": chunk})
        except HTTPException:
            yield _sse({"type": "error", "content": "AI 服务调用失败，请检查后台 AI 配置"})
            return

    answer = "".join(full_answer)
    # 保存历史（挂会话）
    history = AiHistory(
        uid=current_user.uid,
        conversation_id=conv.id,
        question=payload.question,
        answer=answer,
        model=model_used,
    )
    db.add(history)
    conv.updated_time = datetime.now(timezone.utc)
    await db.commit()

    yield _sse(
        {"type": "done", "model": model_used, "conversation_id": conv.id, "title": conv.title}
    )


@router.get("/usage", summary="今日 AI 用量与每日配额")
async def usage(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return {
        "today_count": await _today_usage_count(db, current_user.uid),
        "quota": await _quota_of(db),
        "unlimited": _is_admin(current_user),
    }


@router.get("/conversations", response_model=ConversationList, summary="会话列表（按最近使用排序）")
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    convs = (
        (
            await db.execute(
                select(Conversation)
                .where(Conversation.uid == current_user.uid)
                .order_by(Conversation.updated_time.desc())
            )
        )
        .scalars()
        .all()
    )
    counts: dict[str, int] = {}
    if convs:
        rows = await db.execute(
            select(AiHistory.conversation_id, func.count())
            .where(AiHistory.conversation_id.in_([c.id for c in convs]))
            .group_by(AiHistory.conversation_id)
        )
        counts = dict(rows.all())
    items = []
    for c in convs:
        out = ConversationOut.model_validate(c)
        out.message_count = counts.get(c.id, 0)
        items.append(out)
    return ConversationList(items=items, total=len(items))


@router.post("/conversations", response_model=ConversationOut, summary="新建会话")
async def create_conversation(
    payload: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv = Conversation(uid=current_user.uid, title=payload.title or "新对话")
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return ConversationOut.model_validate(conv)


@router.put("/conversations/{cid}", response_model=ConversationOut, summary="重命名会话")
async def rename_conversation(
    cid: str,
    payload: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv = await _get_own_conv(db, current_user.uid, cid)
    conv.title = payload.title
    await db.commit()
    await db.refresh(conv)
    return ConversationOut.model_validate(conv)


@router.delete("/conversations/{cid}", status_code=status.HTTP_204_NO_CONTENT, summary="删除会话及其历史")
async def delete_conversation(
    cid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_own_conv(db, current_user.uid, cid)
    await db.execute(delete(AiHistory).where(AiHistory.conversation_id == cid))
    await db.execute(delete(Conversation).where(Conversation.id == cid))
    await db.commit()


@router.post("/chat", response_model=AiChatResponse)
async def chat(
    payload: AiChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 免费额度校验（管理员豁免；quota=0 表示不限制）
    if not _is_admin(current_user):
        quota = await _quota_of(db)
        if quota > 0 and await _today_usage_count(db, current_user.uid) >= quota:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"今日免费额度已用完（{quota} 次/天），请明天再试，或联系管理员提升额度",
            )

    # 会话解析：指定会话则校验归属；未指定则自动新建（首句自动标题）
    if payload.conversation_id:
        conv = await _get_own_conv(db, current_user.uid, payload.conversation_id)
    else:
        title = payload.question[:24] + ("…" if len(payload.question) > 24 else "")
        conv = Conversation(uid=current_user.uid, title=title)
        db.add(conv)
        await db.flush()

    # 流式模式
    if payload.stream:
        return StreamingResponse(
            _stream_generator(payload, current_user, db, conv),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # 非流式：调用真实模型（带 reasoning 支持）或 mock
    cfg = await settings_svc.get_ai_config(db)
    eff = settings_svc.ai_effective(cfg)
    configured = settings_svc.ai_configured(cfg)

    if not configured:
        answer = _mock_answer(payload.question)
        model = "mock"
    else:
        model = eff["model"]
        if payload.reasoning:
            model = await settings_svc.get_setting(db, "ai.reasoner_model", default="deepseek-reasoner")
        collected: list[str] = []
        async for etype, chunk in _call_ai_real_stream(payload.question, model, payload.reasoning, db):
            if etype == "content":
                collected.append(chunk)
        answer = "".join(collected)

    history = AiHistory(
        uid=current_user.uid,
        conversation_id=conv.id,
        question=payload.question,
        answer=answer,
        model=model,
    )
    db.add(history)
    conv.updated_time = datetime.now(timezone.utc)
    await db.commit()
    return AiChatResponse(answer=answer, model=model)


@router.get("/models", response_model=list[str])
async def list_models(db: AsyncSession = Depends(get_db)):
    cfg = await settings_svc.get_ai_config(db)
    eff = settings_svc.ai_effective(cfg)
    if settings_svc.ai_configured(cfg):
        return [eff["model"]]
    return ["mock"]


@router.delete("/history/last", status_code=status.HTTP_204_NO_CONTENT, summary="删除会话最后一条问答（重新生成/编辑重发）")
async def delete_last_history(
    conversation_id: str = Query(..., max_length=36),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_own_conv(db, current_user.uid, conversation_id)
    row = (
        await db.execute(
            select(AiHistory)
            .where(AiHistory.conversation_id == conversation_id)
            .order_by(AiHistory.created_time.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if row is not None:
        await db.delete(row)
        await db.commit()


@router.get("/history", response_model=AiHistoryList)
async def history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    conversation_id: str | None = Query(default=None, max_length=36),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    base = select(AiHistory).where(AiHistory.uid == current_user.uid)
    if conversation_id:
        # 归属校验：非本人会话返回空
        try:
            conv = await db.get(Conversation, conversation_id)
        except Exception:
            conv = None
        if conv is None or conv.uid != current_user.uid:
            return AiHistoryList(items=[], total=0)
        base = base.where(AiHistory.conversation_id == conversation_id)
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()

    result = await db.execute(
        base.order_by(AiHistory.created_time.desc()).limit(limit).offset(offset)
    )
    items = result.scalars().all()
    return AiHistoryList(items=[AiHistoryItem.model_validate(i) for i in items], total=total)
