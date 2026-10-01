# Dockerfile — Railway Backend API (FastAPI + Uvicorn)
#
# To run the original Streamlit monolith instead, swap the CMD line:
#   CMD ["sh", "-c", "streamlit run app/main.py --server.port=${PORT:-8501} --server.address=0.0.0.0"]

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if required by some python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

# Copy the rest of the app source code
COPY . .

EXPOSE 8000

# Railway sets $PORT automatically — use it, fallback to 8000
CMD ["sh", "-c", "uvicorn api.server:app --host 0.0.0.0 --port ${PORT:-8000}"]
