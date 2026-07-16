# ⚡ Quick ETA Prediction Platform

> **A production-grade, end-to-end Machine Learning platform for real-time delivery ETA prediction, powered by XGBoost, SHAP explainability, and Google Gemini AI.**

## 📖 Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Project Structure](#project-structure)
5. [Dataset Overview](#dataset-overview)
6. [ML Pipeline](#ml-pipeline)
7. [API Reference](#api-reference)
8. [Frontend UI](#frontend-ui)
9. [Installation & Setup](#installation--setup)
10. [Running the Platform](#running-the-platform)
11. [Running Tests](#running-tests)
12. [Environment Variables](#environment-variables)
13. [Model Performance](#model-performance)
14. [Tech Stack](#tech-stack)

---

## 🎯 Project Overview

Fully-integrated Quick Commerce ETA (Estimated Time of Arrival) Prediction Platform for delivery logistics. Given an order — including restaurant, rider, drop-off coordinates, and order details — the platform predicts the delivery time with confidence bounds in real time.

The system combines:
- 🤖 **XGBoost Regression** trained on a merged dataset of orders, restaurants, and riders
- 🧠 **SHAP TreeExplainer** for model transparency and explainability
- 🌐 **FastAPI** RESTful backend with auto-generated OpenAPI docs
- 💬 **Google Gemini AI** assistant for interactive Q&A about predictions and the model
- 🎨 **Premium dark-themed glassmorphism UI** for the delivery simulation dashboard

---

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Browser (User)                     │
│         Glassmorphism Dark UI (HTML/CSS/JS)          │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP Requests
┌──────────────────────▼──────────────────────────────┐
│                  FastAPI Backend                      │
│  ┌────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │  /predict  │  │  /chat       │  │ /restaurants│  │
│  │  XGBoost   │  │  Gemini AI   │  │ /riders     │  │
│  └─────┬──────┘  └──────┬───────┘  └─────────────┘  │
│        │                │                             │
│  ┌─────▼──────┐  ┌──────▼───────┐                   │
│  │  ML Module │  │  AI Module   │                   │
│  │ features.py│  │ chatbot.py   │                   │
│  │ model_load │  │              │                   │
│  └─────┬──────┘  └──────────────┘                   │
└────────┼────────────────────────────────────────────┘
         │
┌────────▼────────────────────────────────────────────┐
│            Trained ML Artifacts (models/)             │
│  model.pkl │ encoders.pkl │ features.pkl │ shap_values│
└─────────────────────────────────────────────────────┘
```

---

## ✨ Features

| Feature | Description |
|---|---|
| 🎯 **Real-time ETA Prediction** | XGBoost model predicts delivery time with MAE-based confidence intervals |
| 📍 **Haversine Distance** | Precise rider→restaurant and restaurant→customer distances using Haversine formula |
| 🕒 **Temporal Features** | Peak-hour, traffic level, weekend detection from order timestamp |
| 🏍️ **Vehicle Speed Mapping** | Speed-based travel time estimation per vehicle type (bike, scooter, car, bicycle) |
| 🎭 **Rider Experience Scoring** | Experience classification (Beginner/Intermediate/Expert) from completed order count |
| 📊 **SHAP Explainability** | Feature importance values from TreeExplainer to explain each prediction |
| 🤖 **Gemini AI Chat** | AI assistant to explain predictions, model, EDA, and dataset facts |
| 🔁 **Rule-based Fallback** | When no Gemini API key is provided, a built-in rule-based chatbot responds |
| 🌐 **REST API** | Full OpenAPI/Swagger documentation auto-generated at `/docs` |
| 📦 **Full Test Suite** | 30+ integration & unit tests covering all endpoints and feature logic |

---

## 📁 Project Structure

```
ETA_prediction_system/
│
├── backend/                          # FastAPI server
│   ├── app.py                        # Application entry point
│   ├── config.py                     # Paths and configuration
│   ├── schemas.py                    # Pydantic request/response models
│   ├── requirements.txt              # Python dependencies
│   ├── test_api.py                   # Integration & unit test suite
│   │
│   ├── api/                          # Route handlers
│   │   ├── __init__.py
│   │   ├── health.py                 # GET /health
│   │   ├── prediction.py             # GET /api/restaurants, /api/riders, POST /api/predict
│   │   └── chatbot.py                # POST /api/chat
│   │
│   ├── ml/                           # ML logic
│   │   ├── features.py               # Feature engineering pipeline
│   │   └── model_loader.py           # Artifact loading (model, encoders, SHAP)
│   │
│   └── static/                       # Frontend (served by FastAPI)
│       ├── index.html                # Main UI
│       ├── style.css                 # Dark glassmorphism design
│       └── app.js                    # UI interactions & API calls
│
├── datasets/                         # Input data
│   ├── orders.csv                    # Raw orders (timestamp, order info)
│   ├── restaurants.csv               # Restaurant metadata (lat, lon, cuisine, etc.)
│   ├── riders.csv                    # Rider metadata (vehicle, experience, etc.)
│   ├── merged_data.csv               # Merged orders + restaurants + riders
│   └── final_dataset.csv             # After cleaning & feature engineering
│
├── models/                           # Saved ML artifacts
│   ├── model.pkl                     # Trained XGBoost regressor
│   ├── encoders.pkl                  # LabelEncoder dict for categorical features
│   ├── features.pkl                  # Ordered feature column names
│   ├── metrics.json                  # Model evaluation metrics (MAE, RMSE, R²)
│   ├── shap_values.pkl               # SHAP values for prediction explanation
│   ├── feature_importance.csv        # XGBoost feature importances
│   ├── feature_importance.png        # Feature importance bar chart
│   ├── model_info.json               # Model hyperparameters
│   └── shap_summary.png              # SHAP summary plot
│
└── notebooks/
    └── Model_train.ipynb             # Full EDA + training notebook
```

---

## 📊 Dataset Overview

The platform uses three merged CSV datasets:

### `orders.csv`
| Column | Description |
|---|---|
| `order_id` | Unique order identifier |
| `restaurant_id` | Linked restaurant |
| `rider_id` | Assigned delivery rider |
| `drop_lat`, `drop_lon` | Customer drop-off GPS coordinates |
| `order_size` | Number of items ordered |
| `order_value` | Order value in INR |
| `promised_eta` | Operator-promised delivery time |
| `actual_delivery_time` | **Target variable** — actual delivery duration (minutes) |
| `timestamp` | Order placement datetime |
| `promo_code_used` | Promotional code applied |

### `restaurants.csv`
| Column | Description |
|---|---|
| `id` | Unique restaurant identifier |
| `name` | Restaurant name |
| `lat`, `lon` | Restaurant GPS coordinates |
| `cuisine` | Food category |
| `avg_rating` | Average customer rating |
| `prep_capacity` | Orders prepared per hour |

### `riders.csv`
| Column | Description |
|---|---|
| `id` | Unique rider identifier |
| `rider_call_sign` | Unique rider alias |
| `lat`, `lon` | Current rider GPS location |
| `vehicle_type` | Transportation mode |
| `completed_orders` | Lifetime completed deliveries |
| `shift_hours` | Current shift duration |
| `current_load` | Active orders being carried |

---

## 🤖 ML Pipeline

### Engineered Features (35 total)

| Feature | Source | Description |
|---|---|---|
| `hour`, `day`, `month`, `weekday` | `timestamp` | Temporal decomposition |
| `is_weekend` | `weekday` | Weekend indicator |
| `peak_hour` | `hour` | Lunch (11–14) or dinner (18–22) rush |
| `traffic` | `hour` | Low/Medium/High/Very High level |
| `rider_restaurant_distance` | GPS | Haversine km from rider to restaurant |
| `restaurant_customer_distance` | GPS | Haversine km from restaurant to customer |
| `load_per_shift` | `current_load`, `shift_hours` | Rider workload intensity |
| `rider_experience` | `completed_orders` | Beginner/Intermediate/Expert |
| `restaurant_efficiency` | `prep_capacity × avg_rating` | Composite prep efficiency score |
| `vehicle_speed` | `vehicle_type` | Speed lookup (bike=30, scooter=35, car=40, bicycle=15 km/h) |
| `estimated_travel_time` | `distance / speed × 60` | Pre-calculated travel time (minutes) |
| `order_category` | `order_size` | Small/Medium/Large classification |
| Encoded categoricals | LabelEncoder | `cuisine`, `traffic`, `vehicle_type`, `rider_experience`, etc. |

### Model: XGBoost Regressor

```python
XGBRegressor(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)
```

### Training Strategy
- **80/20 train-test split** with `random_state=42`
- Label encoding for all categorical features
- SHAP TreeExplainer for post-hoc feature attribution

---

## 🌐 API Reference

Base URL: `http://127.0.0.1:8000`

> Interactive docs: **http://127.0.0.1:8000/docs**

---

### `GET /health`
Returns server health status.

**Response:**
```json
{ "status": "ok" }
```

---

### `GET /api/restaurants`
Returns all restaurants with ID, location, and metadata.

**Response (array):**
```json
[
  {
    "id": 1,
    "name": "The Biryani House",
    "lat": 12.9716,
    "lon": 77.5946,
    "cuisine": "Indian",
    "avg_rating": 4.3,
    "prep_capacity": 45
  }
]
```

---

### `GET /api/riders`
Returns all riders with ID, vehicle type, and workload info.

**Response (array):**
```json
[
  {
    "id": 101,
    "lat": 12.9600,
    "lon": 77.6100,
    "vehicle_type": "scooter",
    "completed_orders": 1240,
    "shift_hours": 5.5,
    "current_load": 1,
    "rider_call_sign": "FALCON-42"
  }
]
```

---

### `POST /api/predict`
Runs the XGBoost model and returns the predicted ETA.

**Request:**
```json
{
  "restaurant_id": 1,
  "rider_id": 101,
  "drop_lat": 12.9715987,
  "drop_lon": 77.5945627,
  "order_size": 3,
  "vehicle_type": "scooter",      // optional override
  "order_value": 750.0,            // optional
  "promo_code_used": "BLR10"       // optional
}
```

**Response:**
```json
{
  "predicted_eta": 28.45,
  "confidence_lower": 24.21,
  "confidence_upper": 32.69,
  "unit": "minutes",
  "summary": "Delivery distance is 4.21 km. Travel time is estimated at 7.2 minutes...",
  "restaurant_name": "The Biryani House",
  "rider_call_sign": "FALCON-42",
  "distance_km": 4.21,
  "estimated_travel_time": 7.22,
  "features_engineered": { ... }
}
```

---

### `POST /api/chat`
Ask the AI assistant about predictions, the model, or EDA findings.

**Request:**
```json
{
  "question": "Why was this ETA predicted?",
  "prediction_context": {
    "predicted_eta": 28.45,
    "distance_km": 4.21,
    "restaurant_name": "The Biryani House",
    "rider_call_sign": "FALCON-42"
  },
  "api_key": "AIzaSy..."  // optional Gemini API key
}
```

**Response:**
```json
{
  "answer": "Based on the current prediction context, the 28.45 minute ETA was calculated primarily due to the 4.21 km delivery distance. The XGBoost model weighted distance and estimated travel time as the top contributing factors..."
}
```

---

## 🎨 Frontend UI

The dashboard is a fully interactive single-page application:

- **Delivery Simulator** (left panel) — configure restaurant, rider, vehicle, and order parameters
- **Results Panel** (right panel) — shows ETA, confidence bounds, key metric cards, and factor bar charts
- **AI Assistant** — embedded chat drawer with quick-prompt buttons and real-time Gemini/rule-based responses
- **Settings Modal** — Gemini API key storage (browser localStorage)

Design highlights:
- 🌑 **Dark glassmorphism** aesthetic
- ✨ **Animated glowing submit button**
- 📊 **Animated CSS bar charts** for factor visualization
- 🔄 **Live server status indicator** in header

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.9+
- `pip`
- Virtual environment (recommended)

### 1. Clone / Open the project
```bash
cd ETA_prediction_system
```

### 2. Create and activate virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r backend/requirements.txt
```

### 4. Ensure model artifacts are present
Verify the `models/` directory contains:
```
models/
  model.pkl
  encoders.pkl
  features.pkl
  metrics.json
  shap_values.pkl
```

> If models are missing, open and run all cells in `notebooks/Model_train.ipynb` to train and save the artifacts.

---

## ▶️ Running the Platform

```bash
cd backend
uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

Then open your browser at:

**http://127.0.0.1:8000**

Interactive API docs are at:

**http://127.0.0.1:8000/docs**

---

## 🧪 Running Tests

```bash
cd backend

# Option 1: Run standalone (colorized output)
python test_api.py

# Option 2: Run with pytest (detailed output)
pip install pytest httpx
python -m pytest test_api.py -v
```

**Test coverage includes:**
- ✅ Health endpoint
- ✅ Restaurants and Riders list endpoints
- ✅ Prediction endpoint (valid, invalid IDs, missing fields, optional overrides)
- ✅ Chat endpoint (various question types, with/without context)
- ✅ Feature engineering unit tests (Haversine, peak hour, traffic, experience, order category)
- ✅ Model artifact loading

---

## 🔑 Environment Variables

| Variable | Description | Required |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API key for AI assistant | Optional |

You can also set the Gemini API key through the **Settings** gear icon in the UI — it will be saved to browser `localStorage` and sent with each chat request.

To set globally, create a `.env` file in the `backend/` directory:
```env
GEMINI_API_KEY=AIzaSy...
```

---

## 📈 Model Performance

| Metric | Value |
|---|---|
| **MAE** | ~4.2 minutes |
| **RMSE** | ~6.1 minutes |
| **R² Score** | ~0.85 |

> Metrics are stored in `models/metrics.json` and loaded dynamically for confidence interval calculation.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **ML Model** | XGBoost (XGBRegressor) |
| **Explainability** | SHAP TreeExplainer |
| **Backend** | FastAPI + Uvicorn |
| **Data Processing** | Pandas + NumPy |
| **Model Persistence** | Joblib |
| **API Validation** | Pydantic v2 |
| **AI Assistant** | Google Gemini 1.5 Flash |
| **Frontend** | Vanilla HTML5, CSS3, JavaScript (ES6+) |
| **Icons** | FontAwesome 6 |
| **Fonts** | Google Fonts (Outfit, Plus Jakarta Sans) |
| **Testing** | Pytest + HTTPX (FastAPI TestClient) |

---

## 👨‍💻 Author

Built end-to-end as a demonstration of production-grade ML platform engineering:
- Feature engineering → model training → artifact serialization
- REST API design → integration testing → deployment
- Interactive frontend → AI assistant integration

---
Railway deployed : [etasystem-production.up.railway.app](https://etasystem-production.up.railway.app/)

* Making every delivery predictable.*
