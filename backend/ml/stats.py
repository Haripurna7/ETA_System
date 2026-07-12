"""
backend/ml/stats.py
====================
Thread-safe in-memory session statistics tracker.
Records every prediction for real-time analytics display.
"""
import threading
from datetime import datetime
from typing import Dict, Any, List

_lock = threading.Lock()

_session: Dict[str, Any] = {
    "total_predictions": 0,
    "total_eta_sum": 0.0,
    "vehicle_eta_totals": {},   # vehicle_type -> (count, eta_sum)
    "predictions": [],           # last 200 entries
}

VEHICLE_SPEED_MAP = {
    "bike": 30.0,
    "scooter": 35.0,
    "bicycle": 15.0,
    "car": 40.0,
    "unknown": 30.0,
}


def record_prediction(
    predicted_eta: float,
    distance_km: float,
    vehicle_type: str,
    restaurant_name: str,
    rider_call_sign: str,
    restaurant_lat: float,
    restaurant_lon: float,
    rider_lat: float,
    rider_lon: float,
    drop_lat: float,
    drop_lon: float,
    features: Dict[str, Any],
) -> None:
    """Records a single prediction into the session store."""
    vtype = str(vehicle_type).strip().lower()

    with _lock:
        _session["total_predictions"] += 1
        _session["total_eta_sum"] += predicted_eta

        # Per-vehicle ETA accumulation
        count, eta_sum = _session["vehicle_eta_totals"].get(vtype, (0, 0.0))
        _session["vehicle_eta_totals"][vtype] = (count + 1, eta_sum + predicted_eta)

        entry = {
            "id": _session["total_predictions"],
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "predicted_eta": round(predicted_eta, 2),
            "distance_km": round(distance_km, 3),
            "vehicle_type": vtype,
            "restaurant_name": restaurant_name,
            "rider_call_sign": rider_call_sign,
            # Map coordinates for replaying on the frontend
            "restaurant_lat": restaurant_lat,
            "restaurant_lon": restaurant_lon,
            "rider_lat": rider_lat,
            "rider_lon": rider_lon,
            "drop_lat": drop_lat,
            "drop_lon": drop_lon,
            # Feature flags for display
            "peak_hour": int(features.get("peak_hour", 0)),
            "is_weekend": int(features.get("is_weekend", 0)),
        }

        _session["predictions"].append(entry)
        # Cap at 200 entries
        if len(_session["predictions"]) > 200:
            _session["predictions"] = _session["predictions"][-200:]


def get_stats() -> Dict[str, Any]:
    """Returns aggregated session statistics."""
    with _lock:
        total = _session["total_predictions"]
        avg_eta = round(_session["total_eta_sum"] / total, 2) if total > 0 else 0.0

        vehicle_avg = {}
        for vtype, (cnt, eta_sum) in _session["vehicle_eta_totals"].items():
            vehicle_avg[vtype] = round(eta_sum / cnt, 2) if cnt > 0 else 0.0

        # Most used vehicle
        most_used = max(
            _session["vehicle_eta_totals"].items(),
            key=lambda x: x[1][0],
            default=("N/A", (0, 0)),
        )
        most_used_vehicle = most_used[0] if total > 0 else "N/A"

        return {
            "total_predictions": total,
            "avg_eta_minutes": avg_eta,
            "most_used_vehicle": most_used_vehicle,
            "vehicle_avg_eta": vehicle_avg,
            "vehicle_counts": {k: v[0] for k, v in _session["vehicle_eta_totals"].items()},
            "recent_predictions": list(reversed(_session["predictions"][-50:])),
            "trend_etas": [p["predicted_eta"] for p in _session["predictions"][-20:]],
        }
