import os
import time
from prometheus_client import start_http_server, Info

# Prometheus configuration
PROMETHEUS_PORT = int(os.getenv('PROMETHEUS_PORT', 8001))

def main():
    """Start Prometheus metrics HTTP server"""
    print(f"[Prometheus Exporter] Starting metrics server on port {PROMETHEUS_PORT}")
    
    # Add application info
    info = Info('remo_backend', 'ReMo Backend Application')
    info.info({
        'version': '1.0.0',
        'description': 'Real-time monitoring system with Kafka and Prometheus'
    })
    
    # Start HTTP server for Prometheus to scrape
    start_http_server(PROMETHEUS_PORT)
    print(f"[Prometheus Exporter] Metrics available at http://localhost:{PROMETHEUS_PORT}/metrics")
    
    # Keep the server running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[Prometheus Exporter] Shutting down...")

if __name__ == "__main__":
    # Wait a bit for the application to initialize
    time.sleep(5)
    main()
