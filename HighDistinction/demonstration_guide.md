# High Distinction Demonstration Guide
## TNE20003 – Internet and Cybersecurity for Engineering Applications

---

## Before You Start

### 1. Install required libraries
```
pip install paho-mqtt scikit-learn pymongo matplotlib
```
tkinter is built into Python — no separate install needed.

### 2. Start MongoDB
Make sure MongoDB is running locally. Open **MongoDB Compass** and connect to:
```
mongodb://localhost:27017
```
You will see the `smart_factory` database populated with live data during the demo.

### 3. Update config.py — ONE file controls everything
Open `HighDistinction/config.py` and change two values:

```python
STUDENT_ID = "123456789"       →   STUDENT_ID = "your_actual_student_id"
BROKER     = "127.0.0.1"       →   BROKER     = "192.168.12.100"
```

That is the only file you need to edit. `device1.py`, `device2.py`, and `ui_client.py`
all import from `config.py` automatically.

---

## Topic Structure

| Topic | Who Publishes | Who Subscribes |
|-------|--------------|----------------|
| `STUDENT_ID/device1/telemetry` (private) | Device 1 | UI Client |
| `STUDENT_ID/sensors/temperature` | Device 1 | UI Client |
| `STUDENT_ID/sensors/humidity` | Device 1 | UI Client |
| `STUDENT_ID/sensors/vibration` | Device 1 | UI Client |
| `STUDENT_ID/device1/heartbeat` | Device 1 | UI Client |
| `STUDENT_ID/device1/ack` | Device 1 | UI Client |
| `STUDENT_ID/device2/heartbeat` | Device 2 | UI Client |
| `STUDENT_ID/device2/ack` | Device 2 | UI Client |
| `public/STUDENT_ID/alerts/temperature` (Topic 1) | Device 1 | Device 2 + all `public/#` |
| `public/STUDENT_ID/alerts/maintenance` (Topic 2) | Device 2 | Device 1 + all `public/#` |
| `public/STUDENT_ID/log` | Device 1, Device 2 | All `public/#` subscribers |
| `STUDENT_ID/commands/device1` | UI Client | Device 1 |
| `STUDENT_ID/commands/device2` | UI Client | Device 2 |

**Both devices subscribe to `public/#`** — they receive ALL public messages from any device
on the broker, satisfying the Credit requirement for broad public subscription.

---

## Step 1 — Run Device 2 first

Open a PowerShell window, navigate to the HighDistinction folder and run:
```
cd "path\to\HighDistinction"
python device2.py
```

Expected output:
```
[Device 2] Connecting to broker at 192.168.12.100:1883 ...
[Device 2] Connected to MQTT Broker successfully!
[Device 2] Subscribed to public (all)       : public/#
[Device 2] Responds specifically to         : public/<id>/alerts/temperature
[Device 2] Subscribed to commands           : <id>/commands/device2
------------------------------------------------------------
[Device 2] Running. Press Ctrl+C to stop.
```

**What to point out:** Device 2 subscribes to `public/#` — the wildcard means it receives
every public message on the broker, not just its own student ID's messages. This satisfies
the Credit requirement for inter-device public communication.

---

## Step 2 — Run Device 1

Open a SECOND PowerShell window and run:
```
python device1.py
```

Expected output:
```
[Device 1] Connected to MQTT Broker successfully!
[Device 1] Subscribed to public (all)       : public/#
[Device 1] Responds specifically to         : public/<id>/alerts/maintenance
[Device 1] Subscribed to commands           : <id>/commands/device1
[Device 1] Sensor simulation running. Press Ctrl+C to stop.

[21:33:20] [TELEMETRY]  Temp=27.43°C  Hum=61.2%  Vib=1.234mm/s  Cooling=OFF
[21:33:25] [TELEMETRY]  Temp=36.1°C   Hum=55.7%  Vib=2.011mm/s  Cooling=OFF
[21:33:25] [PUBLIC ALERT → Topic 1]  HIGH_TEMPERATURE 36.1°C
```

When Device 1 publishes a HIGH_TEMPERATURE alert, Device 2 automatically reacts:
```
[21:33:25] [TOPIC 1 RECEIVED]  HIGH_TEMPERATURE 36.1°C  (consecutive=1)
[21:33:25] [AUTO RESPONSE → Topic 2]  status=MONITOR_TEMPERATURE  priority=LOW
```

**What to point out:** Device 2 is reacting autonomously to Device 1's public alert,
calculating a priority response, and publishing it back to Topic 2 — all without human input.
After 3 consecutive alerts the status escalates to EMERGENCY_COOLING_REQUIRED.

---

## Step 3 — Run the GUI Dashboard

Open a THIRD PowerShell window and run:
```
python ui_client.py
```

