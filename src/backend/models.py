from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Numeric, func
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    thresholds = relationship("Threshold", back_populates="creator")
    acknowledged_alerts = relationship("Alert", back_populates="acknowledger")

class Node(Base):
    __tablename__ = "nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String(50), unique=True, nullable=False, index=True)
    node_name = Column(String(100), nullable=False)
    node_password_hash = Column(String(255), nullable=False)
    status = Column(String(20), default="active")
    last_seen = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    metrics = relationship("Metric", back_populates="node", cascade="all, delete-orphan")
    thresholds = relationship("Threshold", back_populates="node", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="node", cascade="all, delete-orphan")

class Metric(Base):
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String(50), ForeignKey("nodes.node_id"), nullable=False)
    metric_type = Column(String(50), nullable=False)
    metric_value = Column(Numeric(10, 2), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    node = relationship("Node", back_populates="metrics")

class Threshold(Base):
    __tablename__ = "thresholds"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String(50), ForeignKey("nodes.node_id"), nullable=False)
    metric_type = Column(String(50), nullable=False)
    threshold_value = Column(Numeric(10, 2), nullable=False)
    condition = Column(String(10), nullable=False)  # 'greater' or 'less'
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    node = relationship("Node", back_populates="thresholds")
    creator = relationship("User", back_populates="thresholds")

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String(50), ForeignKey("nodes.node_id"), nullable=False)
    metric_type = Column(String(50), nullable=False)
    metric_value = Column(Numeric(10, 2), nullable=False)
    threshold_value = Column(Numeric(10, 2), nullable=False)
    message = Column(String, nullable=False)
    severity = Column(String(20), default="warning")
    acknowledged = Column(Boolean, default=False, index=True)
    acknowledged_by = Column(Integer, ForeignKey("users.id"))
    acknowledged_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    node = relationship("Node", back_populates="alerts")
    acknowledger = relationship("User", back_populates="acknowledged_alerts")
