# ReMo - Real-time Monitoring System

A comprehensive real-time monitoring system built with Kafka, FastAPI, Svelte, and Prometheus. This project demonstrates a scalable architecture for collecting, processing, and visualizing metrics from multiple nodes with alerting capabilities.

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Metric Nodes   │────▶│  Kafka Broker   │────▶│   Backend API   │
│  (Producers)    │     │   (Zookeeper)   │     │   (Consumer)    │
│  - Node 1       │     └─────────────────┘     │  - FastAPI      │
│  - Node 2       │                              │  - PostgreSQL   │
│  - Node 3       │                              │  - Prometheus   │
│  - Node 4       │                              └────────┬────────┘
└─────────────────┘                                       │
                                                          │
                                                          ▼
                                                ┌─────────────────┐
                                                │  Svelte Web UI  │
                                                │  - Dashboard    │
                                                │  - Alerts       │
                                                │  - Thresholds   │
                                                └─────────────────┘
```

## ✨ Features

- **4 Dockerized Metric Nodes**: Generate and publish CPU, Memory, Disk I/O, and Network metrics
- **Kafka Message Broker**: Reliable message streaming with topic-based architecture
- **Real-time Dashboard**: Svelte-based UI with live metric visualization
- **Threshold Management**: Configure custom thresholds for each metric type per node
- **Alert System**: Automatic alert generation with severity levels and acknowledgment
- **Prometheus Integration**: Metrics exported for long-term storage and analysis
- **CSV Export**: Download historical data for offline analysis
- **JWT Authentication**: Secure login system with role-based access
- **PostgreSQL Storage**: Persistent storage for metrics, alerts, and configurations

## 📁 Project Structure

```
remo-project/
│
├── docker-compose.yml                    # Main orchestration file
├── README.md                             # This file
│
└── src/
    │
    ├── metric-nodes/                     # Metric Producers
    │   ├── Dockerfile
    │   ├── metric_producer.py            # Python Kafka producer
    │   └── requirements.txt
    │
    ├── prometheus/
    │   └── prometheus.yml                # Prometheus configuration
    │
    ├── backend/                          # FastAPI Backend
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   ├── init-db.sql                   # Database schema
    │   ├── main.py                       # FastAPI app
    │   ├── kafka_consumer.py             # Kafka consumer
    │   ├── prometheus_exporter.py        # Metrics exporter
    │   ├── export_endpoints.py           # CSV export APIs
    │   ├── models.py                     # SQLAlchemy models
    │   ├── auth.py                       # JWT authentication
    │   └── database.py                   # Database connection
    │
    └── frontend/                         # Svelte Frontend
        ├── Dockerfile
        ├── package.json
        ├── vite.config.js
        ├── index.html
        │
        └── src/
            ├── main.js
            ├── App.svelte
            ├── app.css
            │
            ├── lib/
            │   ├── components/
            │   │   ├── Login.svelte
            │   │   ├── Dashboard.svelte
            │   │   ├── MetricChart.svelte
            │   │   ├── ThresholdConfig.svelte
            │   │   └── AlertPanel.svelte
            │   │
            │   └── api/
            │       └── client.js
            │
            └── stores/
                └── auth.js
```

## 🚀 Quick Start

### Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Docker Compose
- At least 4GB RAM available for Docker
- Ports 5173, 8000, 8001, 9090, 9092, 5432 available

### Installation & Running

1. **Clone the repository**:
   ```powershell
   git clone <repository-url>
   cd ReMo
   ```

2. **Start all services**:
   ```powershell
   docker-compose up --build
   ```

   This will start:
   - 4 Metric nodes (producers)
   - Kafka broker + Zookeeper
   - PostgreSQL database
   - Prometheus
   - Backend API
   - Frontend web app

3. **Access the application**:
   - **Web Dashboard**: http://localhost:5173
   - **Backend API**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs
   - **Prometheus**: http://localhost:9090

4. **Default Login Credentials**:
   - Username: `admin`
   - Password: `admin123`

### Stopping the Application

```powershell
docker-compose down
```

To remove all data volumes:
```powershell
docker-compose down -v
```

## 📊 Usage Guide

### Dashboard Overview

1. **Stats Cards**: View total nodes, active nodes, active alerts, and recent metrics count
2. **Nodes List**: All metric-generating nodes with their current status
3. **Current Metrics**: Real-time view of selected node's latest metrics

### Viewing Metrics

1. Select the **Metrics** tab
2. Choose a node from the left panel
3. View real-time charts for:
   - CPU Usage (%)
   - Memory Usage (%)
   - Disk I/O (MB/s)
   - Network Traffic (Mbps)
4. Click **Export CSV** to download historical data

### Configuring Thresholds

1. Select the **Thresholds** tab
2. Choose a node
3. Set threshold values:
   - Select metric type (CPU, Memory, Disk I/O, Network)
   - Enter threshold value
   - Choose condition (Greater Than / Less Than)
4. Click **Save Threshold**
5. View and manage active thresholds in the table

### Managing Alerts

1. Select the **Alerts** tab
2. Filter by:
   - Unacknowledged
   - All
   - Acknowledged
3. Review alert details (severity, metric, threshold)
4. Click **Acknowledge** to mark alerts as resolved

### Exporting Data

- **CSV Export**: Click "Export CSV" in the Metrics tab
- **Prometheus Queries**: Access Prometheus at http://localhost:9090
- **API Endpoints**: Use `/api/export/` endpoints for programmatic access

## 🔧 Configuration

### Environment Variables

Edit `docker-compose.yml` to customize:

**Backend**:
- `DATABASE_URL`: PostgreSQL connection string
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka broker address
- `JWT_SECRET_KEY`: Secret key for JWT tokens (⚠️ Change in production!)
- `PROMETHEUS_PORT`: Port for Prometheus metrics

**Metric Nodes**:
- `NODE_ID`: Unique identifier for the node
- `NODE_NAME`: Human-readable name
- `KAFKA_TOPIC`: Kafka topic to publish to
- `METRIC_INTERVAL`: Seconds between metric publications (default: 5)

**Frontend**:
- `VITE_API_URL`: Backend API URL

### Adding More Metric Nodes

Add a new service in `docker-compose.yml`:

```yaml
metric-node-5:
  build:
    context: ./src/metric-nodes
    dockerfile: Dockerfile
  container_name: metric-node-5
  environment:
    NODE_ID: "node-5"
    NODE_NAME: "Server-Epsilon"
    KAFKA_BOOTSTRAP_SERVERS: kafka:9092
    KAFKA_TOPIC: "metrics-node-5"
    METRIC_INTERVAL: 5
  depends_on:
    kafka:
      condition: service_healthy
  networks:
    - remo-network
  restart: unless-stopped
