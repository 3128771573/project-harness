"""WebSocket 连接管理：按「房间」广播实时事件（uid 房间 + 会话/群房间）+ 每用户连接上限"""
import json

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # room -> set[WebSocket]
        self._rooms: dict[str, set[WebSocket]] = {}
        # uid -> set[WebSocket]（每用户连接上限，安全基线 §2.7）
        self._user_conns: dict[str, set[WebSocket]] = {}
        self.MAX_CONNS_PER_USER = 5

    def _track(self, websocket: WebSocket, uid: str):
        self._user_conns.setdefault(uid, set()).add(websocket)

    def _untrack(self, websocket: WebSocket, uid: str):
        conns = self._user_conns.get(uid)
        if conns:
            conns.discard(websocket)
            if not conns:
                self._user_conns.pop(uid, None)

    async def connect(self, websocket: WebSocket, room: str, uid: str | None = None):
        """接受连接并加入房间；uid 提供时执行每用户连接上限（超限关闭 1013）"""
        if uid is not None and len(self._user_conns.get(uid, set())) >= self.MAX_CONNS_PER_USER:
            await websocket.close(code=1013)  # try again later
            return False
        await websocket.accept()
        self._rooms.setdefault(room, set()).add(websocket)
        if uid is not None:
            self._track(websocket, uid)
        return True

    def disconnect(self, websocket: WebSocket, room: str | None = None, uid: str | None = None):
        if room is not None:
            room_set = self._rooms.get(room)
            if room_set:
                room_set.discard(websocket)
                if not room_set:
                    self._rooms.pop(room, None)
        if uid is not None:
            self._untrack(websocket, uid)

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
