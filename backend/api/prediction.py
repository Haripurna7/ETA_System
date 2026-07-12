from fastapi import APIRouter, HTTPException, Depends
from schemas import PredictionRequest, PredictionResponse, RestaurantSchema, RiderSchema
from ml.model_loader import loader
from ml.features import engineer_features
import pandas as pd
import numpy as np
from typing import List

router = APIRouter()

@router.get("/restaurants", response_model=List[RestaurantSchema])
def get_restaurants():
    """
    Returns the list of all available restaurants.
    """
    # Convert dataframe to records
    records = loader.restaurants_df.to_dict(orient="records")
    return records

@router.get("/riders", response_model=List[RiderSchema])
def get_riders():
    """
    Returns the list of all available riders.
    """
    records = loader.riders_df.to_dict(orient="records")
    return records

@router.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    """
    Accepts delivery information, performs feature engineering, and returns the predicted ETA.
    """
    # 1. Lookup Restaurant
    restaurant_match = loader.restaurants_df[loader.restaurants_df["id"] == request.restaurant_id]
    if restaurant_match.empty:
        raise HTTPException(status_code=404, detail=f"Restaurant with ID {request.restaurant_id} not found.")
    restaurant = restaurant_match.iloc[0].to_dict()

    # 2. Lookup Rider
    rider_match = loader.riders_df[loader.riders_df["id"] == request.rider_id]
    if rider_match.empty:
        raise HTTPException(status_code=404, detail=f"Rider with ID {request.rider_id} not found.")
    rider = rider_match.iloc[0].to_dict()

    # 3. Formulate Raw Row
    # Use current time as timestamp
    now = pd.Timestamp.now()
    
    raw_data = {
        "drop_lat": [request.drop_lat],
        "drop_lon": [request.drop_lon],
        "order_size": [request.order_size],
        "order_value": [request.order_value if request.order_value is not None else request.order_size * 200.0],
        "promised_eta": [30.0],  # Default promised ETA
        "order_status": ["delivered"],
        "promo_code_used": [request.promo_code_used if request.promo_code_used is not None else "Unknown"],
        "lat": [restaurant["lat"]],
        "lon": [restaurant["lon"]],
        "cuisine": [restaurant["cuisine"]],
        "avg_rating": [restaurant["avg_rating"]],
        "prep_capacity": [restaurant["prep_capacity"]],
        "manager_contact": [restaurant["manager_contact"]],
        "lat_rider": [rider["lat"]],
        "lon_rider": [rider["lon"]],
        "vehicle_type": [request.vehicle_type if request.vehicle_type is not None else rider["vehicle_type"]],
        "completed_orders": [rider["completed_orders"]],
        "shift_hours": [rider["shift_hours"]],
        "current_load": [rider["current_load"]],
        "rider_call_sign": [rider["rider_call_sign"]],
        "timestamp": [now.strftime("%Y-%m-%d %H:%M:%S")]
    }

    raw_df = pd.DataFrame(raw_data)

    try:
        # 4. Feature Engineering
        engineered_df = engineer_features(raw_df, loader.encoders, loader.features)
        engineered_row = engineered_df.iloc[0].to_dict()

        # 5. Predict Model
        pred_eta = float(loader.model.predict(engineered_df)[0])
        # Ensure predicted ETA is positive
        pred_eta = max(1.0, pred_eta)

        # 6. Calculate Confidence Intervals (using model MAE as standard deviation indicator)
        mae = loader.metrics.get("MAE", 4.0)
        confidence_lower = max(1.0, pred_eta - mae)
        confidence_upper = pred_eta + mae

        # 7. Formulate Prediction Summary
        distance = engineered_row["restaurant_customer_distance"]
        travel_time = engineered_row["estimated_travel_time"]
        traffic_level = request.vehicle_type if request.vehicle_type else rider["vehicle_type"]
        
        summary = (
            f"Delivery distance is {distance:.2f} km. Travel time is estimated at {travel_time:.1f} minutes "
            f"using a {traffic_level}. Restaurant prep capacity is {restaurant['prep_capacity']} orders/hr "
            f"with an average rating of {restaurant['avg_rating']} stars."
        )

        return PredictionResponse(
            predicted_eta=round(pred_eta, 2),
            confidence_lower=round(confidence_lower, 2),
            confidence_upper=round(confidence_upper, 2),
            restaurant_name=restaurant["name"],
            rider_call_sign=rider["rider_call_sign"],
            distance_km=round(distance, 2),
            estimated_travel_time=round(travel_time, 2),
            summary=summary,
            features_engineered=engineered_row
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during feature engineering or prediction: {str(e)}")