### Login Screen

A login window appears. Two accounts are pre-seeded automatically:

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Admin |
| operator | operator123 | Operator |

**What to point out:** Passwords are stored as SHA-256 hashes with a random salt in
MongoDB — not plain text. Log in as `admin` first to show all features, then re-launch
and log in as `operator` to demonstrate role-based access control.

### Main Dashboard — 6 Tabs

After login the title bar shows your username and role:
```
Smart Factory Floor Monitor  —  admin (Admin)
```

---

## Step 4 — Tab 1: Live Dashboard

The Live tab has three panels running side by side:

**Sensor Readings panel:**
```
Temperature : 27.43 °C
Humidity    : 61.2 %
Vibration   : 1.234 mm/s
Cooling     : OFF
```

**AI Engine panel:**
```
Status        : Normal
Score         : -0.082
Classification: NORMAL
Risk Score    : 2.1 / 10
Predicted     : 28.1 °C (in 30s)
Samples       : 15 / 20
```

**Device Status panel:**
```
Device 1 : Online   Last seen: 14:22:05
Device 2 : Online   Last seen: 14:22:03
```

Below the panels is a scrolling alert log showing every reading, alert,
and AI result in real time.

**Command buttons (bottom):**
- Activate Cooling → sends ACTIVATE_COOLING to Device 1
- Deactivate Cooling → sends DEACTIVATE_COOLING to Device 1
- Emergency Cooling → **Admin only**, sends EMERGENCY_COOLING to Device 1
- D2 Diagnostics → sends RUN_DIAGNOSTICS to Device 2
- Status Check → sends STATUS to Device 1
- Simulate Attack → publishes a fake 95°C reading to trigger AI detection

**Demonstrate role restriction:**
Log in as `operator` and the Emergency Cooling button does not appear.
Log in as `admin` and it is present. This is role-based access control.

---

## Step 5 — Demo: AI Anomaly Detection + Simulate Attack

**What to explain:**

The AI uses scikit-learn's Isolation Forest algorithm to learn the normal range of
temperature, humidity, and vibration readings. After 20 samples it scores every new
reading. A score close to -1.0 means anomaly; close to 0 means normal.

The AI Engine also runs `numpy.polyfit` on the last 15 temperatures to predict the
temperature 30 seconds ahead — predictive maintenance.

Classifications:
- `NORMAL` — within learned range
- `OVERHEATING` — high temperature + anomaly
- `SENSOR_FAULT` — value is statistically impossible (below 0 or extreme)
- `HUMIDITY_SPIKE` — humidity anomaly
- `INJECTION_ATTACK` — extreme outlier, consistent with a spoofed MQTT message

**How to demonstrate:**

Click **"Simulate Attack"**. This publishes a fake reading of 95°C attributed to
`ATTACKER` — the AI has never seen a value that high, so it scores it as a strong anomaly.

Watch the AI panel:
```
Status        : ANOMALY DETECTED
Score         : -0.412
Classification: INJECTION_ATTACK
Risk Score    : 9.8 / 10
```

The alert log shows:
```
[14:25:10] AI ANOMALY  INJECTION_ATTACK  temp=95.0°C  risk=9.8
```

The anomaly is also saved to MongoDB immediately — open Compass and show the
`sensor_readings` collection updating in real time.

**Cybersecurity relevance to explain:**
"This simulates detecting a tampered or injected MQTT message. If an attacker publishes
a fake sensor reading to our topic, the Isolation Forest flags it as statistically
abnormal within milliseconds — this is anomaly-based intrusion detection applied
to IoT message streams."

---

## Step 6 — Tab 2: Charts

The Chart tab shows two live matplotlib charts embedded directly in the GUI:
- Temperature history (last 30 readings)
- Humidity history (last 30 readings)

Charts auto-refresh every 15 seconds from MongoDB. This means even if you close
and re-open the UI, the history is preserved — data lives in the database, not RAM.

---

## Step 7 — Tab 3: Alerts

The Alerts tab shows every alert raised, pulled from MongoDB's `alerts` collection:

```
Timestamp          | Device  | Type              | Value | Severity | Status
2026-05-13 14:22:01 | Device1 | HIGH_TEMPERATURE  | 36.1  | HIGH     | Unresolved
2026-05-13 14:25:10 | ATTACKER| INJECTION_ATTACK  | 95.0  | CRITICAL | Unresolved
```

**Admin only:** Click an alert row and press **"Acknowledge Alert"** to mark it resolved.
Operators see the button greyed out — they can view but not acknowledge.

Open MongoDB Compass → `smart_factory` → `alerts` to show the same data persisted.

---

## Step 8 — Tab 4: Commands

The Commands tab shows the full command history with acknowledgment tracking:

