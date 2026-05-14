"""
Device 2 - Maintenance Node (Smart Factory Floor)
DISTINCTION version (User 2):
  - Publishes maintenance alerts to PUBLIC Topic 2
  - Subscribes to PUBLIC Topic 1 (temperature alerts from Device 1)
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

# Public Topic 1 — Device 1 publishes here, Device 2 subscribes
TOPIC_PUBLIC_1 = f"public/{STUDENT_ID}/alerts/temperature"

# Public Topic 2 — Device 2 publishes maintenance alerts here
TOPIC_PUBLIC_2 = f"public/{STUDENT_ID}/alerts/maintenance"

# Command topic — UI client sends commands to Device 2
TOPIC_COMMANDS = f"{STUDENT_ID}/commands/device2"

MAINTENANCE_INTERVAL = 3   # publish a maintenance status every N cycles
# ──────────────────────────────────────────────────────────────────────────────


def on_connect(client, userdata, flags, reason_code, _properties):
    if reason_code == 0:
        print("[Device 2] Connected to MQTT Broker successfully!")
        client.subscribe("public/#")
        client.subscribe(TOPIC_COMMANDS)
        print(f"[Device 2] Subscribed to public (all)   : public/#")
        print(f"[Device 2] Responds specifically to     : {TOPIC_PUBLIC_1}")
        print(f"[Device 2] Subscribed to commands       : {TOPIC_COMMANDS}")
        print("-" * 60)
        print("[Device 2] Running. Press Ctrl+C to stop.\n")
    else:
        print(f"[Device 2] Connection failed. Return code: {reason_code}")


def on_message(client, userdata, msg):
    topic   = msg.topic
    payload = msg.payload.decode()
    ts      = datetime.now().strftime("%H:%M:%S")

    if topic == TOPIC_PUBLIC_1:
        print(f"[{ts}] [PUBLIC TOPIC 1 - TEMP ALERT] topic={topic}")
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

    print(f"[Device 2] Connecting to broker at {BROKER}:{PORT} ...")
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()

    statuses = ["ALL_SYSTEMS_OK", "FILTER_CHECK_DUE", "BELT_WORN", "LUBRICATION_NEEDED"]
    cycle = 0

    try:
        while True:
            cycle += 1
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Publish maintenance status to PUBLIC Topic 2 every N cycles
            if cycle % MAINTENANCE_INTERVAL == 0:
                status = random.choice(statuses)
                payload = json.dumps({
                    "device": "Device2",
                    "status": status,
                    "machine_id": f"MACHINE_{random.randint(1, 5)}",
                    "timestamp": ts
                })
                client.publish(TOPIC_PUBLIC_2, payload)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [PUBLIC TOPIC 2 PUBLISHED]"
                      f"  Status={status}")

            time.sleep(5)

    except KeyboardInterrupt:
        print("\n[Device 2] Shutting down...")
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
