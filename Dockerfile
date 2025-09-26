FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import socket; s=socket.socket(); s.connect(('127.0.0.1',8501))" || exit 1
CMD ["streamlit","run","app.py","--server.headless=true","--server.port=8501","--server.enableCORS=false"]