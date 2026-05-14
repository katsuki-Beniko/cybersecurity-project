"""
Device 1 - Sensor Node (Smart Factory Floor)
DISTINCTION version (User 1):
  - Publishes temperature + humidity to PRIVATE topic
  - Publishes temperature alerts to PUBLIC Topic 1
  - Subscribes to PUBLIC Topic 2 (maintenance alerts from Device 2)
  - Subscribes to command topic
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

# Private topics (Device 1 publishes)
TOPIC_TEMP     = f"{STUDENT_ID}/sensors/temperature"
TOPIC_HUMIDITY = f"{STUDENT_ID}/sensors/humidity"

# Public Topic 1 — Device 1 publishes temperature alerts here
TOPIC_PUBLIC_1 = f"public/{STUDENT_ID}/alerts/temperature"

# Public Topic 2 — Device 2 publishes here, Device 1 subscribes
TOPIC_PUBLIC_2 = f"public/{STUDENT_ID}/alerts/maintenance"

# Command topic — UI client sends commands to Device 1
TOPIC_COMMANDS = f"{STUDENT_ID}/commands/device1"

TEMP_ALERT_THRESHOLD = 35.0   # degrees C — publish alert if exceeded
# ──────────────────────────────────────────────────────────────────────────────


def on_connect(client, userdata, flags, reason_code, _properties):
    if reason_code == 0:
        print("[Device 1] Connected to MQTT Broker successfully!")
        client.subscribe("public/#")
        client.subscribe(TOPIC_COMMANDS)
        print(f"[Device 1] Subscribed to public (all)   : public/#")
        print(f"[Device 1] Responds specifically to     : {TOPIC_PUBLIC_2}")
        print(f"[Device 1] Subscribed to commands       : {TOPIC_COMMANDS}")
        print("-" * 60)
    else:
        print(f"[Device 1] Connection failed. Return code: {reason_code}")


def on_message(client, userdata, msg):
    topic   = msg.topic
    payload = msg.payload.decode()
    ts      = datetime.now().strftime("%H:%M:%S")

    if topic == TOPIC_PUBLIC_2:
        print(f"[{ts}] [PUBLIC TOPIC 2 - MAINTENANCE] topic={topic}")
        print(f"         Message: {payload}")
    elif topic.startswith("public/"):
        print(f"[{ts}] [PUBLIC] topic={topic}")
        print(f"         Message: {payload}")
    elif topic == TOPIC_COMMANDS:
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

            # Publish to PRIVATE topics
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
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [PRIVATE PUBLISHED]"
                  f"  Temp={temperature}°C  Humidity={humidity}%")

            # Publish alert to PUBLIC Topic 1 if temperature exceeds threshold
            if temperature > TEMP_ALERT_THRESHOLD:
                alert = json.dumps({
                    "device": "Device1",
                    "alert": "HIGH_TEMPERATURE",
                    "value": temperature,
                    "unit": "C",
                    "timestamp": ts
                })
                client.publish(TOPIC_PUBLIC_1, alert)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [PUBLIC TOPIC 1 PUBLISHED]"
                      f"  ALERT: High temp {temperature}°C")

            time.sleep(5)

    except KeyboardInterrupt:
        print("\n[Device 1] Shutting down...")
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
