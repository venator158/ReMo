-- Create Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Nodes table (metric producers)
CREATE TABLE IF NOT EXISTS nodes (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) UNIQUE NOT NULL,
    node_name VARCHAR(100) NOT NULL,
    node_password_hash VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Metrics table
CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    metric_value DECIMAL(10, 2) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (node_id) REFERENCES nodes(node_id) ON DELETE CASCADE
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_metrics_node_id ON metrics(node_id);
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_metrics_node_time ON metrics(node_id, timestamp);

-- Create Thresholds table
CREATE TABLE IF NOT EXISTS thresholds (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    threshold_value DECIMAL(10, 2) NOT NULL,
    condition VARCHAR(10) NOT NULL, -- 'greater' or 'less'
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (node_id) REFERENCES nodes(node_id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE(node_id, metric_type)
);

-- Create Alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    metric_value DECIMAL(10, 2) NOT NULL,
    threshold_value DECIMAL(10, 2) NOT NULL,
    message TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'warning',
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by INTEGER,
    acknowledged_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (node_id) REFERENCES nodes(node_id) ON DELETE CASCADE,
    FOREIGN KEY (acknowledged_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_alerts_node_id ON alerts(node_id);
CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged ON alerts(acknowledged);

-- Insert default admin user (password: admin123)
-- Password hash generated using bcrypt
INSERT INTO users (username, email, hashed_password)
VALUES ('admin', 'admin@remo.local', '$2b$12$PeU/.kcOHZjQx5NKag/VUeO9BjcTg8shBWmDBkgaJ7JIH7SykmaRC')
ON CONFLICT (username) DO NOTHING;

-- Insert initial nodes (all nodes have password: node123)
-- Password hash generated using bcrypt
INSERT INTO nodes (node_id, node_name, node_password_hash, status)
VALUES 
    ('node-1', 'Server-Alpha', '$2b$12$ciFuPtqFkOcSNhIFb095x.u9SeGNnL43vvlIselWuatbl1LWzXADO', 'active'),
    ('node-2', 'Server-Beta', '$2b$12$ciFuPtqFkOcSNhIFb095x.u9SeGNnL43vvlIselWuatbl1LWzXADO', 'active'),
    ('node-3', 'Server-Gamma', '$2b$12$ciFuPtqFkOcSNhIFb095x.u9SeGNnL43vvlIselWuatbl1LWzXADO', 'active'),
    ('node-4', 'Server-Delta', '$2b$12$ciFuPtqFkOcSNhIFb095x.u9SeGNnL43vvlIselWuatbl1LWzXADO', 'active')
ON CONFLICT (node_id) DO NOTHING;
