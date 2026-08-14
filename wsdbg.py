import asyncio, json, sys
sys.path.insert(0, "/app/backend")
import httpx
from app.security import decode_token

async def main():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as lc:
        r = await lc.post("/api/v1/auth/send-code", json={"email": "ws-dbg@example.com", "purpose": "register"})
        code = r.json().get("dev_code")
        print("dev_code:", code)
        if not code:
            # 直接库里取
            from app.database import SessionLocal
            from sqlalchemy import select
            from app.models import EmailCode
            async with SessionLocal() as db:
                row = (await db.execute(select(EmailCode).where(EmailCode.email == "ws-dbg@example.com").order_by(EmailCode.created_time.desc()).limit(1))).scalar_one()
                code = row.code
        r = await lc.post("/api/v1/auth/register", json={"username": "wsdbguser", "email": "ws-dbg@example.com", "password": "TestPass123", "code": code})
        print("register:", r.status_code)
        token = r.json()["access_token"]
        print("token head:", token[:30])
        print("decode in test process:", decode_token(token))
        import websockets
        try:
            async with websockets.connect(f"ws://127.0.0.1:8000/api/v1/im/ws?token={token}") as ws:
                print("WS CONNECTED")
                await ws.send(json.dumps({"type": "ping"}))
        except Exception as e:
            print("WS ERROR:", type(e).__name__, str(e)[:300])
asyncio.run(main())
