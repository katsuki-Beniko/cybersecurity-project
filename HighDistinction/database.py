"""
MongoDB database layer for Smart Factory Floor Monitor.
All collections live in the 'smart_factory' database.

Collections:
  users           — operator / admin accounts
  sensor_readings — every sensor reading with AI results
  alerts          — every alert raised, with resolved status
  commands        — every command sent, with acknowledgment tracking
  devices         — device registry with heartbeat and online status
"""

from pymongo import MongoClient, DESCENDING
from bson import ObjectId
from datetime import datetime
from config import MONGO_URI, MONGO_DB

_client = None
_db     = None


def get_db():
    global _client, _db
    if _db is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        _db     = _client[MONGO_DB]
    return _db


# ─── Users ────────────────────────────────────────────────────────────────────

def find_user(username: str):
    return get_db().users.find_one({"username": username})


def create_user(username: str, password_hash: str, role: str) -> bool:
    if find_user(username):
        return False
    get_db().users.insert_one({
        "username":      username,
        "password_hash": password_hash,
        "role":          role,
        "created_at":    datetime.now(),
    })
    return True


def get_all_users():
    return list(get_db().users.find({}, {"_id": 0, "password_hash": 0}))


# ─── Sensor readings ──────────────────────────────────────────────────────────

def insert_reading(device, sensor, value, unit,
                   is_anomaly, anomaly_score, classification, risk_score):
    get_db().sensor_readings.insert_one({
        "device":         device,
        "sensor":         sensor,
        "value":          value,
        "unit":           unit,
        "is_anomaly":     is_anomaly,
        "anomaly_score":  anomaly_score,
        "classification": classification,
        "risk_score":     risk_score,
        "timestamp":      datetime.now(),
    })


def get_recent_readings(sensor=None, limit=50):
    query = {"sensor": sensor} if sensor else {}
    return list(
        get_db().sensor_readings
        .find(query, {"_id": 0})
        .sort("timestamp", DESCENDING)
        .limit(limit)
    )


def get_chart_data(sensor="temperature", limit=30):
    docs = list(
        get_db().sensor_readings
        .find({"sensor": sensor}, {"_id": 0, "value": 1, "timestamp": 1})
        .sort("timestamp", DESCENDING)
        .limit(limit)
    )
    docs.reverse()
    return docs


# ─── Alerts ───────────────────────────────────────────────────────────────────

def insert_alert(device, alert_type, value, severity, classification) -> str:
    result = get_db().alerts.insert_one({
        "device":         device,
        "alert_type":     alert_type,
        "value":          value,
        "severity":       severity,
        "classification": classification,
        "resolved":       False,
        "resolved_at":    None,
        "timestamp":      datetime.now(),
    })
    return str(result.inserted_id)


def get_alerts(resolved=None, limit=100):
    query = {}
    if resolved is not None:
        query["resolved"] = resolved
    return list(
        get_db().alerts
        .find(query)
        .sort("timestamp", DESCENDING)
        .limit(limit)
    )


def resolve_alert(alert_id: str):
    get_db().alerts.update_one(
        {"_id": ObjectId(alert_id)},
        {"$set": {"resolved": True, "resolved_at": datetime.now()}},
    )


# ─── Commands ─────────────────────────────────────────────────────────────────

def insert_command(device, action, sent_by) -> str:
    result = get_db().commands.insert_one({
        "device":    device,
        "action":    action,
        "sent_by":   sent_by,
        "status":    "PENDING",
        "ack_at":    None,
        "timestamp": datetime.now(),
    })
    return str(result.inserted_id)


def acknowledge_command(device, action):
    cmd = get_db().commands.find_one(
        {"device": device, "action": action, "status": "PENDING"},
        sort=[("timestamp", DESCENDING)],
    )
    if cmd:
        get_db().commands.update_one(
            {"_id": cmd["_id"]},
            {"$set": {"status": "ACKNOWLEDGED", "ack_at": datetime.now()}},
        )


def get_commands(limit=50):
    return list(
        get_db().commands
        .find({}, {"_id": 0})
        .sort("timestamp", DESCENDING)
        .limit(limit)
    )


# ─── Devices ──────────────────────────────────────────────────────────────────

def upsert_device(device_id, name, status="online"):
    get_db().devices.update_one(
        {"device_id": device_id},
        {
            "$set": {
                "name":            name,
                "status":          status,
                "last_heartbeat":  datetime.now(),
            },
            "$setOnInsert": {"created_at": datetime.now()},
        },
        upsert=True,
    )


def update_heartbeat(device_id, active=True):
    status = "active" if active else "inactive"
    get_db().devices.update_one(
        {"device_id": device_id},
        {"$set": {"status": status, "last_heartbeat": datetime.now()}},
    )


def set_device_offline(device_id):
    get_db().devices.update_one(
        {"device_id": device_id},
        {"$set": {"status": "offline"}},
    )


def get_all_devices():
    return list(get_db().devices.find({}, {"_id": 0}))
