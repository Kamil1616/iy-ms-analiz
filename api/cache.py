import json
import os
from datetime import datetime, timedelta

CACHE_DIR = os.path.join(os.path.dirname(__file__), "../instance/cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def _cache_path(key):
    safe = key.replace("/", "_").replace(":", "_")
    return os.path.join(CACHE_DIR, f"{safe}.json")

def get(key, ttl_minutes=60):
    path = _cache_path(key)
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        saved_at = datetime.fromisoformat(data["saved_at"])
        if datetime.now() - saved_at > timedelta(minutes=ttl_minutes):
            return None
        return data["value"]
    except Exception:
        return None

def set(key, value):
    path = _cache_path(key)
    with open(path, "w") as f:
        json.dump({"saved_at": datetime.now().isoformat(), "value": value}, f)

def invalidate(key):
    path = _cache_path(key)
    if os.path.exists(path):
        os.remove(path)
