"""IoT 设备管理 + 遥测接入（HTTP / MQTT 双通道）+ WebSocket 实时推送"""
import json
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import SessionLocal, get_db
from ..deps import get_current_user
from ..models import Device, DeviceTelemetry, User
from ..schemas import DeviceCreate, DeviceList, DeviceOut, DeviceUpdate, TelemetryIn, TelemetryList, TelemetryOut
from ..security import decode_token
from ..services.ws_manager import manager

router = APIRouter(prefix="/iot", tags=["iot"])

# 在线判定阈值（秒）：超过视为离线
ONLINE_WINDOW = 30


def _device_out(device: Device, last_payload: dict | None) -> DeviceOut:
    out = DeviceOut.model_validate(device)
    out.last_payload = last_payload
    return out


async def _latest_payload(db: AsyncSession, device_id: str) -> dict | None:
    row = (
        await db.execute(
            select(DeviceTelemetry.payload)
            .where(DeviceTelemetry.device_id == device_id)
            .order_by(DeviceTelemetry.created_time.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if not row:
        return None
    try:
        return json.loads(row)
    except (ValueError, TypeError):
        return None


async def _get_own_device(db: AsyncSession, uid: str, did: str) -> Device:
    device = await db.get(Device, did)
    if device is None or device.uid != uid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="设备不存在")
    return device


async def _ingest(db: AsyncSession, device: Device, data: dict) -> dict:
    """遥测入库 + 更新 last_seen + 广播（HTTP 与 MQTT 共用）"""
    now = datetime.now(timezone.utc)
    db.add(DeviceTelemetry(device_id=device.id, payload=json.dumps(data, ensure_ascii=False)))
    device.last_seen = now
    await db.commit()
    event = {
        "type": "telemetry",
        "device_id": device.id,
        "payload": data,
        "created_time": now.isoformat(),
    }
    await manager.broadcast(device.uid, event)
    return event


@router.get("/devices", response_model=DeviceList, summary="我的设备列表")
async def list_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Device).where(Device.uid == current_user.uid).order_by(Device.created_time.desc())
    )
    devices = result.scalars().all()
    items = []
    for d in devices:
        items.append(_device_out(d, await _latest_payload(db, d.id)))
    return DeviceList(items=items, total=len(items))


@router.post("/devices", response_model=DeviceOut, summary="注册设备")
async def create_device(
    payload: DeviceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    device = Device(uid=current_user.uid, name=payload.name, token=secrets.token_hex(16))
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return _device_out(device, None)


@router.put("/devices/{did}", response_model=DeviceOut, summary="重命名设备")
async def rename_device(
    did: str,
    payload: DeviceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    device = await _get_own_device(db, current_user.uid, did)
    device.name = payload.name
    await db.commit()
    await db.refresh(device)
    return _device_out(device, await _latest_payload(db, device.id))


@router.delete("/devices/{did}", status_code=status.HTTP_204_NO_CONTENT, summary="删除设备及其遥测")
async def delete_device(
    did: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_own_device(db, current_user.uid, did)
    await db.execute(delete(DeviceTelemetry).where(DeviceTelemetry.device_id == did))
    await db.execute(delete(Device).where(Device.id == did))
    await db.commit()


@router.post("/devices/{did}/token", response_model=DeviceOut, summary="重新生成设备 token")
async def regenerate_token(
    did: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    device = await _get_own_device(db, current_user.uid, did)
    device.token = secrets.token_hex(16)
    await db.commit()
    await db.refresh(device)
    return _device_out(device, await _latest_payload(db, device.id))


@router.post("/devices/{did}/telemetry", status_code=status.HTTP_204_NO_CONTENT, summary="HTTP 上报遥测")
async def http_telemetry(
    did: str,
    payload: TelemetryIn,
    db: AsyncSession = Depends(get_db),
):
    device = await db.get(Device, did)
    if device is None or device.token != payload.token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="设备或 token 无效")
    await _ingest(db, device, payload.data or {})
    return None


@router.get("/devices/{did}/telemetry", response_model=TelemetryList, summary="遥测历史")
async def telemetry_history(
    did: str,
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_own_device(db, current_user.uid, did)
    base = select(DeviceTelemetry).where(DeviceTelemetry.device_id == did)
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    result = await db.execute(
        base.order_by(DeviceTelemetry.created_time.desc()).limit(limit)
    )
    items = result.scalars().all()
    out = []
    for row in reversed(items):
        try:
            payload = json.loads(row.payload)
        except (ValueError, TypeError):
            payload = {}
        out.append(TelemetryOut(id=row.id, device_id=row.device_id, payload=payload, created_time=row.created_time))
    return TelemetryList(items=out, total=total)


@router.websocket("/ws")
async def iot_ws(websocket: WebSocket):
    """实时遥测推送：?token=<access_token>"""
    token = websocket.query_params.get("token")
    uid = None
    if token:
        payload = decode_token(token)
        if payload and payload.get("type") == "access":
            uid = payload.get("sub")
    if not uid:
        await websocket.close(code=4401)
        return
    async with SessionLocal() as db:
        user = await db.get(User, uid)
        if user is None or not user.is_active:
            await websocket.close(code=4401)
            return
    await manager.connect(websocket, uid)
    try:
        while True:
            # 接收客户端消息以检测断开（客户端发空串保活）
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, uid)
    except Exception:
        manager.disconnect(websocket, uid)
