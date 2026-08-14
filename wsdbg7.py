import sys
sys.path.insert(0, "/app/backend")
from app.main import app
from starlette.routing import WebSocketRoute
print("=== WebSocket 路由 ===")
for r in app.routes:
    if isinstance(r, WebSocketRoute):
        print("WS:", r.path, "->", getattr(r, "endpoint", None))
print("=== /api/v1/im 前缀 HTTP 路由数 ===")
n = [r.path for r in app.routes if isinstance(r, WebSocketRoute)]
print(len(n))
