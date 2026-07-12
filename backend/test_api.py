"""
ETA Prediction API - Integration & Unit Test Suite
===================================================
Run with:
    cd backend
    python -m pytest test_api.py -v

Or run standalone:
    python test_api.py
"""

import sys
import os

# Ensure backend directory is on the path
sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

# ======================================================
# Helpers
# ======================================================

# Bangalore coordinates (realistic drop-off)
SAMPLE_LAT = 12.9715987
SAMPLE_LON = 77.5945627

def get_first_restaurant_id():
    """Fetch a valid restaurant ID from the API."""
    resp = client.get("/api/restaurants")
    assert resp.status_code == 200, f"Failed to fetch restaurants: {resp.text}"
    data = resp.json()
    assert len(data) > 0, "No restaurants returned"
    return data[0]["id"]

def get_first_rider_id():
    """Fetch a valid rider ID from the API."""
    resp = client.get("/api/riders")
    assert resp.status_code == 200, f"Failed to fetch riders: {resp.text}"
    data = resp.json()
    assert len(data) > 0, "No riders returned"
    return data[0]["id"]


# ======================================================
# 1. Health Check Tests
# ======================================================

class TestHealthEndpoint:

    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    def test_health_response_has_status_field(self):
        response = client.get("/health")
        body = response.json()
        assert "status" in body, f"No 'status' key in response: {body}"

    def test_health_status_is_ok(self):
        response = client.get("/health")
        body = response.json()
        assert body["status"] in ("ok", "healthy"), f"Status should be 'ok' or 'healthy', got: {body['status']}"


# ======================================================
# 2. Restaurants Endpoint Tests
# ======================================================

class TestRestaurantsEndpoint:

    def test_get_restaurants_200(self):
        response = client.get("/api/restaurants")
        assert response.status_code == 200

    def test_restaurants_returns_list(self):
        response = client.get("/api/restaurants")
        data = response.json()
        assert isinstance(data, list), "Expected a list of restaurants"

    def test_restaurants_not_empty(self):
        response = client.get("/api/restaurants")
        data = response.json()
        assert len(data) > 0, "Restaurant list should not be empty"

    def test_restaurant_schema_fields(self):
        response = client.get("/api/restaurants")
        restaurant = response.json()[0]
        required_fields = ["id", "name", "lat", "lon", "cuisine", "avg_rating", "prep_capacity"]
        for field in required_fields:
            assert field in restaurant, f"Missing field '{field}' in restaurant schema: {restaurant.keys()}"


# ======================================================
# 3. Riders Endpoint Tests
# ======================================================

class TestRidersEndpoint:

    def test_get_riders_200(self):
        response = client.get("/api/riders")
        assert response.status_code == 200

    def test_riders_returns_list(self):
        response = client.get("/api/riders")
        data = response.json()
        assert isinstance(data, list), "Expected a list of riders"

    def test_riders_not_empty(self):
        response = client.get("/api/riders")
        data = response.json()
        assert len(data) > 0, "Rider list should not be empty"

    def test_rider_schema_fields(self):
        response = client.get("/api/riders")
        rider = response.json()[0]
        required_fields = ["id", "lat", "lon", "vehicle_type", "completed_orders",
                           "shift_hours", "current_load", "rider_call_sign"]
        for field in required_fields:
            assert field in rider, f"Missing field '{field}' in rider schema: {rider.keys()}"


# ======================================================
# 4. Prediction Endpoint Tests
# ======================================================

