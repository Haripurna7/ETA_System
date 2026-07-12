from fastapi import APIRouter, HTTPException
from schemas import ChatRequest, ChatResponse
from ml.model_loader import loader
import os
try:
    from google import genai as genai_new
    _GENAI_NEW = True
except ImportError:
    try:
        import google.generativeai as genai_old
        _GENAI_NEW = False
    except ImportError:
        genai_old = None
        _GENAI_NEW = False

router = APIRouter()

# Top 10 feature importances for explanation context
TOP_FEATURES = [
    ("restaurant_customer_distance", "Distance between the restaurant and the customer drop-off location (highest impact)."),
    ("estimated_travel_time", "Estimated travel time computed from distance and vehicle type speed."),
    ("prep_capacity", "The restaurant's kitchen preparation capacity (orders they can handle in parallel per hour)."),
    ("avg_rating", "Historical average customer rating of the restaurant (indicates food prep efficiency)."),
    ("completed_orders", "Rider's lifetime completed orders (higher means more experienced, reducing delivery time)."),
    ("current_load", "The number of active orders currently assigned to the rider."),
    ("traffic", "Estimated traffic level based on time of day (High, Medium, Very High, Low)."),
    ("rider_restaurant_distance", "Distance between the rider's last known location and the restaurant."),
    ("load_per_shift", "The ratio of rider's current load to their shift hours."),
    ("vehicle_type", "The vehicle type being used (car, scooter, bike, bicycle).")
]

def get_rule_based_fallback(question: str, context: dict = None) -> str:
    """
    Local heuristic fallback engine that answers questions if Gemini API key is missing.
    """
    q_lower = question.lower()
    
    # 1. Explain prediction / why predicted
    if "why" in q_lower or "explain this prediction" in q_lower or "explain" in q_lower and context:
        eta = context.get("predicted_eta", "N/A")
        rest = context.get("restaurant_name", "the restaurant")
        rider = context.get("rider_call_sign", "the rider")
        dist = context.get("distance_km", 0.0)
        travel = context.get("estimated_travel_time", 0.0)
        features = context.get("features_engineered", {})
        
        vehicle = features.get("vehicle_type", "vehicle")
        # Reverse encode vehicle if needed
        # In our case, we can look up from raw request or just display the text
        
        explanation = (
            f"### Local Heuristic Explanation\n"
            f"The predicted delivery ETA is **{eta} minutes**.\n\n"
            f"**Key contributing factors:**\n"
            f"- **Travel Distance**: The customer is **{dist:.2f} km** away from **{rest}**, resulting in an estimated travel time of **{travel:.1f} minutes**.\n"
            f"- **Restaurant Prep**: The restaurant has a prep capacity of **{features.get('prep_capacity', 'N/A')} orders/hour** and an average rating of **{features.get('avg_rating', 'N/A')}** stars.\n"
            f"- **Rider Workload**: Courier **{rider}** has a current load of **{features.get('current_load', 0)}** active orders in this shift, with **{features.get('completed_orders', 0)}** lifetime completed orders.\n"
            f"- **Model Bounds**: Our XGBoost model predicts with a Mean Absolute Error (MAE) of ±**3.96 minutes**."
        )
        return explanation
        
    # 2. Factors affecting prediction
    if "factors" in q_lower or "features" in q_lower or "importance" in q_lower:
        explanation = (
            "### Feature Importance (XGBoost)\n"
            "Here are the top factors that influence our ETA predictions, ranked by their importance in the model:\n\n"
        )
        for i, (feat, desc) in enumerate(TOP_FEATURES, 1):
            explanation += f"{i}. **{feat}**: {desc}\n"
        return explanation

    # 3. Summarize dataset
    if "dataset" in q_lower or "summarize" in q_lower:
        explanation = (
            "### Dataset Summary\n"
            "The ETA prediction engine was trained on historical quick-commerce delivery logs containing:\n"
            f"- **Restaurants**: {len(loader.restaurants_df)} unique outlets across 10 cuisine types.\n"
            f"- **Riders**: {len(loader.riders_df)} active delivery partners using 4 vehicle types (bike, scooter, bicycle, car).\n"
            f"- **Training Dataset**: Over 70,000 merged delivery records with GPS coordinates, order size, value, timestamps, and actual delivery times.\n"
            f"- **Data Quality Notes**: The raw dataset contained missing coordinates, NaN average ratings, and duplicate entries, which were cleaned using median/mode imputation."
        )
        return explanation

    # 4. Explain EDA observations
    if "eda" in q_lower or "observation" in q_lower or "analysis" in q_lower:
        explanation = (
            "### Exploratory Data Analysis (EDA) Insights\n"
            "Key findings from our exploratory analysis include:\n"
            "1. **Distance vs. ETA**: Travel distance has a linear correlation with delivery times. Long-distance drop-offs significantly spike the ETA.\n"
            "2. **Vehicle Speed**: Average speeds differ significantly: Cars (~40 km/h) and Scooters (~35 km/h) deliver faster than Bikes (~30 km/h) and Bicycles (~15 km/h).\n"
            "3. **Peak Hours**: Meal times (11:00-14:00 and 18:00-22:00) show a 15-20% increase in actual delivery times due to cooking backlog and high traffic.\n"
            "4. **Rider Experience**: Delivery partners with >1000 completed orders average 3.5 minutes faster delivery cycles than beginners (<500 orders).\n"
            "5. **Outlier GPS**: Some raw records had coordinates in the middle of the ocean (0,0) or outside Bengaluru (the primary region). These were filtered out."
        )
        return explanation

    # General fallback response
    return (
        "Hello! I am the EulerQ Quick Commerce AI Assistant.\n\n"
        "I can answer questions like:\n"
        "- *Why was this ETA predicted?* (Please run a prediction first)\n"
        "- *Which factors affected the prediction?*\n"
        "- *Summarize the dataset.*\n"
        "- *Explain EDA observations.*\n\n"
        "*(Configure your GEMINI_API_KEY in a .env file or in the top-right settings menu of the UI for advanced natural language responses!)*"
    )

