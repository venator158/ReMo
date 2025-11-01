import os
import json
import time
import random
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError

# Configuration from environment variables
NODE_ID = os.getenv('NODE_ID', 'node-1')
NODE_NAME = os.getenv('NODE_NAME', 'Server-1')
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', f'metrics-{NODE_ID}')
METRIC_INTERVAL = int(os.getenv('METRIC_INTERVAL', 5))  # seconds

def create_producer():
    """Create and return a Kafka producer with retry logic"""
    max_retries = 10
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3,
                max_in_flight_requests_per_connection=1
            )
            print(f"[{NODE_NAME}] Successfully connected to Kafka broker")
            return producer
        except KafkaError as e:
            retry_count += 1
            print(f"[{NODE_NAME}] Failed to connect to Kafka (attempt {retry_count}/{max_retries}): {e}")
            time.sleep(5)
    
    raise Exception(f"[{NODE_NAME}] Could not connect to Kafka after {max_retries} attempts")

def generate_cpu_metric():
    """Generate mock CPU usage metric (0-100%)"""
    # Simulate realistic CPU usage with some variation
    base_usage = random.uniform(20, 80)
    spike = random.choice([0, 0, 0, random.uniform(10, 20)])  # Occasional spikes
    return round(min(100, base_usage + spike), 2)

def generate_memory_metric():
    """Generate mock Memory usage metric (0-100%)"""
    # Simulate realistic memory usage
    base_usage = random.uniform(30, 75)
    spike = random.choice([0, 0, 0, random.uniform(5, 15)])  # Occasional spikes
    return round(min(100, base_usage + spike), 2)

def generate_disk_io_metric():
    """Generate mock Disk I/O metric (MB/s)"""
    return round(random.uniform(10, 500), 2)

def generate_network_traffic_metric():
    """Generate mock Network traffic metric (Mbps)"""
    return round(random.uniform(5, 1000), 2)

def generate_metrics_payload():
    """Generate a complete metrics payload"""
    timestamp = datetime.utcnow().isoformat() + 'Z'
    
    payload = {
        'node_id': NODE_ID,
        'node_name': NODE_NAME,
        'timestamp': timestamp,
        'metrics': {
            'cpu_usage': generate_cpu_metric(),
            'memory_usage': generate_memory_metric(),
            'disk_io': generate_disk_io_metric(),
            'network_traffic': generate_network_traffic_metric()
        }
    }
    
    return payload

def main():
    """Main producer loop"""
    print(f"[{NODE_NAME}] Starting metric producer")
    print(f"[{NODE_NAME}] Node ID: {NODE_ID}")
    print(f"[{NODE_NAME}] Topic: {KAFKA_TOPIC}")
    print(f"[{NODE_NAME}] Interval: {METRIC_INTERVAL}s")
    print(f"[{NODE_NAME}] Kafka Broker: {KAFKA_BOOTSTRAP_SERVERS}")
    
    producer = create_producer()
    
    try:
        while True:
            # Generate metrics
            payload = generate_metrics_payload()
            
            # Send to Kafka
            try:
                future = producer.send(KAFKA_TOPIC, value=payload)
                record_metadata = future.get(timeout=10)
                
                print(f"[{NODE_NAME}] Sent metrics to {record_metadata.topic} "
                      f"partition {record_metadata.partition} offset {record_metadata.offset} | "
                      f"CPU: {payload['metrics']['cpu_usage']}%, "
                      f"MEM: {payload['metrics']['memory_usage']}%")
                
            except KafkaError as e:
                print(f"[{NODE_NAME}] Failed to send message: {e}")
            
            # Wait for next interval
            time.sleep(METRIC_INTERVAL)
            
    except KeyboardInterrupt:
        print(f"[{NODE_NAME}] Shutting down...")
    finally:
        producer.close()
        print(f"[{NODE_NAME}] Producer closed")

if __name__ == "__main__":
    main()