class TestPredictionEndpoint:

    def _base_payload(self):
        restaurant_id = get_first_restaurant_id()
        rider_id = get_first_rider_id()
        return {
            "restaurant_id": restaurant_id,
            "rider_id": rider_id,
            "drop_lat": SAMPLE_LAT,
            "drop_lon": SAMPLE_LON,
            "order_size": 3
        }

    def test_predict_200(self):
        payload = self._base_payload()
        response = client.post("/api/predict", json=payload)
        assert response.status_code == 200, f"Prediction failed: {response.text}"

    def test_predict_returns_eta(self):
        payload = self._base_payload()
        response = client.post("/api/predict", json=payload)
        data = response.json()
        assert "predicted_eta" in data, f"No 'predicted_eta' in response: {data.keys()}"

    def test_predict_eta_positive(self):
        payload = self._base_payload()
        response = client.post("/api/predict", json=payload)
        data = response.json()
        assert data["predicted_eta"] > 0, f"ETA should be positive, got: {data['predicted_eta']}"

    def test_predict_confidence_bounds_logical(self):
        payload = self._base_payload()
        response = client.post("/api/predict", json=payload)
        data = response.json()
        assert data["confidence_lower"] <= data["predicted_eta"], "Lower bound must be ≤ predicted ETA"
        assert data["confidence_upper"] >= data["predicted_eta"], "Upper bound must be ≥ predicted ETA"

    def test_predict_schema_complete(self):
        payload = self._base_payload()
        response = client.post("/api/predict", json=payload)
        data = response.json()
        required_fields = [
            "predicted_eta", "confidence_lower", "confidence_upper", "unit",
            "summary", "restaurant_name", "rider_call_sign", "distance_km",
            "estimated_travel_time", "features_engineered"
        ]
        for field in required_fields:
            assert field in data, f"Missing field '{field}' in prediction response"

    def test_predict_with_vehicle_override(self):
        payload = self._base_payload()
        payload["vehicle_type"] = "scooter"
        response = client.post("/api/predict", json=payload)
        assert response.status_code == 200, f"Vehicle override failed: {response.text}"

    def test_predict_with_order_value(self):
        payload = self._base_payload()
        payload["order_value"] = 850.0
        response = client.post("/api/predict", json=payload)
        assert response.status_code == 200

    def test_predict_with_promo_code(self):
        payload = self._base_payload()
        payload["promo_code_used"] = "WELCOME50"
        response = client.post("/api/predict", json=payload)
        assert response.status_code == 200

    def test_predict_with_all_optional_fields(self):
        payload = self._base_payload()
        payload["vehicle_type"] = "bike"
        payload["order_value"] = 1200.0
        payload["promo_code_used"] = "FREESHIP"
        response = client.post("/api/predict", json=payload)
        assert response.status_code == 200

    def test_predict_invalid_restaurant_returns_404(self):
        payload = self._base_payload()
        payload["restaurant_id"] = 999999  # Very unlikely to exist
        response = client.post("/api/predict", json=payload)
        assert response.status_code == 404, f"Expected 404 for invalid restaurant, got {response.status_code}"

    def test_predict_invalid_rider_returns_404(self):
        payload = self._base_payload()
        payload["rider_id"] = 999999
        response = client.post("/api/predict", json=payload)
        assert response.status_code == 404, f"Expected 404 for invalid rider, got {response.status_code}"

    def test_predict_missing_required_fields_returns_422(self):
        # Missing restaurant_id, rider_id, and coordinates
        response = client.post("/api/predict", json={"order_size": 3})
        assert response.status_code == 422, f"Expected 422 for missing fields, got {response.status_code}"

    def test_predict_distance_km_positive(self):
        payload = self._base_payload()
        response = client.post("/api/predict", json=payload)
        data = response.json()
        assert data["distance_km"] > 0, "distance_km must be positive"

    def test_predict_unit_is_minutes(self):
        payload = self._base_payload()
        response = client.post("/api/predict", json=payload)
        data = response.json()
        assert data["unit"] == "minutes", f"Unit should be 'minutes', got {data['unit']}"


# ======================================================
# 5. Chat / AI Assistant Tests
# ======================================================

class TestChatEndpoint:

    def test_chat_returns_200(self):
        response = client.post("/api/chat", json={"question": "What is ETA?"})
        assert response.status_code == 200, f"Chat failed: {response.text}"

    def test_chat_returns_answer_field(self):
        response = client.post("/api/chat", json={"question": "What is ETA?"})
        data = response.json()
        assert "answer" in data, f"No 'answer' field in chat response: {data}"

    def test_chat_answer_not_empty(self):
        response = client.post("/api/chat", json={"question": "What is ETA?"})
        data = response.json()
        assert len(data["answer"]) > 0, "Chat answer should not be empty"

    def test_chat_with_prediction_context(self):
        context = {
            "predicted_eta": 28.5,
            "distance_km": 4.2,
            "restaurant_name": "Test Restaurant",
            "rider_call_sign": "ALPHA-01"
        }
        response = client.post("/api/chat", json={
            "question": "Why is my delivery taking 28 minutes?",
            "prediction_context": context
        })
        assert response.status_code == 200

    def test_chat_eda_question(self):
        response = client.post("/api/chat", json={"question": "Explain the EDA observations."})
        assert response.status_code == 200

    def test_chat_model_question(self):
        response = client.post("/api/chat", json={"question": "How does the XGBoost model work?"})
        assert response.status_code == 200

    def test_chat_missing_question_returns_422(self):
        response = client.post("/api/chat", json={})
        assert response.status_code == 422


# ======================================================
# 6. Feature Engineering Unit Tests
# ======================================================

