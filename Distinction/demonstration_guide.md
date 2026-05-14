# Distinction Demonstration Guide
## TNE20003 – Internet and Cybersecurity for Engineering Applications

---

## Before You Start

### Requirements
- Python installed
- paho-mqtt library installed: `pip install paho-mqtt`
- Connected to the university lab network (192.168.12.100 must be reachable)

### Update the broker address in ALL THREE files
In device1.py, device2.py, and ui_client.py, change line 8:
```python
BROKER = "127.0.0.1"   →   BROKER = "192.168.12.100"
```

### Update your Student ID in ALL THREE files
In device1.py, device2.py, and ui_client.py, change line 10:
```python
STUDENT_ID = "123456789"   →   STUDENT_ID = "your_actual_student_id"
```

---

## Topic Structure

| Topic | Who Publishes | Who Subscribes |
|-------|--------------|----------------|
| `STUDENT_ID/sensors/temperature` | Device 1 | UI Client |
| `STUDENT_ID/sensors/humidity` | Device 1 | UI Client |
| `public/STUDENT_ID/alerts/temperature` (Topic 1) | Device 1 | Device 2, UI Client |
| `public/STUDENT_ID/alerts/maintenance` (Topic 2) | Device 2 | Device 1, UI Client |
| `STUDENT_ID/commands/device1` | UI Client | Device 1 |
| `STUDENT_ID/commands/device2` | UI Client | Device 2 |

---

## Step 1 — Run Device 2

Open a PowerShell window, navigate to the Distinction folder and run:
```
cd "path\to\Distinction"
python device2.py
```

Expected output:
```
[Device 2] Connected to MQTT Broker successfully!
[Device 2] Subscribed to public Topic 1 : public/<student_id>/alerts/temperature
[Device 2] Subscribed to commands       : <student_id>/commands/device2
------------------------------------------------------------
[Device 2] Running. Press Ctrl+C to stop.
```

---

## Step 2 — Run Device 1

Open a SECOND PowerShell window and run:
```
python device1.py
```

Expected output:
```
[Device 1] Connected to MQTT Broker successfully!
[Device 1] Subscribed to public Topic 2 : public/<student_id>/alerts/maintenance
[Device 1] Subscribed to commands       : <student_id>/commands/device1
------------------------------------------------------------
[21:33:20] [PRIVATE PUBLISHED]  Temp=27.43°C  Humidity=61.2%
[21:33:25] [PRIVATE PUBLISHED]  Temp=36.1°C  Humidity=55.7%
[21:33:25] [PUBLIC TOPIC 1 PUBLISHED]  ALERT: High temp 36.1°C
```

When Device 1 publishes to Public Topic 1, check Device 2's window — it will print:
```
[PUBLIC TOPIC 1 - TEMP ALERT] topic=public/<student_id>/alerts/temperature
         Message: {"device": "Device1", "alert": "HIGH_TEMPERATURE", ...}
```

---

## Step 3 — Run the Python UI Client (replaces MQTTX)

Open a THIRD PowerShell window and run:
```
python ui_client.py
```

Expected output:
```
============================================================
  Smart Factory Floor — Python UI Monitor
============================================================
  Connected to broker at 192.168.12.100:1883
  Monitoring : <student_id>/#
  Monitoring : public/<student_id>/#
============================================================
  Incoming messages will appear below.
  Press Enter to open the command menu.
```

Messages from both devices will appear here automatically.

---

## Step 4 — Demo Distinction Requirement: Two Devices on Different Topics

**What to show the lecturer:**

- Device 1 subscribes to Public Topic 2 and prints Device 2's maintenance alerts
- Device 2 subscribes to Public Topic 1 and prints Device 1's temperature alerts
- They are on **different** topics responding to **different** posts

Point to Device 2's terminal when Device 1 publishes a high temperature:
```
[PUBLIC TOPIC 1 - TEMP ALERT] Message: HIGH_TEMPERATURE 36.1°C
```

Point to Device 1's terminal when Device 2 publishes a maintenance alert:
```
[PUBLIC TOPIC 2 - MAINTENANCE] Message: FILTER_CHECK_DUE
```

---

## Step 5 — Demo Distinction Requirement: Device 1 Publishes to More Than One Topic

**What to show the lecturer:**

Device 1 publishes to THREE topics:
1. `STUDENT_ID/sensors/temperature` (private)
2. `STUDENT_ID/sensors/humidity` (private)
3. `public/STUDENT_ID/alerts/temperature` (public Topic 1 — only when temp > 35°C)

Point to Device 1's terminal:
```
[PRIVATE PUBLISHED]       Temp=36.1°C  Humidity=55.7%   ← private topics
[PUBLIC TOPIC 1 PUBLISHED]  ALERT: High temp 36.1°C      ← public topic
```

---

## Step 6 — Demo Distinction Requirement: Python UI Client

**What to show the lecturer:**

The UI client replaces MQTTX completely. It monitors all topics and lets you send commands.

Press **Enter** in the UI client window to open the menu:
```
============================================================
  COMMAND MENU
============================================================
  [1] Send command to Device 1
  [2] Send command to Device 2
  [3] Post message to Public Topic 1 (temperature alerts)
  [4] Post message to Public Topic 2 (maintenance alerts)
  [m] Show this menu again
  [q] Quit
============================================================
```

**Demo sending a command to Device 1:**
- Press `1` then Enter
- Type `ACTIVATE_COOLING` then Enter
- Check Device 1's terminal — it prints:
```
[COMMAND RECEIVED] Action: ACTIVATE_COOLING
```

**Demo sending a command to Device 2:**
- Press `2` then Enter
- Type `RUN_DIAGNOSTICS` then Enter
- Check Device 2's terminal — it prints:
```
[COMMAND RECEIVED] Action: RUN_DIAGNOSTICS
```

---

## Step 7 — Cybersecurity Report

Present the **cybersecurity_report.md** file. Walk through the 7 identified security issues and their recommendations.

---

## Summary of What Each Demo Proves

| Distinction Requirement | How it is demonstrated |
|---|---|
| Two devices subscribe to different topics | Device 1 subscribes to Topic 2, Device 2 subscribes to Topic 1 (Steps 1–4) |
| Device 1 generates messages to more than one topic | Device 1 publishes to 3 topics: temp, humidity, public Topic 1 (Step 5) |
| Python UI client replaces graphical MQTT client | ui_client.py monitors all topics and sends commands via menu (Step 6) |
| Cybersecurity report | cybersecurity_report.md (Step 7) |

---

## How to Stop

Press **Ctrl+C** in each PowerShell window, or press `q` then Enter in the UI client.
