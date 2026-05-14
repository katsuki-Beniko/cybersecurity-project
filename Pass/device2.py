"""
Device 2 - Monitor Station (Smart Factory Floor)
PASS version: subscribes to sensor data + public topic + command topic.
Prints all received messages including public sub-topic info.
"""

import paho.mqtt.client as mqtt
import json
from datetime import datetime

# ─── CONFIG ───────────────────────────────────────────────────────────────────
BROKER      = "127.0.0.1"        # change to 192.168.12.100 for lab demo
PORT        = 1883
STUDENT_ID  = "123456789"        # replace with your actual student ID
USERNAME    = STUDENT_ID
PASSWORD    = STUDENT_ID

# Topics this device SUBSCRIBES to
TOPIC_SENSORS  = f"{STUDENT_ID}/sensors/#"        # receives sensor data from Device 1
TOPIC_COMMANDS = f"{STUDENT_ID}/commands/device2" # receives commands (e.g. from MQTTX)
TOPIC_PUBLIC   = "public/#"                        # receives all public messages
# ──────────────────────────────────────────────────────────────────────────────


def on_connect(client, userdata, flags, reason_code, _properties):
    if reason_code == 0:
        print("[Device 2] Connected to MQTT Broker successfully!")
        client.subscribe(TOPIC_SENSORS)
        client.subscribe(TOPIC_COMMANDS)
        client.subscribe(TOPIC_PUBLIC)
        print(f"[Device 2] Subscribed to sensors  : {TOPIC_SENSORS}")
        print(f"[Device 2] Subscribed to commands : {TOPIC_COMMANDS}")
        print(f"[Device 2] Subscribed to public   : {TOPIC_PUBLIC}")
        print("-" * 60)
        print("[Device 2] Waiting for messages...\n")
    else:
        print(f"[Device 2] Connection failed. Return code: {reason_code}")


def on_message(client, userdata, msg):
    topic   = msg.topic
    payload = msg.payload.decode()
    ts      = datetime.now().strftime("%H:%M:%S")

    if topic.startswith("public/"):
        print(f"[{ts}] [PUBLIC]   topic={topic}")
        print(f"         message={payload}")

    elif topic == TOPIC_COMMANDS:
        print(f"[{ts}] [COMMAND RECEIVED]  topic={topic}")
        print(f"         Action: {payload}")

    else:
        try:
            data = json.loads(payload)
            print(f"[{ts}] [SENSOR DATA]  topic={topic}")
            print(f"         device={data.get('device')}  "
                  f"value={data.get('value')}{data.get('unit')}  "
                  f"time={data.get('timestamp')}")
        except (json.JSONDecodeError, KeyError):
            print(f"[{ts}] [SENSOR DATA]  topic={topic}  raw={payload}")


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(USERNAME, PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"[Device 2] Connecting to broker at {BROKER}:{PORT} ...")
    client.connect(BROKER, PORT, keepalive=60)

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n[Device 2] Shutting down...")
        client.disconnect()


if __name__ == "__main__":
    main()
