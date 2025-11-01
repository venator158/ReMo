import os
import json
import time
from datetime import datetime
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Node, Metric, Threshold, Alert
from prometheus_client import Counter, Gauge
from decimal import Decimal

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_TOPICS = ['metrics-node-1', 'metrics-node-2', 'metrics-node-3', 'metrics-node-4']
KAFKA_GROUP_ID = 'remo-consumer-group'

# Prometheus metrics
metrics_received_counter = Counter('remo_metrics_received_total', 'Total metrics received', ['node_id', 'metric_type'])
alerts_generated_counter = Counter('remo_alerts_generated_total', 'Total alerts generated', ['node_id', 'metric_type'])

# Gauges for current metric values
cpu_gauge = Gauge('remo_cpu_usage', 'Current CPU usage', ['node_id', 'node_name'])
memory_gauge = Gauge('remo_memory_usage', 'Current Memory usage', ['node_id', 'node_name'])
disk_io_gauge = Gauge('remo_disk_io', 'Current Disk I/O', ['node_id', 'node_name'])
network_gauge = Gauge('remo_network_traffic', 'Current Network traffic', ['node_id', 'node_name'])

def create_consumer():
    """Create and return a Kafka consumer with retry logic"""
    max_retries = 10
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            consumer = KafkaConsumer(
                *KAFKA_TOPICS,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id=KAFKA_GROUP_ID,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
                auto_commit_interval_ms=1000
            )
            print(f"[Consumer] Successfully connected to Kafka broker")
            print(f"[Consumer] Subscribed to topics: {KAFKA_TOPICS}")
            return consumer
        except KafkaError as e:
            retry_count += 1
            print(f"[Consumer] Failed to connect to Kafka (attempt {retry_count}/{max_retries}): {e}")
            time.sleep(5)
    
    raise Exception(f"[Consumer] Could not connect to Kafka after {max_retries} attempts")

def check_thresholds(db: Session, node_id: str, metric_type: str, metric_value: float) -> None:
    """Check if metric value exceeds thresholds and create alerts"""
    thresholds = db.query(Threshold).filter(
        Threshold.node_id == node_id,
        Threshold.metric_type == metric_type
    ).all()
    
    for threshold in thresholds:
        threshold_exceeded = False
        
        if threshold.condition == 'greater' and metric_value > float(threshold.threshold_value):
            threshold_exceeded = True
        elif threshold.condition == 'less' and metric_value < float(threshold.threshold_value):
            threshold_exceeded = True
        
        if threshold_exceeded:
            # Check if there's already an unacknowledged alert for this
            existing_alert = db.query(Alert).filter(
                Alert.node_id == node_id,
                Alert.metric_type == metric_type,
                Alert.acknowledged == False
            ).order_by(Alert.created_at.desc()).first()
            
            # Only create a new alert if the last one was more than 5 minutes ago
            if not existing_alert or (datetime.utcnow() - existing_alert.created_at).seconds > 300:
                severity = 'critical' if metric_value > float(threshold.threshold_value) * 1.2 else 'warning'
                
                alert = Alert(
                    node_id=node_id,
                    metric_type=metric_type,
                    metric_value=Decimal(str(metric_value)),
                    threshold_value=threshold.threshold_value,
                    message=f"{metric_type} on {node_id} is {metric_value} (threshold: {threshold.threshold_value})",
                    severity=severity
                )
                db.add(alert)
                db.commit()
                
                alerts_generated_counter.labels(node_id=node_id, metric_type=metric_type).inc()
                print(f"[Consumer] Alert created: {alert.message}")

def process_message(db: Session, message: dict) -> None:
    """Process a single Kafka message"""
    try:
        node_id = message.get('node_id')
        node_name = message.get('node_name')
        timestamp_str = message.get('timestamp')
        metrics = message.get('metrics', {})
        
        # Parse timestamp
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        
        # Update node last_seen
        node = db.query(Node).filter(Node.node_id == node_id).first()
        if node:
            node.last_seen = datetime.utcnow()
            db.commit()
        
        # Process each metric
        for metric_type, metric_value in metrics.items():
            # Store in database
            metric = Metric(
                node_id=node_id,
                metric_type=metric_type,
                metric_value=Decimal(str(metric_value)),
                timestamp=timestamp
            )
            db.add(metric)
            
            # Update Prometheus metrics
            metrics_received_counter.labels(node_id=node_id, metric_type=metric_type).inc()
            
            # Update gauges
            if metric_type == 'cpu_usage':
                cpu_gauge.labels(node_id=node_id, node_name=node_name).set(metric_value)
            elif metric_type == 'memory_usage':
                memory_gauge.labels(node_id=node_id, node_name=node_name).set(metric_value)
            elif metric_type == 'disk_io':
                disk_io_gauge.labels(node_id=node_id, node_name=node_name).set(metric_value)
            elif metric_type == 'network_traffic':
                network_gauge.labels(node_id=node_id, node_name=node_name).set(metric_value)
            
            # Check thresholds
            check_thresholds(db, node_id, metric_type, float(metric_value))
        
        db.commit()
        print(f"[Consumer] Processed metrics from {node_name} ({node_id})")
        
    except Exception as e:
        print(f"[Consumer] Error processing message: {e}")
        db.rollback()

def main():
    """Main consumer loop"""
    print("[Consumer] Starting Kafka consumer...")
    
    consumer = create_consumer()
    db = SessionLocal()
    
    try:
        print("[Consumer] Waiting for messages...")
        for message in consumer:
            try:
                payload = message.value
                process_message(db, payload)
            except Exception as e:
                print(f"[Consumer] Error processing message: {e}")
                continue
                
    except KeyboardInterrupt:
        print("[Consumer] Shutting down...")
    finally:
        consumer.close()
        db.close()
        print("[Consumer] Consumer closed")

if __name__ == "__main__":
    # Wait for dependencies to be ready
    time.sleep(10)
    main()
