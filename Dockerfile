# ----- Base image -----
FROM python:3.11-slim

WORKDIR /app

# ----- Install system dependencies -----
# Add CA certificates so Python requests/https works
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# ----- Python dependencies -----
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -r requirements.txt

# ----- Application code -----
COPY . .

# ----- Environment variables -----
# Used by Streamlit UI to call FastAPI inside same container
ENV API_URL=http://localhost:8001 \
    API_KEY=dev-secret \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501

# ----- Expose ports -----
EXPOSE 8501 8001

# copy script healthcheck
COPY healthcheck.py .

# Healthcheck:file Python
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD ["python", "healthcheck.py"]

# Start API & UI
# ----- Start both API & Auth UI -----
CMD sh -c "uvicorn api:app --host 0.0.0.0 --port 8001 & \
           exec streamlit run auth_ui.py \
             --server.address=0.0.0.0 \
             --server.port=8501 \
             --server.headless=true \
             --server.enableCORS=false"