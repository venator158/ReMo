from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, EmailStr
import time

from database import get_db, engine
from models import Base, User, Node, Metric, Threshold, Alert
from auth import (
    authenticate_user, 
    create_access_token, 
    get_current_user, 
    get_password_hash,
    verify_password,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from export_endpoints import router as export_router

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ReMo API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include export endpoints
app.include_router(export_router)

# Pydantic models
class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class NodeResponse(BaseModel):
    id: int
    node_id: str
    node_name: str
    status: str
    last_seen: Optional[datetime]
    requires_password: bool = True
    
    class Config:
        from_attributes = True

class NodeAuthRequest(BaseModel):
    node_id: str
    password: str

class NodeAuthResponse(BaseModel):
    node_id: str
    node_name: str
    access_granted: bool
    message: str

class MetricResponse(BaseModel):
    id: int
    node_id: str
    metric_type: str
    metric_value: float
    timestamp: datetime
    
    class Config:
        from_attributes = True

class ThresholdCreate(BaseModel):
    node_id: str
    metric_type: str
    threshold_value: float
    condition: str  # 'greater' or 'less'

class ThresholdResponse(BaseModel):
    id: int
    node_id: str
    metric_type: str
    threshold_value: float
    condition: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AlertResponse(BaseModel):
    id: int
    node_id: str
    metric_type: str
    metric_value: float
    threshold_value: float
    message: str
    severity: str
    acknowledged: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Authentication endpoints
@app.post("/api/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if username exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@app.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login and receive access token"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

# Node endpoints
@app.get("/api/nodes", response_model=List[NodeResponse])
async def get_nodes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all nodes (without sensitive data)"""
    nodes = db.query(Node).all()
    # Return nodes without password hash
    return [
        NodeResponse(
            id=node.id,
            node_id=node.node_id,
            node_name=node.node_name,
            status=node.status,
            last_seen=node.last_seen,
            requires_password=True
        ) for node in nodes
    ]

@app.get("/api/nodes/{node_id}", response_model=NodeResponse)
async def get_node(
    node_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific node (without sensitive data)"""
    node = db.query(Node).filter(Node.node_id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return NodeResponse(
        id=node.id,
        node_id=node.node_id,
        node_name=node.node_name,
        status=node.status,
        last_seen=node.last_seen,
        requires_password=True
    )

@app.post("/api/nodes/authenticate", response_model=NodeAuthResponse)
async def authenticate_node(
    auth_request: NodeAuthRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Authenticate access to a specific node"""
    node = db.query(Node).filter(Node.node_id == auth_request.node_id).first()
    
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    # Verify node password
    if not verify_password(auth_request.password, node.node_password_hash):
        return NodeAuthResponse(
            node_id=node.node_id,
            node_name=node.node_name,
            access_granted=False,
            message="Invalid node password"
        )
    
    # Password is correct
    return NodeAuthResponse(
        node_id=node.node_id,
        node_name=node.node_name,
        access_granted=True,
        message="Access granted"
    )

# Metrics endpoints
@app.get("/api/metrics/latest")
async def get_latest_metrics(
    node_id: Optional[str] = None,
    node_password: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the latest metrics for each node and metric type
    Requires node_password parameter if requesting specific node data"""
    
    # If specific node requested, verify password
    if node_id and node_password:
        node = db.query(Node).filter(Node.node_id == node_id).first()
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
        if not verify_password(node_password, node.node_password_hash):
            raise HTTPException(status_code=403, detail="Invalid node password")
    elif node_id and not node_password:
        raise HTTPException(status_code=400, detail="Node password required for node-specific data")
    # Subquery to get the latest timestamp for each node and metric type
    subquery = db.query(
        Metric.node_id,
        Metric.metric_type,
        func.max(Metric.timestamp).label('max_timestamp')
    )
    
    if node_id:
        subquery = subquery.filter(Metric.node_id == node_id)
    
    subquery = subquery.group_by(Metric.node_id, Metric.metric_type).subquery()
    
    # Join to get the full metric records
    metrics = db.query(Metric).join(
        subquery,
        and_(
            Metric.node_id == subquery.c.node_id,
            Metric.metric_type == subquery.c.metric_type,
            Metric.timestamp == subquery.c.max_timestamp
        )
    ).all()
    
    # Format response
    result = {}
    for metric in metrics:
        if metric.node_id not in result:
            result[metric.node_id] = {}
        result[metric.node_id][metric.metric_type] = {
            'value': float(metric.metric_value),
            'timestamp': metric.timestamp.isoformat()
        }
    
    return result

@app.get("/api/metrics/history")
async def get_metrics_history(
    node_id: str,
    node_password: str,
    metric_type: Optional[str] = None,
    hours: int = 1,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get historical metrics for a node (requires node password)"""
    
    # Verify node password
    node = db.query(Node).filter(Node.node_id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    if not verify_password(node_password, node.node_password_hash):
        raise HTTPException(status_code=403, detail="Invalid node password")
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    query = db.query(Metric).filter(
        Metric.node_id == node_id,
        Metric.timestamp >= start_time,
        Metric.timestamp <= end_time
    )
    
    if metric_type:
        query = query.filter(Metric.metric_type == metric_type)
    
    metrics = query.order_by(Metric.timestamp.asc()).all()
    
    # Format response by metric type
    result = {}
    for metric in metrics:
        if metric.metric_type not in result:
            result[metric.metric_type] = []
        result[metric.metric_type].append({
            'value': float(metric.metric_value),
            'timestamp': metric.timestamp.isoformat()
        })
    
    return result

# Threshold endpoints
@app.get("/api/thresholds", response_model=List[ThresholdResponse])
async def get_thresholds(
    node_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all thresholds"""
    query = db.query(Threshold)
    if node_id:
        query = query.filter(Threshold.node_id == node_id)
    return query.all()

@app.post("/api/thresholds", response_model=ThresholdResponse)
async def create_threshold(
    threshold_data: ThresholdCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create or update a threshold"""
    # Validate condition
    if threshold_data.condition not in ['greater', 'less']:
        raise HTTPException(status_code=400, detail="Condition must be 'greater' or 'less'")
    
    # Check if node exists
    node = db.query(Node).filter(Node.node_id == threshold_data.node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    # Check if threshold already exists
    existing = db.query(Threshold).filter(
        Threshold.node_id == threshold_data.node_id,
        Threshold.metric_type == threshold_data.metric_type
    ).first()
    
    if existing:
        # Update existing threshold
        existing.threshold_value = threshold_data.threshold_value
        existing.condition = threshold_data.condition
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new threshold
        new_threshold = Threshold(
            node_id=threshold_data.node_id,
            metric_type=threshold_data.metric_type,
            threshold_value=threshold_data.threshold_value,
            condition=threshold_data.condition,
            created_by=current_user.id
        )
        db.add(new_threshold)
        db.commit()
        db.refresh(new_threshold)
        return new_threshold

@app.delete("/api/thresholds/{threshold_id}")
async def delete_threshold(
    threshold_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a threshold"""
    threshold = db.query(Threshold).filter(Threshold.id == threshold_id).first()
    if not threshold:
        raise HTTPException(status_code=404, detail="Threshold not found")
    
    db.delete(threshold)
    db.commit()
    return {"message": "Threshold deleted successfully"}

# Alert endpoints
@app.get("/api/alerts", response_model=List[AlertResponse])
async def get_alerts(
    node_id: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get alerts"""
    query = db.query(Alert)
    
    if node_id:
        query = query.filter(Alert.node_id == node_id)
    if acknowledged is not None:
        query = query.filter(Alert.acknowledged == acknowledged)
    
    alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
    return alerts

@app.post("/api/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Acknowledge an alert"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.acknowledged = True
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Alert acknowledged successfully"}

@app.get("/api/dashboard/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics"""
    total_nodes = db.query(Node).count()
    active_nodes = db.query(Node).filter(Node.status == 'active').count()
    
    # Count unacknowledged alerts
    unack_alerts = db.query(Alert).filter(Alert.acknowledged == False).count()
    
    # Count metrics in last hour
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_metrics = db.query(Metric).filter(Metric.timestamp >= one_hour_ago).count()
    
    return {
        'total_nodes': total_nodes,
        'active_nodes': active_nodes,
        'unacknowledged_alerts': unack_alerts,
        'metrics_last_hour': recent_metrics
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
