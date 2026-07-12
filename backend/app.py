from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from api.health import router as health_router
from api.prediction import router as prediction_router
from api.chatbot import router as chatbot_router
from api.analytics import router as analytics_router

from config import APP_NAME, VERSION

app = FastAPI(
    title=APP_NAME,
    version=VERSION,
    description="""
Quick ETA Prediction Platform

Built with:
✔ FastAPI
✔ XGBoost (Locally trained and optimized)
✔ SHAP TreeExplainer
✔ Google Gemini AI
"""
)

# 1. Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Include Routers
app.include_router(
    health_router,
    tags=["Health"]
)

app.include_router(
    prediction_router,
    prefix="/api",
    tags=["Prediction"]
)

app.include_router(
    chatbot_router,
    prefix="/api",
    tags=["AI Assistant"]
)

app.include_router(
    analytics_router,
    prefix="/api",
    tags=["Analytics"]
)

# 3. Serve Frontend Static Files
static_dir = os.path.join(os.path.dirname(__file__), "static")
# Create static directory if it does not exist
os.makedirs(static_dir, exist_ok=True)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)