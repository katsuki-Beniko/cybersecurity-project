# ─── Broker ───────────────────────────────────────────────────────────────────
BROKER     = "127.0.0.1"        # change to 192.168.12.100 for lab demo
PORT       = 1883
STUDENT_ID = "123456789"        # replace with your actual student ID
USERNAME   = STUDENT_ID
PASSWORD   = STUDENT_ID

# ─── MongoDB ──────────────────────────────────────────────────────────────────
MONGO_URI = "mongodb://localhost:27017"
MONGO_DB  = "smart_factory"

# ─── Private MQTT topics ──────────────────────────────────────────────────────
TOPIC_D1_TELEMETRY = f"{STUDENT_ID}/factory/device1/telemetry"
TOPIC_D1_HEARTBEAT = f"{STUDENT_ID}/factory/device1/heartbeat"
TOPIC_D2_HEARTBEAT = f"{STUDENT_ID}/factory/device2/heartbeat"
TOPIC_D1_ACK       = f"{STUDENT_ID}/factory/device1/ack"
TOPIC_D2_ACK       = f"{STUDENT_ID}/factory/device2/ack"
TOPIC_CMD_D1       = f"{STUDENT_ID}/commands/device1"
TOPIC_CMD_D2       = f"{STUDENT_ID}/commands/device2"

# ─── Public MQTT topics (assignment requirement) ──────────────────────────────
TOPIC_PUBLIC_1   = "public/smartfactory/alerts/temperature"   # Topic 1
TOPIC_PUBLIC_2   = "public/smartfactory/alerts/maintenance"   # Topic 2
TOPIC_PUBLIC_LOG = "public/smartfactory/factory/logs"

# ─── Subscribe wildcards ──────────────────────────────────────────────────────
TOPIC_PRIVATE_ALL = f"{STUDENT_ID}/#"
TOPIC_PUBLIC_ALL  = "public/#"

# ─── Thresholds ───────────────────────────────────────────────────────────────
TEMP_ALERT_THRESHOLD = 35.0    # °C — publish Topic 1 alert
TEMP_CRITICAL        = 50.0    # °C — immediate cooling required
AI_MIN_SAMPLES       = 20      # readings before Isolation Forest fits
AI_REFIT_EVERY       = 50      # refit model every N readings
CONTAMINATION        = 0.1     # expected anomaly fraction
AUTO_EMERGENCY_COUNT = 3       # consecutive alerts before emergency

# ─── Device management ────────────────────────────────────────────────────────
HEARTBEAT_INTERVAL = 30        # seconds between heartbeats
OFFLINE_TIMEOUT    = 60        # seconds before marking device offline

# ─── Roles ────────────────────────────────────────────────────────────────────
ROLE_ADMIN    = "admin"
ROLE_OPERATOR = "operator"
