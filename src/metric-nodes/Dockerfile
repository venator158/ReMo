FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY metric_producer.py .

# Use unbuffered output so logs appear immediately
CMD ["python", "-u", "metric_producer.py"]
