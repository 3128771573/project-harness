import asyncio, sys
sys.path.insert(0, "/app/backend")
import httpx
from starlette.testclient import TestClient
from app.main import app

async def main():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as lc:
        r = await lc.post("/api/v1/auth/send-code", json={"email": "ws-dbg5@example.com", "purpose": "register"})
        code = r.json().get("dev_code")
        r = await lc.post("/api/v1/auth/register", json={"username": "wsdbguser5", "email": "ws-dbg5@example.com", "password": "TestPass123", "code": code})
        token = r.json()["access_token"]
    with TestClient(app) as tc:
        try:
            with tc.websocket_connect(f"/api/v1/im/ws?token={token}") as ws:
                print("TESTCLIENT: CONNECTED")
        except Exception as e:
            print("TESTCLIENT-IM:", type(e).__name__, str(e)[:200])
        try:
            with tc.websocket_connect(f"/api/v1/iot/ws?token={token}") as ws:
                print("TESTCLIENT-IOT: CONNECTED")
        except Exception as e:
            print("TESTCLIENT-IOT:", type(e).__name__, str(e)[:200])
asyncio.run(main())
