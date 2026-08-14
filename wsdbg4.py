import asyncio, sys
sys.path.insert(0, "/app/backend")
import httpx
from app.security import decode_token
from app.database import SessionLocal
from app.models import User

async def main():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as lc:
        r = await lc.post("/api/v1/auth/send-code", json={"email": "ws-dbg4@example.com", "purpose": "register"})
        code = r.json().get("dev_code")
        r = await lc.post("/api/v1/auth/register", json={"username": "wsdbguser4", "email": "ws-dbg4@example.com", "password": "TestPass123", "code": code})
        token = r.json()["access_token"]
        print("token:", token[:40])
        payload = decode_token(token)
        print("decode:", payload)
        async with SessionLocal() as db:
            user = await db.get(User, payload["sub"])
            print("user:", user.username if user else None, "active:", user.is_active if user else None, "bot:", user.is_bot if user else None, "uid:", user.uid if user else None)
        # 直接模拟 handler 的关闭条件
        uid = payload.get("sub") if payload and payload.get("type") == "access" else None
        print("uid:", uid)
asyncio.run(main())
