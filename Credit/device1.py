"""
Device 1 - Sensor Node (Smart Factory Floor)
CREDIT version: publishes temperature and humidity AND subscribes to commands + public.
"""

import paho.mqtt.client as mqtt
import time
import random
import json
from datetime import datetime

# ─── CONFIG ───────────────────────────────────────────────────────────────────
BROKER      = "127.0.0.1"        # change to 192.168.12.100 for lab demo
PORT        = 1883
STUDENT_ID  = "123456789"        # replace with your actual student ID
USERNAME    = STUDENT_ID
PASSWORD    = STUDENT_ID

# Topics this device PUBLISHES to
TOPIC_TEMP     = f"{STUDENT_ID}/sensors/temperature"
TOPIC_HUMIDITY = f"{STUDENT_ID}/sensors/humidity"

# Topics this device SUBSCRIBES to
TOPIC_COMMANDS = f"{STUDENT_ID}/commands/device1"
TOPIC_PUBLIC   = "public/#"
# ──────────────────────────────────────────────────────────────────────────────


def on_connect(client, userdata, flags, reason_code, _properties):
    if reason_code == 0:
        print("[Device 1] Connected to MQTT Broker successfully!")
        client.subscribe(TOPIC_COMMANDS)
        client.subscribe(TOPIC_PUBLIC)
        print(f"[Device 1] Subscribed to commands : {TOPIC_COMMANDS}")
        print(f"[Device 1] Subscribed to public   : {TOPIC_PUBLIC}")
        print("-" * 60)
    else:
        print(f"[Device 1] Connection failed. Return code: {reason_code}")


def on_message(client, userdata, msg):
    topic   = msg.topic
    payload = msg.payload.decode()
    ts      = datetime.now().strftime("%H:%M:%S")

    if topic.startswith("public/"):
        print(f"[{ts}] [PUBLIC]  topic={topic}  msg={payload}")
    else:
        print(f"[{ts}] [COMMAND RECEIVED] topic={topic}")
        print(f"         Action: {payload}")


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(USERNAME, PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"[Device 1] Connecting to broker at {BROKER}:{PORT} ...")
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()

    print("[Device 1] Sensor simulation running. Press Ctrl+C to stop.\n")
    try:
        while True:
            temperature = round(random.uniform(18.0, 40.0), 2)
            humidity    = round(random.uniform(30.0, 85.0), 2)
            ts          = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            temp_payload = json.dumps({
                "device": "Device1",
                "value": temperature,
                "unit": "C",
                "timestamp": ts
            })
            hum_payload = json.dumps({
                "device": "Device1",
                "value": humidity,
                "unit": "%",
                "timestamp": ts
            })

            client.publish(TOPIC_TEMP, temp_payload)
            client.publish(TOPIC_HUMIDITY, hum_payload)

            print(f"[{datetime.now().strftime('%H:%M:%S')}] [PUBLISHED]"
                  f"  Temp={temperature}°C  Humidity={humidity}%")
            time.sleep(5)

    except KeyboardInterrupt:
        print("\n[Device 1] Shutting down...")
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
