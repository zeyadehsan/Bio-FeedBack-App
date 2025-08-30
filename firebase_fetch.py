# firebase_fetch.py
import firebase_admin
from firebase_admin import credentials, db

if not firebase_admin._apps:  # only initialize once
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://biofeedback-a3a9d-default-rtdb.firebaseio.com/"
    })

def fetch_latest_hrv():
    ref = db.reference("processed_sensor_logs")
    logs = ref.get()
    if not logs:
        return None

    latest_log = max(logs.values(), key=lambda x: x.get("timestamp", 0))
    hrv = latest_log.get("hrvMetrics", {})

    return {
        "hfPower": hrv.get("hfPower", 0),
        "lfPower": hrv.get("lfPower", 0),
        "lfHfRatio": hrv.get("lfHfRatio", 0),
        "pnn50": hrv.get("pnn50", 0),
        "rmssd": hrv.get("rmssd", 0),
        "sdnn": hrv.get("sdnn", 0)
    }
