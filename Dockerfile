# ----- Base image -----
FROM python:3.11-slim

WORKDIR /app

# Faster/safer Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ----- System deps (for HTTPS requests, wheels, etc.) -----
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# ----- Python deps -----
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# ----- App code -----
COPY . .

# ----- App env (UI calls API inside same container) -----
ENV API_URL=http://localhost:8001 \
    API_KEY=dev-secret \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501

# ----- Ports -----
EXPOSE 8001 8501

# ----- Healthcheck (Python script you already have) -----
COPY healthcheck.py .
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD ["python", "healthcheck.py"]

# ----- Start API & full UI (app.py) -----
CMD sh -c "uvicorn api:app --host 0.0.0.0 --port 8001 & \
           exec streamlit run app.py \
             --server.address=${STREAMLIT_SERVER_ADDRESS} \
             --server.port=${STREAMLIT_SERVER_PORT} \
             --server.headless=true \
             --server.enableCORS=false"