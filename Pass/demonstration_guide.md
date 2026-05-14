# Pass Demonstration Guide
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

Open a PowerShell window, navigate to the Pass folder and run:
```
cd "path\to\Pass"
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

## Step 2 — Run Device 1 (Publisher)

Open a SECOND PowerShell window, navigate to the Pass folder and run:
```
cd "path\to\Pass"
python device1.py
```

Expected output:
```
[Device 1] Connecting to broker at 192.168.12.100:1883 ...
[Device 1] Connected to MQTT Broker successfully!
------------------------------------------------------------
[Device 1] Sensor simulation running. Press Ctrl+C to stop.

[09:01:05] [PUBLISHED]  Temp=27.43°C  Humidity=61.2%
[09:01:10] [PUBLISHED]  Temp=31.08°C  Humidity=55.7%
```

Check Device 2's window — it should now be printing the received messages:
```
[09:01:05] [SENSOR DATA]  topic=<student_id>/sensors/temperature
           device=Device1  value=27.43C  time=2026-05-04 09:01:05
[09:01:05] [SENSOR DATA]  topic=<student_id>/sensors/humidity
           device=Device1  value=61.2%   time=2026-05-04 09:01:05
```

---

## Step 3 — Demo 1: Graphical Client Receives Device 1 Messages
### (Pass requirement: "Use a graphical MQTT client to demonstrate received messages from device 1")

1. Open MQTTX
2. Click **New Connection** and fill in:
   - Host: `192.168.12.100`
   - Port: `1883`
   - Username: your student ID
   - Password: your student ID
3. Click **Connect** (dot turns green)
4. Click **+ New Subscription**
5. Enter topic: `<student_id>/sensors/#`
6. Click **Confirm**
7. MQTTX will now show temperature and humidity messages arriving every 5 seconds

**What to show the lecturer:** MQTTX receiving live sensor messages from Device 1.

---

## Step 4 — Demo 2: Graphical Client Sends Message to Device 2
### (Pass requirement: "Use a graphical MQTT client to demonstrate generating a message and sending it to device 2")

1. In MQTTX (still connected), go to the bottom publish bar
2. In the **Topic** field type: `<student_id>/commands/device2`
3. In the **payload** text area type: `ACTIVATE_ALARM`
4. Click the **Send** button (↑ arrow)

**What to show the lecturer:** Device 2's terminal printing the received command:
```
[COMMAND RECEIVED]  topic=<student_id>/commands/device2
         Action: ACTIVATE_ALARM
```

---

## Step 5 — Demo 3: Public Messages
### (Pass requirement: Device 2 subscribes to public channel and prints sub-topic info)

1. In MQTTX, add another subscription: `public/#`
2. You will see messages from all other students appearing, each showing its full sub-topic

Device 2's terminal will also print any public messages it receives:
```
[09:05:12] [PUBLIC]   topic=public/student123/alerts
           message=temperature_high
```

---

## Summary of What Each Demo Proves

| Pass Requirement                              | How it is demonstrated                          |
|-----------------------------------------------|-------------------------------------------------|
| Device 1 generates and publishes data         | device1.py terminal showing [PUBLISHED] every 5s |
| Device 2 subscribes and prints messages       | device2.py terminal showing [SENSOR DATA]        |
| Device 2 prints public messages + sub-topic   | device2.py prints [PUBLIC] with full topic path  |
| Graphical client receives Device 1 messages   | MQTTX showing sensor messages (Step 3)           |
| Graphical client sends message to Device 2    | MQTTX sends command, Device 2 prints it (Step 4) |
| Source code provided                          | device1.py and device2.py in this folder         |

---

## How to Stop

Press **Ctrl+C** in each PowerShell window to stop the scripts.
