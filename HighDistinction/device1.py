"""
Device 1 - Sensor Node (Smart Factory Floor)
PROFESSIONAL HIGH DISTINCTION version:
  - Publishes temperature, humidity AND vibration telemetry to private topic
  - Publishes temperature alerts to PUBLIC Topic 1 when threshold exceeded
  - Subscribes to public/# (all public messages — Credit requirement)
  - Sends heartbeat every 30 seconds
  - Acknowledges every received command and responds accordingly
"""

import paho.mqtt.client as mqtt
import time
import random
import json
import threading
from datetime import datetime
from config import *

_cooling_active = False
_active         = True


def on_connect(client, userdata, flags, reason_code, _properties):
    if reason_code == 0:
        print("[Device 1] Connected to MQTT Broker successfully!")
        client.subscribe("public/#")
        client.subscribe(TOPIC_CMD_D1)
        print(f"[Device 1] Subscribed to public (all)       : public/#")
        print(f"[Device 1] Responds specifically to         : {TOPIC_PUBLIC_2}")
        print(f"[Device 1] Subscribed to commands           : {TOPIC_CMD_D1}")
        print("-" * 60)
    else:
        print(f"[Device 1] Connection failed. Code: {reason_code}")


def on_message(client, userdata, msg):
    global _cooling_active, _active
    topic   = msg.topic
    payload = msg.payload.decode()
    ts      = datetime.now().strftime("%H:%M:%S")

    if topic == TOPIC_CMD_D1:
        try:
            data   = json.loads(payload)
            action = data.get("action", payload)
        except json.JSONDecodeError:
            action = payload

        print(f"[{ts}] [COMMAND RECEIVED]  action={action}")

        # Acknowledge command back to UI
        ack = json.dumps({
            "device":    "Device1",
            "action":    action,
            "status":    "ACKNOWLEDGED",
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        })
        client.publish(TOPIC_D1_ACK, ack)

        if action == "ACTIVATE":
            _active = True
            print(f"[{ts}]   → Device ACTIVATED — resuming telemetry")
        elif action == "DEACTIVATE":
            _active = False
            print(f"[{ts}]   → Device DEACTIVATED — telemetry paused")
        elif action == "ACTIVATE_COOLING":
            _cooling_active = True
            print(f"[{ts}]   → Cooling system ACTIVATED")
        elif action == "DEACTIVATE_COOLING":
            _cooling_active = False
            print(f"[{ts}]   → Cooling system DEACTIVATED")
        elif action == "EMERGENCY_COOLING":
            _cooling_active = True
            print(f"[{ts}]   → EMERGENCY COOLING ACTIVATED")
        elif action == "STATUS":
            print(f"[{ts}]   → Active: {_active}  Cooling: {_cooling_active}")

    elif topic == TOPIC_PUBLIC_2:
        try:
            data     = json.loads(payload)
            status   = data.get("status", payload)
            priority = data.get("priority", "")
            machine  = data.get("machine_id", "")
            print(f"[{ts}] [TOPIC 2 - MAINTENANCE]  status={status}  priority={priority}  machine={machine}")
        except json.JSONDecodeError:
            print(f"[{ts}] [TOPIC 2 - MAINTENANCE]  {payload}")

    elif topic.startswith("public/"):
        print(f"[{ts}] [PUBLIC]  topic={topic}")
        print(f"         Message: {payload}")


def _heartbeat_loop(client):
    while True:
        payload = json.dumps({
            "device":    "Device1",
            "status":    "online",
            "active":    _active,
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        })
        client.publish(TOPIC_D1_HEARTBEAT, payload)
        time.sleep(HEARTBEAT_INTERVAL)


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(USERNAME, PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"[Device 1] Connecting to broker at {BROKER}:{PORT} ...")
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()

    # Heartbeat in background thread
    threading.Thread(target=_heartbeat_loop, args=(client,), daemon=True).start()

    print("[Device 1] Sensor simulation running. Press Ctrl+C to stop.\n")
    try:
        while True:
            if _active:
                temperature = round(random.uniform(18.0, 42.0), 2)
                humidity    = round(random.uniform(30.0, 85.0), 2)
                vibration   = round(random.uniform(0.1, 5.0), 3)
                ts_iso      = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

                # Full telemetry to private topic
                telemetry = json.dumps({
                    "device":      "Device1",
                    "temperature": temperature,
                    "humidity":    humidity,
                    "vibration":   vibration,
                    "cooling":     _cooling_active,
                    "timestamp":   ts_iso,
                })
                client.publish(TOPIC_D1_TELEMETRY, telemetry)

                # Individual sensor topics (used by UI for AI processing)
                client.publish(
                    f"{STUDENT_ID}/sensors/temperature",
                    json.dumps({"device": "Device1", "sensor": "temperature",
                                "value": temperature, "unit": "C", "timestamp": ts_iso})
                )
                client.publish(
                    f"{STUDENT_ID}/sensors/humidity",
                    json.dumps({"device": "Device1", "sensor": "humidity",
                                "value": humidity, "unit": "%", "timestamp": ts_iso})
                )
                client.publish(
                    f"{STUDENT_ID}/sensors/vibration",
                    json.dumps({"device": "Device1", "sensor": "vibration",
                                "value": vibration, "unit": "mm/s", "timestamp": ts_iso})
                )

                print(f"[{datetime.now().strftime('%H:%M:%S')}] [TELEMETRY]"
                      f"  Temp={temperature}°C  Hum={humidity}%"
                      f"  Vib={vibration}mm/s  Cooling={'ON' if _cooling_active else 'OFF'}")

                # Temperature alert to public Topic 1
                if temperature > TEMP_ALERT_THRESHOLD:
                    alert = json.dumps({
                        "device":    "Device1",
                        "alert":     "HIGH_TEMPERATURE",
                        "value":     temperature,
                        "unit":      "C",
                        "timestamp": ts_iso,
                    })
                    client.publish(TOPIC_PUBLIC_1, alert)

                    # Sanitised public log
                    client.publish(TOPIC_PUBLIC_LOG, json.dumps({
                        "device":    "Device1",
                        "event":     "TEMPERATURE_ALERT",
                        "value":     temperature,
                        "timestamp": ts_iso,
                    }))
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] [PUBLIC ALERT → Topic 1]"
                          f"  HIGH_TEMPERATURE {temperature}°C")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [STANDBY]  Device deactivated — waiting for ACTIVATE command")

            time.sleep(5)

    except KeyboardInterrupt:
        print("\n[Device 1] Shutting down...")
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
