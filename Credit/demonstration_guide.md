# Credit Demonstration Guide
## TNE20003 – Internet and Cybersecurity for Engineering Applications

---

## Before You Start

### Requirements
- Python installed
- paho-mqtt library installed: `pip install paho-mqtt`
- Connected to the university lab network (192.168.12.100 must be reachable)
- MQTTX graphical client installed (mqttx.app)

### Update the broker address in both files
In both device1.py and device2.py, change line 8:
```python
BROKER = "127.0.0.1"   →   BROKER = "192.168.12.100"
```

### Update your Student ID in both files
In both device1.py and device2.py, change line 10:
```python
STUDENT_ID = "123456789"   →   STUDENT_ID = "your_actual_student_id"
```

---

## Step 1 — Run Device 2 (Subscriber)

Open a PowerShell window, navigate to the Credit folder and run:
```
cd "path\to\Credit"
python device2.py
```

Expected output:
```
[Device 2] Connecting to broker at 192.168.12.100:1883 ...
[Device 2] Connected to MQTT Broker successfully!
[Device 2] Subscribed to sensors  : <student_id>/sensors/#
[Device 2] Subscribed to commands : <student_id>/commands/device2
[Device 2] Subscribed to public   : public/#
------------------------------------------------------------
[Device 2] Waiting for messages...
```

Leave this window open.

---

## Step 2 — Run Device 1 (Publisher + Subscriber)

Open a SECOND PowerShell window, navigate to the Credit folder and run:
```
cd "path\to\Credit"
python device1.py
```

Expected output:
```
[Device 1] Connecting to broker at 192.168.12.100:1883 ...
[Device 1] Connected to MQTT Broker successfully!
[Device 1] Subscribed to commands : <student_id>/commands/device1
[Device 1] Subscribed to public   : public/#
------------------------------------------------------------
[Device 1] Sensor simulation running. Press Ctrl+C to stop.

[09:01:05] [PUBLISHED]  Temp=27.43°C  Humidity=61.2%
[09:01:10] [PUBLISHED]  Temp=31.08°C  Humidity=55.7%
```

Check Device 2's window — it should now be printing received sensor data:
```
[09:01:05] [SENSOR DATA]  topic=<student_id>/sensors/temperature
           device=Device1  value=27.43C  time=2026-05-04 09:01:05
[09:01:05] [SENSOR DATA]  topic=<student_id>/sensors/humidity
           device=Device1  value=61.2%   time=2026-05-04 09:01:05
```

---

## Step 3 — Demo Credit Requirement: Device 1 Both Publishes AND Subscribes
### (Credit requirement: "One of the device applications must both generate messages AND subscribe to a topic")

**What to show the lecturer:**
- Device 1's terminal shows [PUBLISHED] every 5 seconds (it is generating data)
- Now open MQTTX and send a command TO Device 1:
  1. Connect MQTTX to `192.168.12.100:1883` (username + password = student ID)
  2. In the **Topic** field type: `<student_id>/commands/device1`
  3. In the payload type: `STOP_FAN`
  4. Click **Send**
- Device 1's terminal will print:
```
[COMMAND RECEIVED] topic=<student_id>/commands/device1
         Action: STOP_FAN
```

This proves Device 1 both **publishes** sensor data AND **subscribes** to receive commands.

---

## Step 4 — Demo Credit Requirement: Both Devices Subscribe to Public Topic
### (Credit requirement: "Both device applications must subscribe to the public topic")

**What to show the lecturer:**
- Point to Device 1's terminal subscriptions printed at startup:
  ```
  [Device 1] Subscribed to public   : public/#
  ```
- Point to Device 2's terminal subscriptions printed at startup:
  ```
  [Device 2] Subscribed to public   : public/#
  ```
- In MQTTX, publish a message to the public topic:
  1. Topic: `public/demo/alert`
  2. Payload: `hello_from_mqttx`
  3. Click **Send**
- BOTH Device 1 and Device 2 terminals will print:
```
[PUBLIC]  topic=public/demo/alert  msg=hello_from_mqttx
```

This proves both devices subscribe to the public topic.

---

## Step 5 — Demo Pass Requirements (still required for Credit)

### Graphical client receives Device 1 messages
1. In MQTTX, click **+ New Subscription**
2. Enter topic: `<student_id>/sensors/#`
3. Click **Confirm**
4. MQTTX shows temperature and humidity messages arriving every 5 seconds

### Graphical client sends message to Device 2
1. In MQTTX, set Topic to: `<student_id>/commands/device2`
2. Payload: `ACTIVATE_ALARM`
3. Click **Send**
4. Device 2's terminal prints:
```
[COMMAND RECEIVED]  topic=<student_id>/commands/device2
         Action: ACTIVATE_ALARM
```

---

## Step 6 — Cybersecurity Report

Present the **cybersecurity_report.md** file. Walk through the key security issues:

1. **No TLS encryption** — all traffic is plaintext, anyone on the network can sniff it
2. **Weak credentials** — password equals username (student ID), trivially guessable
3. **Insufficient access control** — public topic can be flooded by any user
4. **Shared broker** — one bad client can affect all other projects
5. **No message integrity** — no way to verify messages haven't been tampered with
6. **Perimeter-only security** — once inside the network, no further barriers exist
7. **No audit logging** — attacks leave no trace

---

## Summary of What Each Demo Proves

| Credit Requirement                                        | How it is demonstrated                                        |
|-----------------------------------------------------------|---------------------------------------------------------------|
| Device 1 generates AND subscribes                         | Device 1 prints [PUBLISHED] + receives [COMMAND] from MQTTX  |
| Both devices subscribe to public topic                    | Both terminals show public subscription at startup (Step 4)   |
| Device 2 subscribes and prints messages + public sub-topic| Device 2 terminal prints [SENSOR DATA] and [PUBLIC] with topic|
| Graphical client receives Device 1 messages               | MQTTX shows sensor messages (Step 5)                          |
| Graphical client sends message to Device 2                | MQTTX sends command, Device 2 prints it (Step 5)              |
| Cybersecurity report on broker security issues            | Present cybersecurity_report.md (Step 6)                      |
| Source code provided                                      | device1.py and device2.py in this folder                      |

---

## How to Stop

Press **Ctrl+C** in each PowerShell window to stop the scripts.
