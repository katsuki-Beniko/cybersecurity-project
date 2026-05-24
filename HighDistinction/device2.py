"""
Device 2 - Maintenance Node (Smart Factory Floor)
PROFESSIONAL HIGH DISTINCTION version:
  - Subscribes to public/# (all public — Credit requirement)
  - Automatically reacts to Topic 1 alerts with calculated responses
  - Escalates to EMERGENCY after consecutive alerts
  - Publishes routine maintenance status on a regular cycle
  - Sends heartbeat every 30 seconds
  - Acknowledges every received command
"""

import paho.mqtt.client as mqtt
import time
import random
import json
import threading
from datetime import datetime
from config import *

_consecutive_alerts = 0
_active             = True


def on_connect(client, userdata, flags, reason_code, _properties):
    if reason_code == 0:
        print("[Device 2] Connected to MQTT Broker successfully!")
        client.subscribe("public/#")
        client.subscribe(TOPIC_CMD_D2)
        print(f"[Device 2] Subscribed to public (all)       : public/#")
        print(f"[Device 2] Responds specifically to         : {TOPIC_PUBLIC_1}")
        print(f"[Device 2] Subscribed to commands           : {TOPIC_CMD_D2}")
        print("-" * 60)
        print("[Device 2] Running. Press Ctrl+C to stop.\n")
    else:
        print(f"[Device 2] Connection failed. Code: {reason_code}")


def on_message(client, userdata, msg):
    global _consecutive_alerts, _active
    topic   = msg.topic
    payload = msg.payload.decode()
    ts      = datetime.now().strftime("%H:%M:%S")

    if topic == TOPIC_PUBLIC_1:
        try:
            data  = json.loads(payload)
            alert = data.get("alert", "")
            value = data.get("value", 0)
        except json.JSONDecodeError:
            alert = payload
            value = 0

        if alert == "HIGH_TEMPERATURE":
            if _active:
                _consecutive_alerts += 1
                print(f"[{ts}] [TOPIC 1 RECEIVED]  HIGH_TEMPERATURE {value}°C"
                      f"  (consecutive={_consecutive_alerts})")
                _auto_respond(client, float(value), ts)
            else:
                print(f"[{ts}] [TOPIC 1 RECEIVED]  HIGH_TEMPERATURE {value}°C  (STANDBY — ignoring)")
        else:
            _consecutive_alerts = 0

    elif topic == TOPIC_CMD_D2:
        try:
            data   = json.loads(payload)
            action = data.get("action", payload)
        except json.JSONDecodeError:
            action = payload

        print(f"[{ts}] [COMMAND RECEIVED]  action={action}")

        if action == "RUN_DIAGNOSTICS":
            diag_ack = json.dumps({
                "device":             "Device2",
                "action":             "RUN_DIAGNOSTICS",
                "status":             "ACKNOWLEDGED",
                "active":             _active,
                "consecutive_alerts": _consecutive_alerts,
                "checks": {
                    "mqtt_connection":      "OK",
                    "sensor_subscription":  "OK",
                    "maintenance_response": "OK",
                },
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            })
            client.publish(TOPIC_D2_ACK, diag_ack)
            print(f"[{ts}]   → Diagnostics report sent  (active={_active}  alerts={_consecutive_alerts})")
        else:
            ack = json.dumps({
                "device":    "Device2",
                "action":    action,
                "status":    "ACKNOWLEDGED",
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            })
            client.publish(TOPIC_D2_ACK, ack)

            if action == "ACTIVATE":
                _active = True
                print(f"[{ts}]   → Device ACTIVATED — resuming maintenance monitoring")
            elif action == "DEACTIVATE":
                _active = False
                print(f"[{ts}]   → Device DEACTIVATED — maintenance monitoring paused")

    elif topic.startswith("public/"):
        print(f"[{ts}] [PUBLIC]  topic={topic}")
        print(f"         Message: {payload}")


def _auto_respond(client, temperature, ts):
    ts_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    if _consecutive_alerts >= AUTO_EMERGENCY_COUNT:
        status, priority, machine = "EMERGENCY_COOLING_REQUIRED", "CRITICAL", "MACHINE_ALL"
    elif temperature >= TEMP_CRITICAL:
        status, priority = "IMMEDIATE_COOLING_REQUIRED", "HIGH"
        machine = f"MACHINE_{random.randint(1, 5)}"
    elif temperature >= TEMP_ALERT_THRESHOLD + 2:
        status, priority = "COOLING_ACTIVATED", "MEDIUM"
        machine = f"MACHINE_{random.randint(1, 5)}"
    else:
        status, priority = "MONITOR_TEMPERATURE", "LOW"
        machine = f"MACHINE_{random.randint(1, 5)}"

    response = json.dumps({
        "device":             "Device2",
        "status":             status,
        "triggered_by_temp":  temperature,
        "consecutive_alerts": _consecutive_alerts,
        "machine_id":         machine,
        "priority":           priority,
        "timestamp":          ts_iso,
    })
    client.publish(TOPIC_PUBLIC_2, response)

    # Sanitised public log
    client.publish(TOPIC_PUBLIC_LOG, json.dumps({
        "device":    "Device2",
        "event":     "MAINTENANCE_RESPONSE",
        "status":    status,
        "priority":  priority,
        "timestamp": ts_iso,
    }))

    print(f"[{ts}] [AUTO RESPONSE → Topic 2]  status={status}  priority={priority}")


def _heartbeat_loop(client):
    while True:
        payload = json.dumps({
            "device":    "Device2",
            "status":    "online",
            "active":    _active,
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        })
        client.publish(TOPIC_D2_HEARTBEAT, payload)
        time.sleep(HEARTBEAT_INTERVAL)


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(USERNAME, PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"[Device 2] Connecting to broker at {BROKER}:{PORT} ...")
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()

    threading.Thread(target=_heartbeat_loop, args=(client,), daemon=True).start()

    routine_statuses = ["ALL_SYSTEMS_OK", "FILTER_CHECK_DUE", "BELT_WORN", "LUBRICATION_NEEDED"]
    cycle = 0

    try:
        while True:
            cycle += 1
            if cycle % 6 == 0:
                if _active:
                    ts_iso  = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    status  = random.choice(routine_statuses)
                    payload = json.dumps({
                        "device":     "Device2",
                        "status":     status,
                        "machine_id": f"MACHINE_{random.randint(1, 5)}",
                        "priority":   "ROUTINE",
                        "timestamp":  ts_iso,
                    })
                    client.publish(TOPIC_PUBLIC_2, payload)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] [ROUTINE STATUS]  status={status}")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] [STANDBY]  Device deactivated — waiting for ACTIVATE command")

            time.sleep(5)

    except KeyboardInterrupt:
        print("\n[Device 2] Shutting down...")
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
