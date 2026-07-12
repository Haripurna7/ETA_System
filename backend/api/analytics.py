from fastapi import APIRouter
from schemas import StatsResponse
from ml.model_loader import loader
from typing import Dict

router = APIRouter()

@router.get("/stats", response_model=StatsResponse)
def get_stats():
    """
    Returns high-level system statistics for the analytics dashboard.
    """
    total_rest = int(len(loader.restaurants_df))
    total_riders = int(len(loader.riders_df))
    
    avg_rating = 0.0
    if not loader.restaurants_df.empty and "avg_rating" in loader.restaurants_df.columns:
        avg_rating = float(loader.restaurants_df["avg_rating"].mean())
        
    avg_orders = 0.0
    if not loader.riders_df.empty and "completed_orders" in loader.riders_df.columns:
        avg_orders = float(loader.riders_df["completed_orders"].mean())
        
    vehicle_counts: Dict[str, int] = {}
    if not loader.riders_df.empty and "vehicle_type" in loader.riders_df.columns:
        counts = loader.riders_df["vehicle_type"].value_counts().to_dict()
        vehicle_counts = {str(k): int(v) for k, v in counts.items()}
        
    return StatsResponse(
        total_restaurants=total_rest,
        total_riders=total_riders,
        avg_restaurant_rating=round(avg_rating, 2),
        avg_rider_completed_orders=round(avg_orders, 1),
        vehicle_counts=vehicle_counts
    )
