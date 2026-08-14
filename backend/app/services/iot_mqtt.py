"""MQTT 遥测订阅：harness/{device_id}/telemetry → 校验 token → 入库 → WebSocket 广播"""
import asyncio
import json
import logging
from datetime import datetime, timezone

import aiomqtt

from ..config import settings
from ..database import SessionLocal
from ..models import Device, DeviceTelemetry
from .ws_manager import manager

logger = logging.getLogger("iot.mqtt")
_RETRY_DELAY = 5


async def _handle_message(message: aiomqtt.Message) -> None:
    """处理一条遥测消息"""
    topic = message.topic.value
    parts = topic.split("/")
    if len(parts) < 3:
        return
    device_id = parts[1]
    try:
        body = json.loads(message.payload.decode("utf-8", errors="ignore"))
    except (ValueError, UnicodeDecodeError):
        return
    token = body.get("token")
    data = body.get("data")
    if not token or not isinstance(data, dict):
        return

    now = datetime.now(timezone.utc)
    async with SessionLocal() as db:
        device = await db.get(Device, device_id)
        if device is None or device.token != token:
            logger.warning("mqtt 遥测被拒绝: device=%s token 不匹配", device_id)
            return
        db.add(DeviceTelemetry(device_id=device.id, payload=json.dumps(data, ensure_ascii=False)))
        device.last_seen = now
        await db.commit()

    await manager.broadcast(
        device.uid,
        {
            "type": "telemetry",
            "device_id": device.id,
            "payload": data,
            "created_time": now.isoformat(),
        },
    )


async def mqtt_worker() -> None:
    """后台常驻任务：断线自动重连（broker 可能晚于后端启动）"""
    while True:
        try:
            async with aiomqtt.Client(settings.MQTT_HOST, port=settings.MQTT_PORT) as client:
                topic = f"{settings.MQTT_TOPIC_PREFIX}/+/telemetry"
                await client.subscribe(topic)
                logger.info("MQTT 已订阅 %s @ %s:%s", topic, settings.MQTT_HOST, settings.MQTT_PORT)
                async for message in client.messages:
                    try:
                        await _handle_message(message)
                    except Exception:
                        logger.exception("处理 MQTT 消息失败")
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("MQTT 连接断开，%ss 后重试", _RETRY_DELAY)
            await asyncio.sleep(_RETRY_DELAY)