```

And add the node to the database init script (`src/backend/init-db.sql`):

```sql
INSERT INTO nodes (node_id, node_name, status)
VALUES ('node-5', 'Server-Epsilon', 'active')
ON CONFLICT (node_id) DO NOTHING;
```

## 🔍 API Documentation

Once the backend is running, visit http://localhost:8000/docs for interactive API documentation.

### Key Endpoints

**Authentication**:
- `POST /api/auth/login` - Login and receive JWT token
- `POST /api/auth/register` - Register new user
- `GET /api/auth/me` - Get current user info

**Nodes**:
- `GET /api/nodes` - List all nodes
- `GET /api/nodes/{node_id}` - Get node details

**Metrics**:
- `GET /api/metrics/latest` - Get latest metrics for all nodes
- `GET /api/metrics/history` - Get historical metrics

**Thresholds**:
- `GET /api/thresholds` - List thresholds
- `POST /api/thresholds` - Create/update threshold
- `DELETE /api/thresholds/{id}` - Delete threshold

**Alerts**:
- `GET /api/alerts` - List alerts
- `POST /api/alerts/{id}/acknowledge` - Acknowledge alert

**Export**:
- `GET /api/export/csv` - Export metrics as CSV
- `GET /api/export/summary` - Get metrics summary

## 🛠️ Development

### Running Components Individually

**Backend**:
```powershell
cd src/backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend**:
```powershell
cd src/frontend
npm install
npm run dev
```

**Metric Producer**:
```powershell
cd src/metric-nodes
pip install -r requirements.txt
python metric_producer.py
```

## 🐛 Troubleshooting

### Services not starting

1. Check if ports are available:
   ```powershell
   netstat -ano | findstr "5173 8000 9092 5432"
   ```

2. View service logs:
   ```powershell
   docker-compose logs backend
   docker-compose logs kafka
   docker-compose logs metric-node-1
   ```

### Kafka connection issues

- Wait 30-60 seconds after startup for Kafka to be fully ready
- Check Kafka health: `docker-compose logs kafka`
- Verify Zookeeper is running: `docker-compose logs zookeeper`

### Database connection errors

- Ensure PostgreSQL is healthy: `docker-compose ps`
- Check database logs: `docker-compose logs postgres`
- Verify credentials in `docker-compose.yml`

### Frontend not loading

- Clear browser cache
- Check backend is accessible: http://localhost:8000/health
- View frontend logs: `docker-compose logs frontend`

## 📈 Performance Considerations

- **Metric Interval**: Default is 5 seconds. Increase for lower load.
- **Data Retention**: Metrics accumulate in PostgreSQL. Implement cleanup jobs for production.
- **Prometheus Storage**: Configure retention in `prometheus.yml` for production use.
- **Kafka Partitions**: Increase partitions for higher throughput with more consumers.

## 🔐 Security Notes

⚠️ **Important for Production**:

1. Change `JWT_SECRET_KEY` in docker-compose.yml
2. Use environment variables or secrets management (not hardcoded values)
3. Change default admin password immediately
4. Enable HTTPS/TLS for all services
5. Configure proper CORS origins in backend
6. Use strong PostgreSQL passwords
7. Enable Kafka authentication and encryption
8. Implement rate limiting on APIs
9. Regular security updates for all dependencies

## 📝 License

This project is provided as-is for educational and demonstration purposes.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

## 📧 Support

For questions or issues, please open an issue in the repository.

---

Built with ❤️ using Kafka, FastAPI, Svelte, PostgreSQL, and Prometheus