@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Accepts customer queries, injects prediction context, and returns AI responses using Gemini or local fallback.
    """
    # 1. Determine API Key
    api_key = request.api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    
    # 2. Check if key is empty or dummy
    if not api_key or api_key.strip() == "" or api_key == "YOUR_API_KEY":
        # Fall back to local rule-based response
        ans = get_rule_based_fallback(request.question, request.prediction_context)
        return ChatResponse(answer=ans)

    try:
        # 3. Configure and call Gemini
        
        # 4. Formulate System Context and Prompt
        system_context = (
            "You are EulerQ's Quick Commerce ETA Assistant. You help users understand estimated delivery times, "
            "explain factors that affect deliveries, and summarize our machine learning dataset and Exploratory Data Analysis (EDA).\n\n"
            "### MODEL & PERFORMANCE DETAILS:\n"
            "- Algorithm: XGBoost Regressor (Tuned with GridSearchCV)\n"
            "- Mean Absolute Error (MAE): 3.96 minutes\n"
            "- Root Mean Squared Error (RMSE): 19.98 minutes\n"
            "- R2 Score: 0.9812\n\n"
            "### TOP FEATURES INFLUENCING PREDICTIONS (SHAP Importance):\n"
        )
        for feat, desc in TOP_FEATURES:
            system_context += f"- {feat}: {desc}\n"
            
        system_context += (
            "\n### EXPLORATORY DATA ANALYSIS (EDA) OBSERVATIONS:\n"
            "1. Distance between restaurant and customer is the primary factor.\n"
            "2. Kitchen preparation backlog and time-of-day traffic peak during 11:00-14:00 and 18:00-22:00.\n"
            "3. Rider experience (completed orders) significantly reduces delivery times.\n"
            "4. Vehicle speeds: Car (40km/h), Scooter (35km/h), Bike (30km/h), Bicycle (15km/h).\n"
            "5. Missing value ratios: avg_rating had ~10% NaNs, drop coordinates had ~17% NaNs, which were median/mode imputed.\n"
        )

        if request.prediction_context:
            ctx = request.prediction_context
            features = ctx.get("features_engineered", {})
            system_context += (
                f"\n### CURRENT PREDICTION CONTEXT:\n"
                f"- Predicted ETA: {ctx.get('predicted_eta')} minutes\n"
                f"- Restaurant: {ctx.get('restaurant_name')} (Cuisine: {features.get('cuisine')}, Prep Capacity: {features.get('prep_capacity')} orders/hr, Avg Rating: {features.get('avg_rating')} stars)\n"
                f"- Rider Call Sign: {ctx.get('rider_call_sign')} (Vehicle Type: {features.get('vehicle_type')}, Completed Orders: {features.get('completed_orders')}, Current Load: {features.get('current_load')}, Shift Hours: {features.get('shift_hours')})\n"
                f"- Delivery Distance: {ctx.get('distance_km')} km\n"
                f"- Estimated Travel Time: {ctx.get('estimated_travel_time')} minutes\n"
                f"- Time of Day: Hour {features.get('hour')}, Weekday {features.get('weekday')}, Is Weekend: {features.get('is_weekend')}\n"
                f"- Current Traffic Level: {features.get('traffic')}\n"
                f"- Order Size: {features.get('order_size')} items, Order Value: {features.get('order_value')} currency units\n"
            )
        else:
            system_context += "\n(Note: No active prediction context. If the user asks about a specific delivery, ask them to make a prediction first.)\n"

        prompt = (
            f"System Context:\n{system_context}\n\n"
            f"User Question: {request.question}\n\n"
            f"Instructions: Please answer the user's question clearly, concisely, and conversationally in Markdown format. "
            f"Keep your tone helpful, professional, and friendly. Reference the model metrics, feature importances, or current context where relevant."
        )

        # 5. Call Gemini (supports both old and new SDK)
        if _GENAI_NEW:
            client = genai_new.Client(api_key=api_key)
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt
            )
            answer = response.text
        else:
            genai_old.configure(api_key=api_key)
            model = genai_old.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            answer = response.text
        return ChatResponse(answer=answer)

    except Exception as e:
        # Fall back to rule-based on any API error
        fallback_ans = (
            f"*(Gemini API Call failed with: {str(e)}. Falling back to local engine)*\n\n"
            + get_rule_based_fallback(request.question, request.prediction_context)
        )
        return ChatResponse(answer=fallback_ans)