```
Timestamp          | Device  | Action           | Sent By | Status
2026-05-13 14:23:01 | Device1 | ACTIVATE_COOLING | admin   | ACKNOWLEDGED
2026-05-13 14:23:15 | Device1 | STATUS           | admin   | PENDING
```

Status goes from `PENDING` → `ACKNOWLEDGED` when the device publishes its ACK message.

**What to point out:**
- Every command is traceable to the user who sent it
- The PENDING → ACKNOWLEDGED lifecycle shows the complete command loop
- This is non-repudiation and audit trail — core cybersecurity concepts

---

## Step 9 — Tab 5: Devices

The Devices tab shows live device registry from MongoDB's `devices` collection:

```
Device ID | Name     | Status  | Last Heartbeat
Device1   | Sensor 1 | Online  | 14:25:02
Device2   | Maint 2  | Online  | 14:25:00
```

Both devices send a heartbeat every 30 seconds. If a device stops sending heartbeats,
the UI marks it `Offline` after 60 seconds — demonstrated by stopping device1.py
with Ctrl+C and watching the Devices tab update.

---

## Step 10 — Tab 6: Audit Log

The Audit Log tab shows every sensor reading stored in MongoDB, with all AI columns:

```
Timestamp  | Device  | Sensor      | Value | Unit | Anomaly | Score  | Class         | Risk
14:22:01   | Device1 | temperature | 27.43 | C    | False   | -0.082 | NORMAL        | 2.1
14:25:10   | ATTACKER| temperature | 95.0  | C    | True    | -0.412 | INJECTION_ATK | 9.8
```

This is the forensic log — every reading with AI analysis is permanently stored.

---

## Step 11 — Show MongoDB Compass Live

While the system is running, switch to MongoDB Compass and show:

| Collection | What it shows |
|---|---|
| `users` | admin and operator accounts with hashed passwords (no plain text) |
| `sensor_readings` | every reading with AI score and classification |
| `alerts` | all alerts with resolved/unresolved status |
| `commands` | every command with sent_by and acknowledgment time |
| `devices` | device registry with last heartbeat timestamp |

**Key point for cybersecurity:** The passwords in the `users` collection are stored as
`salt:sha256hash` — never plain text. Compromising the database does not expose credentials.

---

## Step 12 — Cybersecurity Report

Present **cybersecurity_report.md**. Walk through:

1. **Sections 3.1–3.7**: The 7 internal network security issues
2. **Section 5**: The HD internet exposure extension

Key points to highlight:
- Section 5.2: Automated scanning (Shodan, Mirai botnet) — exposed broker is found
  within minutes
- Section 5.4: Remote command injection — attacker sends EMERGENCY_COOLING from
  anywhere with no physical access
- Section 7.8: AI anomaly detection as a defence — directly connects the Simulate
  Attack demo to a real cybersecurity mitigation technique

---

## Summary Table — What Each Demo Proves

| Requirement | Evidence |
|---|---|
| Both devices subscribe to `public/#` | Device 1 + 2 startup output (Step 1–2) |
| Device 1 publishes temp/humidity/vibration | Telemetry output + Audit Log tab (Step 2, 10) |
| Device 2 auto-responds to Topic 1 alerts | AUTO RESPONSE lines in Device 2 terminal (Step 2) |
| Escalation to EMERGENCY after 3 alerts | Device 2 terminal after 3 consecutive alerts (Step 2) |
| Login + role-based access control | Login screen + Emergency Cooling button (Step 3, 4) |
| Password hashing with SHA-256 + salt | MongoDB Compass `users` collection (Step 11) |
| AI anomaly detection (Isolation Forest) | AI Engine panel + Simulate Attack (Step 5) |
| Anomaly classification + risk score | AI Engine panel (INJECTION_ATTACK, 9.8/10) (Step 5) |
| Predictive temperature (polyfit) | AI Engine "Predicted" field (Step 4) |
| Live charts from MongoDB | Chart tab auto-refresh (Step 6) |
| Alert acknowledgment (admin only) | Alerts tab Acknowledge button (Step 7) |
| Command + ACK lifecycle | Commands tab PENDING → ACKNOWLEDGED (Step 8) |
| Device heartbeat + offline detection | Devices tab, stop device1.py (Step 9) |
| Full audit log in MongoDB | Audit Log tab + Compass (Step 10–11) |
| Cybersecurity report | cybersecurity_report.md (Step 12) |

---

## How to Stop

1. Close the GUI window (or press the X button) — MQTT disconnects cleanly
2. Press **Ctrl+C** in the Device 2 PowerShell window
3. Press **Ctrl+C** in the Device 1 PowerShell window

MongoDB keeps all data between sessions — restart the UI any time and the history,
alerts, and audit log are still there.
