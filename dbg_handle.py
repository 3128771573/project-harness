import asyncio, sys
sys.path.insert(0, "/app/backend")
from datetime import datetime, timezone
from app.database import SessionLocal
from app.models import Report, User
from sqlalchemy import select
from app.services.audit import record_audit
from app.services.bot import ensure_bot, send_bot_dm

async def main():
    async with SessionLocal() as db:
        # 造一个 pending 举报（目标 bob 或任意用户）
        u = (await db.execute(select(User).where(User.is_bot.is_(False)).limit(1))).scalars().first()
        rep = Report(reporter_id=u.uid, target_type="dm", target_id="fake-target-id", reason="调试", status="pending")
        db.add(rep)
        await db.commit()
        await db.refresh(rep)
        rep.status = "handled"
        rep.handled_by = "test"
        rep.handled_at = datetime.now(timezone.utc)
        await db.commit()
        await record_audit(db, actor=None, action="im.report_handle", resource=f"report:{rep.id}", detail="debug")
        try:
            bot = await ensure_bot(db)
            await send_bot_dm(db, rep.reporter_id, "【举报处理结果】调试消息")
            print("SIMULATE OK, reporter:", u.email)
        except Exception:
            import traceback
            traceback.print_exc()
        # 清理
        await db.delete(rep)
        await db.commit()

asyncio.run(main())
