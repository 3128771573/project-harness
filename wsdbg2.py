import asyncio, json, sys
sys.path.insert(0, "/app/backend")
import httpx

async def main():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as lc:
        r = await lc.post("/api/v1/auth/send-code", json={"email": "ws-dbg2@example.com", "purpose": "register"})
        code = r.json().get("dev_code")
        r = await lc.post("/api/v1/auth/register", json={"username": "wsdbguser2", "email": "ws-dbg2@example.com", "password": "TestPass123", "code": code})
        token = r.json()["access_token"]
        import websockets
        url = f"ws://127.0.0.1:8000/api/v1/im/ws?token={token}"
        # 尝试1：无 Origin 头
        try:
            async with websockets.connect(url, origin=None) as ws:
                print("NO-ORIGIN: CONNECTED")
        except Exception as e:
            print("NO-ORIGIN:", type(e).__name__, str(e)[:150])
        # 尝试2：Origin = http://localhost:8080
        try:
            async with websockets.connect(url, origin="http://localhost:8080") as ws:
                print("LOCALHOST-8080: CONNECTED")
        except Exception as e:
            print("LOCALHOST-8080:", type(e).__name__, str(e)[:150])
        # 尝试3：Origin = https://www.platformharness.ltd
        try:
            async with websockets.connect(url, origin="https://www.platformharness.ltd") as ws:
                print("PLH: CONNECTED")
        except Exception as e:
            print("PLH:", type(e).__name__, str(e)[:150])
asyncio.run(main())
