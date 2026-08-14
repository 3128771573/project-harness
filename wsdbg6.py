import asyncio, sys
sys.path.insert(0, "/app/backend")
import httpx
from starlette.testclient import TestClient
from app.main import app
from app.routers import im as im_mod

async def main():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as lc:
        r = await lc.post("/api/v1/auth/send-code", json={"email": "ws-dbg6@example.com", "purpose": "register"})
        code = r.json().get("dev_code")
        r = await lc.post("/api/v1/auth/register", json={"username": "wsdbguser6", "email": "ws-dbg6@example.com", "password": "TestPass123", "code": code})
        token = r.json()["access_token"]

    orig_decode = im_mod.decode_token
    def wrap(tok):
        res = orig_decode(tok)
        print("  [handler] decode_token ->", res)
        return res
    im_mod.decode_token = wrap

    orig_get = im_mod.SessionLocal
    # 直接调用 handler 逻辑分支不便；改为打印 close
    with TestClient(app) as tc:
        try:
            with tc.websocket_connect(f"/api/v1/im/ws?token={token}") as ws:
                print("CONNECTED")
        except Exception as e:
            print("DISCONNECT:", type(e).__name__, repr(str(e))[:300])
asyncio.run(main())
