"""WebSocket 连接管理：按用户广播实时事件（IoT 遥测等）"""
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # uid -> set[WebSocket]
        self._rooms: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, uid: str):
        await websocket.accept()
        self._rooms.setdefault(uid, set()).add(websocket)

    def disconnect(self, websocket: WebSocket, uid: str):
        room = self._rooms.get(uid)
        if room:
            room.discard(websocket)
            if not room:
                self._rooms.pop(uid, None)

    async def broadcast(self, uid: str, message: dict):
        """向该用户的所有连接广播 JSON 消息；失效连接静默移除"""
        room = self._rooms.get(uid)
        if not room:
            return
        import json

        text = json.dumps(message, ensure_ascii=False)
        dead: list[WebSocket] = []
        for ws in list(room):
            try:
                await ws.send_text(text)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, uid)


manager = ConnectionManager()
