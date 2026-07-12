from pathlib import Path

# =====================================================
# Project Directories
# =====================================================

# backend/
BACKEND_DIR = Path(__file__).resolve().parent

# ETA_prediction_system/
PROJECT_ROOT = BACKEND_DIR.parent

# =====================================================
# Models Directory
# =====================================================

MODELS_DIR = PROJECT_ROOT / "models"

MODEL_PATH = MODELS_DIR / "model.pkl"

FEATURES_PATH = MODELS_DIR / "features.pkl"

METRICS_PATH = MODELS_DIR / "metrics.json"

FEATURE_IMPORTANCE_PATH = MODELS_DIR / "feature_importance.csv"

SHAP_PATH = MODELS_DIR / "shap_values.pkl"

# =====================================================
# API Configuration
# =====================================================

APP_NAME = "ETA Prediction API"

VERSION = "1.0.0"

HOST = "127.0.0.1"

PORT = 8000

# =====================================================
# Debug (Remove Later)
# =====================================================

if __name__ == "__main__":
    print("Project Root :", PROJECT_ROOT)
    print("Models Folder:", MODELS_DIR)
    print("Model Exists :", MODEL_PATH.exists())
    print("Model Path   :", MODEL_PATH)