class TestFeatureEngineering:

    def _get_loader(self):
        from ml.model_loader import loader
        return loader

    def test_haversine_distance_reasonable(self):
        from ml.features import haversine_vectorized
        import numpy as np
        # Bangalore restaurant to Bangalore customer — should be ~few km, definitely not 0 or 1000+
        dist = haversine_vectorized(
            np.array([12.9716]), np.array([77.5946]),
            np.array([12.9352]), np.array([77.6245])
        )
        assert 1.0 < dist[0] < 100.0, f"Haversine distance seems unreasonable: {dist[0]} km"

    def test_peak_hour_classification(self):
        from ml.features import peak_hour
        import numpy as np
        # Lunch hour (12) -> peak
        assert peak_hour(np.array([12]))[0] == 1
        # Early morning (3AM) -> not peak
        assert peak_hour(np.array([3]))[0] == 0
        # Dinner hour (19) -> peak
        assert peak_hour(np.array([19]))[0] == 1

    def test_traffic_classification(self):
        from ml.features import traffic
        import numpy as np
        result = traffic(np.array([8]))   # Morning rush
        assert result[0] == "High"

        result = traffic(np.array([19]))  # Evening rush
        assert result[0] == "Very High"

        result = traffic(np.array([3]))   # Night
        assert result[0] == "Low"

    def test_experience_classification(self):
        from ml.features import experience_vectorized
        import numpy as np
        assert experience_vectorized(np.array([100]))[0] == "Beginner"
        assert experience_vectorized(np.array([1000]))[0] == "Intermediate"
        assert experience_vectorized(np.array([5000]))[0] == "Expert"

    def test_order_category_classification(self):
        from ml.features import order_category_vectorized
        import numpy as np
        assert order_category_vectorized(np.array([1]))[0] == "Small"
        assert order_category_vectorized(np.array([4]))[0] == "Medium"
        assert order_category_vectorized(np.array([10]))[0] == "Large"

    def test_model_loader_loads_successfully(self):
        loader = self._get_loader()
        assert loader.model is not None, "Model should not be None"
        assert loader.features is not None, "Features list should not be None"
        assert loader.encoders is not None, "Encoders should not be None"
        assert len(loader.features) > 0, "Features list should be non-empty"
        assert len(loader.encoders) > 0, "Encoders dict should be non-empty"

    def test_model_loader_datasets_loaded(self):
        loader = self._get_loader()
        assert len(loader.restaurants_df) > 0, "Restaurants DataFrame should not be empty"
        assert len(loader.riders_df) > 0, "Riders DataFrame should not be empty"


# ======================================================
# 7. Analytics Endpoint Tests
# ======================================================

class TestAnalyticsEndpoint:

    def test_get_stats_200(self):
        response = client.get("/api/stats")
        assert response.status_code == 200, f"Stats failed: {response.text}"

    def test_stats_schema_fields(self):
        response = client.get("/api/stats")
        data = response.json()
        required_fields = [
            "total_restaurants", "total_riders", "avg_restaurant_rating",
            "avg_rider_completed_orders", "vehicle_counts"
        ]
        for field in required_fields:
            assert field in data, f"Missing field '{field}' in stats schema"

    def test_stats_values_reasonable(self):
        response = client.get("/api/stats")
        data = response.json()
        assert data["total_restaurants"] > 0
        assert data["total_riders"] > 0
        assert 0.0 <= data["avg_restaurant_rating"] <= 5.0
        assert data["avg_rider_completed_orders"] >= 0
        assert isinstance(data["vehicle_counts"], dict)


# ======================================================
# Main – Run standalone
# ======================================================

if __name__ == "__main__":
    import traceback

    test_classes = [
        TestHealthEndpoint,
        TestRestaurantsEndpoint,
        TestRidersEndpoint,
        TestPredictionEndpoint,
        TestChatEndpoint,
        TestFeatureEngineering,
        TestAnalyticsEndpoint,
    ]

    total = 0
    passed = 0
    failed = 0
    errors = []

    print("\n" + "="*65)
    print("  ETA Prediction Platform - API Test Suite")
    print("="*65)

    for cls in test_classes:
        instance = cls()
        class_name = cls.__name__
        print(f"\n[{class_name}]")
        print("-" * 55)

        for name in [m for m in dir(cls) if m.startswith("test_")]:
            total += 1
            try:
                getattr(instance, name)()
                print(f"  [PASS]  {name}")
                passed += 1
            except AssertionError as e:
                failed += 1
                errors.append((class_name, name, str(e)))
                print(f"  [FAIL]  {name}")
                print(f"       -> {e}")
            except Exception as e:
                failed += 1
                tb = traceback.format_exc()
                errors.append((class_name, name, tb))
                print(f"  [ERR!]  {name} (Exception)")
                print(f"       -> {type(e).__name__}: {e}")

    print("\n" + "="*65)
    print(f"  Results: {passed}/{total} passed | {failed} failed")
    print("="*65)

    if errors:
        print("\n>> Failure Details:")
        for cls_name, test_name, msg in errors:
            print(f"\n  [{cls_name}] {test_name}")
            print(f"  {msg[:400]}")

    sys.exit(0 if failed == 0 else 1)
