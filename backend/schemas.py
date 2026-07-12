from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class PredictionRequest(BaseModel):
    restaurant_id: int = Field(..., description="ID of the restaurant")
    rider_id: int = Field(..., description="ID of the rider")
    drop_lat: float = Field(..., description="Customer drop-off latitude")
    drop_lon: float = Field(..., description="Customer drop-off longitude")
    order_size: int = Field(..., gt=0, description="Number of items in the order")
    vehicle_type: Optional[str] = Field(None, description="Optional override for vehicle type (bike/scooter/bicycle/car)")
    order_value: Optional[float] = Field(None, description="Optional override for order value in currency")
    promo_code_used: Optional[str] = Field(None, description="Optional promo code used")

class PredictionResponse(BaseModel):
    predicted_eta: float
    confidence_lower: float
    confidence_upper: float
    unit: str = "minutes"
    summary: str
    restaurant_name: str
    rider_call_sign: str
    distance_km: float
    estimated_travel_time: float
    features_engineered: Dict[str, Any]

class ChatRequest(BaseModel):
    question: str
    prediction_context: Optional[Dict[str, Any]] = None
    api_key: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str

class RestaurantSchema(BaseModel):
    id: int
    name: str
    lat: float
    lon: float
    cuisine: str
    avg_rating: float
    prep_capacity: int

class RiderSchema(BaseModel):
    id: int
    lat: float
    lon: float
    vehicle_type: str
    completed_orders: int
    shift_hours: float
    current_load: int
    rider_call_sign: str

class StatsResponse(BaseModel):
    total_restaurants: int
    total_riders: int
    avg_restaurant_rating: float
    avg_rider_completed_orders: float
    vehicle_counts: Dict[str, int]