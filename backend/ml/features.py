import pandas as pd
import numpy as np
from math import sin, cos, sqrt, atan2, radians

# Earth Radius in km
R = 6371

def haversine_vectorized(lat1, lon1, lat2, lon2):
    """
    Vectorized calculation of Haversine distance between two sets of coordinates.
    """
    lat1_r, lon1_r = np.radians(lat1), np.radians(lon1)
    lat2_r, lon2_r = np.radians(lat2), np.radians(lon2)
    dlon = lon2_r - lon1_r
    dlat = lat2_r - lat1_r
    a = np.sin(dlat/2)**2 + np.cos(lat1_r)*np.cos(lat2_r)*np.sin(dlon/2)**2
    c = 2*np.arctan2(np.sqrt(a), np.sqrt(1-a))
    return R * c

def peak_hour(hour_series):
    """
    Classify whether the hour is a peak hour.
    Peak hours: 11:00-14:00 (Lunch) and 18:00-22:00 (Dinner)
    """
    return (((hour_series >= 11) & (hour_series <= 14)) | ((hour_series >= 18) & (hour_series <= 22))).astype(int)

def traffic(hour_series):
    """
    Estimate traffic level based on hour of day.
    """
    conditions = [
        (hour_series >= 7) & (hour_series <= 10),
        (hour_series >= 11) & (hour_series <= 16),
        (hour_series >= 17) & (hour_series <= 21)
    ]
    choices = ["High", "Medium", "Very High"]
    return np.select(conditions, choices, default="Low")

def experience_vectorized(completed_orders_series):
    """
    Classify rider experience based on lifetime completed orders.
    """
    conditions = [
        completed_orders_series < 500,
        (completed_orders_series >= 500) & (completed_orders_series < 2000)
    ]
    choices = ["Beginner", "Intermediate"]
    return np.select(conditions, choices, default="Expert")

def order_category_vectorized(order_size_series):
    """
    Classify order size into Small, Medium, or Large.
    """
    conditions = [
        order_size_series <= 2,
        (order_size_series > 2) & (order_size_series <= 5)
    ]
    choices = ["Small", "Medium"]
    return np.select(conditions, choices, default="Large")

def engineer_features(raw_data: pd.DataFrame, encoders: dict, feature_names: list) -> pd.DataFrame:
    """
    Processes raw input dataframe, engineers all 35 features,
    applies label encoding, and orders columns exactly as expected by the model.
    """
    df = raw_data.copy()

    # 1. Handle Timestamp
    df["timestamp"] = pd.to_datetime(df["timestamp"], format='mixed', dayfirst=True, errors='coerce')
    df["hour"] = df["timestamp"].dt.hour.fillna(12).astype(int)
    df["day"] = df["timestamp"].dt.day.fillna(1).astype(int)
    df["month"] = df["timestamp"].dt.month.fillna(1).astype(int)
    df["weekday"] = df["timestamp"].dt.weekday.fillna(0).astype(int)
    df["is_weekend"] = df["weekday"].isin([5, 6]).astype(int)

    # 2. Derived features from inputs
    df["peak_hour"] = peak_hour(df["hour"])
    df["traffic"] = traffic(df["hour"])

    df["rider_restaurant_distance"] = haversine_vectorized(
        df["lat_rider"], df["lon_rider"], df["lat"], df["lon"]
    )

    df["restaurant_customer_distance"] = haversine_vectorized(
        df["lat"], df["lon"], df["drop_lat"], df["drop_lon"]
    )

    df["load_per_shift"] = df["current_load"] / (df["shift_hours"] + 1)
    df["rider_experience"] = experience_vectorized(df["completed_orders"])
    df["restaurant_efficiency"] = df["prep_capacity"] * df["avg_rating"]

    vehicle_speed_map = {
        "bike": 30.0,
        "scooter": 35.0,
        "bicycle": 15.0,
        "car": 40.0
    }
    # Map speed and handle missing/invalid vehicle types
    df["vehicle_speed"] = df["vehicle_type"].map(vehicle_speed_map).fillna(30.0)

    df["estimated_travel_time"] = (df["restaurant_customer_distance"] / df["vehicle_speed"]) * 60.0
    df["order_category"] = order_category_vectorized(df["order_size"])

    # 3. Label encode categorical columns
    categorical_cols = [
        'cuisine', 'order_status', 'promo_code_used', 'manager_contact', 
        'vehicle_type', 'rider_call_sign', 'traffic', 'rider_experience', 'order_category'
    ]

    for col in categorical_cols:
        if col in df.columns:
            le = encoders[col]
            # Ensure values are strings, fill nans with mode or a default class
            val_series = df[col].astype(str).fillna(le.classes_[0])
            
            # Map unseen values to the first class in the encoder to prevent crashes
            # (Very robust for production environment!)
            val_series = val_series.apply(lambda x: x if x in le.classes_ else le.classes_[0])
            df[col] = le.transform(val_series)

    # 4. Reorder and select features exactly as expected by the model
    # If any feature is missing, fill with 0.0
    for col in feature_names:
        if col not in df.columns:
            df[col] = 0.0

    return df[feature_names]
