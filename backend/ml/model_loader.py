import joblib
import json
import pandas as pd
from pathlib import Path
from config import (
    MODEL_PATH,
    FEATURES_PATH,
    METRICS_PATH,
    SHAP_PATH,
    PROJECT_ROOT
)

# New encoder path
ENCODERS_PATH = MODEL_PATH.parent / "encoders.pkl"
RESTAURANTS_CSV_PATH = PROJECT_ROOT / "datasets" / "restaurants.csv"
RIDERS_CSV_PATH = PROJECT_ROOT / "datasets" / "riders.csv"

class ModelLoader:
    def __init__(self):
        # 1. Load ML Artifacts
        self.model = joblib.load(MODEL_PATH)
        self.features = joblib.load(FEATURES_PATH)
        self.encoders = joblib.load(ENCODERS_PATH)
        
        try:
            self.shap_values = joblib.load(SHAP_PATH)
        except Exception as e:
            print("Warning: SHAP values could not be loaded:", e)
            self.shap_values = None

        with open(METRICS_PATH, "r") as f:
            self.metrics = json.load(f)

        # 2. Load Dataset Tables for Quick Lookup
        self.restaurants_df = pd.read_csv(RESTAURANTS_CSV_PATH)
        self.riders_df = pd.read_csv(RIDERS_CSV_PATH)

        # Fill NaNs in lookup tables to match notebook preprocessing
        # Restaurants: fill avg_rating with its median, cuisine with mode
        self.restaurants_df["avg_rating"] = self.restaurants_df["avg_rating"].fillna(
            self.restaurants_df["avg_rating"].median()
        )
        self.restaurants_df["cuisine"] = self.restaurants_df["cuisine"].fillna(
            self.restaurants_df["cuisine"].mode()[0] if not self.restaurants_df["cuisine"].mode().empty else "Unknown"
        )
        self.restaurants_df["manager_contact"] = self.restaurants_df["manager_contact"].fillna("Unknown")

        # Riders: fill lat/lon with 0.0, vehicle_type with mode
        self.riders_df["lat"] = self.riders_df["lat"].fillna(0.0)
        self.riders_df["lon"] = self.riders_df["lon"].fillna(0.0)
        self.riders_df["vehicle_type"] = self.riders_df["vehicle_type"].fillna(
            self.riders_df["vehicle_type"].mode()[0] if not self.riders_df["vehicle_type"].mode().empty else "Unknown"
        )
        self.riders_df["rider_call_sign"] = self.riders_df["rider_call_sign"].fillna("Unknown")

        print("[OK] ML loader successfully initialized!")
        print(f"  Model      : {type(self.model).__name__}")
        print(f"  Features   : {len(self.features)} | Encoders: {len(self.encoders)}")
        print(f"  Restaurants: {len(self.restaurants_df)} | Riders: {len(self.riders_df)}")

loader = ModelLoader()