FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose ports for API and Prometheus metrics
EXPOSE 8000 8001

# Start script to run both consumer and API
CMD ["sh", "-c", "python kafka_consumer.py & python prometheus_exporter.py & uvicorn main:app --host 0.0.0.0 --port 8000"]
