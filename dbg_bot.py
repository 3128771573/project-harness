import asyncio, sys
sys.path.insert(0, "/app/backend")
from app.database import SessionLocal
from app.services.bot import ensure_bot, send_bot_dm
from sqlalchemy import select
from app.models import User

async def main():
    async with SessionLocal() as db:
        bot = await ensure_bot(db)
        u = (await db.execute(select(User).where(User.email == "superadmin@platformharness.ltd"))).scalar_one()
        try:
            msg = await send_bot_dm(db, bot, u.uid, "调试：测试发送")
            print("SEND OK:", msg.id)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print("SEND FAIL:", type(e).__name__, str(e)[:300])

asyncio.run(main())
