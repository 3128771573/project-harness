#!/usr/bin/env python3
"""Harness IoT 设备模拟器：向 MQTT 发布温湿度遥测

用法（容器内，与后端同网络）:
    docker run --rm --network harness-net \
      -e MQTT_HOST=mqtt \
      -e DEVICE_ID=<device_id> -e DEVICE_TOKEN=<token> \
      -v <本文件路径>:/sim.py python:3.12-alpine \
      sh -c "pip install paho-mqtt -q && python /sim.py"
"""
import json
import os
import random
import sys
import time

import paho.mqtt.client as mqtt

BROKER = os.environ.get("MQTT_HOST", "mqtt")
PORT = int(os.environ.get("MQTT_PORT", "1883"))
DEVICE_ID = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("DEVICE_ID", "")
TOKEN = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("DEVICE_TOKEN", "")
INTERVAL = float(os.environ.get("INTERVAL", "2"))

if not DEVICE_ID or not TOKEN:
    print("用法: simulate_device.py <device_id> <device_token> 或设置 DEVICE_ID/DEVICE_TOKEN 环境变量")
    sys.exit(1)


def on_connect(client, userdata, flags, rc):
    print(f"已连接 MQTT {BROKER}:{PORT} (rc={rc})")


client = mqtt.Client()
client.on_connect = on_connect
client.connect(BROKER, PORT, 60)
client.loop_start()

temp = 25.0 + random.uniform(-2, 2)
topic = f"harness/{DEVICE_ID}/telemetry"
print(f"发布到 {topic}（Ctrl+C 退出）")
try:
    while True:
        temp += random.uniform(-0.4, 0.4)
        temp = max(15.0, min(38.0, temp))
        payload = {
            "token": TOKEN,
            "data": {
                "temp": round(temp, 2),
                "humidity": round(50 + random.uniform(-6, 6), 1),
            },
        }
        client.publish(topic, json.dumps(payload))
        print(".", end="", flush=True)
        time.sleep(INTERVAL)
except KeyboardInterrupt:
    print()
    print("已停止")
    client.loop_stop()
