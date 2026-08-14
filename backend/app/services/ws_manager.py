"""WebSocket 连接管理：按「房间」广播实时事件（uid 房间 + 会话/群房间）"""
import json

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # room -> set[WebSocket]
        self._rooms: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room: str):
        """接受连接并加入房间（兼容旧调用：iot 传入 uid 即用户房间）"""
        await websocket.accept()
        self._rooms.setdefault(room, set()).add(websocket)

    def disconnect(self, websocket: WebSocket, room: str):
        room_set = self._rooms.get(room)
        if room_set:
            room_set.discard(websocket)
            if not room_set:
                self._rooms.pop(room, None)

    def join(self, websocket: WebSocket, room: str):
        """已连接的 socket 额外加入一个房间（如当前打开的会话房间）"""
        self._rooms.setdefault(room, set()).add(websocket)

    def leave(self, websocket: WebSocket, room: str):
        self.disconnect(websocket, room)

    async def broadcast(self, room: str, message: dict):
        """向房间所有连接广播 JSON；失效连接静默移除"""
        room_set = self._rooms.get(room)
        if not room_set:
            return
        text = json.dumps(message, ensure_ascii=False)
        dead: list[WebSocket] = []
        for ws in list(room_set):
            try:
                await ws.send_text(text)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, room)


manager = ConnectionManager()
