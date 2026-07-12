# Use official lightweight Python image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set working directory inside the container
WORKDIR /app

# Install system dependencies (build-essential is useful for C extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first to cache docker layer
COPY backend/requirements.txt /app/backend/requirements.txt

# Install python dependencies
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy dataset, models, and backend source files
COPY backend/ /app/backend/
COPY datasets/ /app/datasets/
COPY models/ /app/models/

# Set working directory to backend to ensure local python imports resolve correctly
WORKDIR /app/backend

# Expose FastAPI default port
EXPOSE 8000

# Command to run application using uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
