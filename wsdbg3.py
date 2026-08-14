import asyncio, json, sys
sys.path.insert(0, "/app/backend")
import httpx

async def main():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as lc:
        r = await lc.post("/api/v1/auth/send-code", json={"email": "ws-dbg3@example.com", "purpose": "register"})
        code = r.json().get("dev_code")
        r = await lc.post("/api/v1/auth/register", json={"username": "wsdbguser3", "email": "ws-dbg3@example.com", "password": "TestPass123", "code": code})
        token = r.json()["access_token"]
        import websockets
        # iot ws 对照
        try:
            async with websockets.connect(f"ws://127.0.0.1:8000/api/v1/iot/ws?token={token}", origin="https://www.platformharness.ltd") as ws:
                print("IOT-WS: CONNECTED")
                await ws.send("ping")
        except Exception as e:
            print("IOT-WS:", type(e).__name__, str(e)[:200])
        # im ws
        try:
            async with websockets.connect(f"ws://127.0.0.1:8000/api/v1/im/ws?token={token}", origin="https://www.platformharness.ltd") as ws:
                print("IM-WS: CONNECTED")
        except Exception as e:
            print("IM-WS:", type(e).__name__, str(e)[:200])
asyncio.run(main())
