"""
Python UI Client - Smart Factory Floor Monitor
DISTINCTION version: replaces the graphical MQTT client.
Monitors all system topics and allows user to send commands to devices.
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

# All topics to monitor
TOPIC_PRIVATE_ALL = f"{STUDENT_ID}/#"
TOPIC_PUBLIC_ALL  = f"public/{STUDENT_ID}/#"

# Topics to publish commands to
TOPIC_CMD_DEVICE1 = f"{STUDENT_ID}/commands/device1"
TOPIC_CMD_DEVICE2 = f"{STUDENT_ID}/commands/device2"
TOPIC_PUBLIC_1    = f"public/{STUDENT_ID}/alerts/temperature"
TOPIC_PUBLIC_2    = f"public/{STUDENT_ID}/alerts/maintenance"
# ──────────────────────────────────────────────────────────────────────────────


def on_connect(client, userdata, flags, reason_code, _properties):
    if reason_code == 0:
        client.subscribe(TOPIC_PRIVATE_ALL)
        client.subscribe(TOPIC_PUBLIC_ALL)
        print("=" * 60)
        print("  Smart Factory Floor — Python UI Monitor")
        print("=" * 60)
        print(f"  Connected to broker at {BROKER}:{PORT}")
        print(f"  Monitoring : {TOPIC_PRIVATE_ALL}")
        print(f"  Monitoring : {TOPIC_PUBLIC_ALL}")
        print("=" * 60)
        print("  Incoming messages will appear below.")
        print("  Press Enter to open the command menu.\n")
    else:
        print(f"[UI] Connection failed. Return code: {reason_code}")


def on_message(client, userdata, msg):
    topic   = msg.topic
    payload = msg.payload.decode()
    ts      = datetime.now().strftime("%H:%M:%S")

    # Try to pretty-print JSON payloads
    try:
        data = json.loads(payload)
        payload_str = json.dumps(data)
    except json.JSONDecodeError:
        payload_str = payload

    if "commands" in topic:
        print(f"\n[{ts}] [COMMAND]  {topic}")
        print(f"         {payload_str}")
    elif "public" in topic:
        print(f"\n[{ts}] [PUBLIC]   {topic}")
        print(f"         {payload_str}")
    else:
        print(f"\n[{ts}] [PRIVATE]  {topic}")
        print(f"         {payload_str}")


def print_menu():
    print("\n" + "=" * 60)
    print("  COMMAND MENU")
    print("=" * 60)
    print("  [1] Send command to Device 1")
    print("  [2] Send command to Device 2")
    print("  [3] Post message to Public Topic 1 (temperature alerts)")
    print("  [4] Post message to Public Topic 2 (maintenance alerts)")
    print("  [m] Show this menu again")
    print("  [q] Quit")
    print("=" * 60)


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(USERNAME, PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"[UI] Connecting to broker at {BROKER}:{PORT} ...")
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()   # runs MQTT in background thread

    try:
        while True:
            user_input = input()   # wait for Enter key

            if user_input.lower() == "q":
                print("[UI] Shutting down...")
                break

            elif user_input.lower() == "m":
                print_menu()

            elif user_input == "1":
                cmd = input("  Enter command for Device 1: ").strip()
                if cmd:
                    client.publish(TOPIC_CMD_DEVICE1, cmd)
                    print(f"  Sent to Device 1: {cmd}")

            elif user_input == "2":
                cmd = input("  Enter command for Device 2: ").strip()
                if cmd:
                    client.publish(TOPIC_CMD_DEVICE2, cmd)
                    print(f"  Sent to Device 2: {cmd}")

            elif user_input == "3":
                msg = input("  Enter message for Public Topic 1: ").strip()
                if msg:
                    client.publish(TOPIC_PUBLIC_1, msg)
                    print(f"  Posted to Public Topic 1: {msg}")

            elif user_input == "4":
                msg = input("  Enter message for Public Topic 2: ").strip()
                if msg:
                    client.publish(TOPIC_PUBLIC_2, msg)
                    print(f"  Posted to Public Topic 2: {msg}")

            elif user_input == "":
                print_menu()

            else:
                print("  Unknown option. Press Enter to see the menu.")

    except KeyboardInterrupt:
        print("\n[UI] Shutting down...")

    client.loop_stop()
    client.disconnect()


if __name__ == "__main__":
    main()
