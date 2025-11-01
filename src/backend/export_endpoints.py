import os
import csv
import io
from datetime import datetime, timedelta
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
import requests
from database import get_db
from models import Metric, Node
from auth import get_current_user, User

router = APIRouter()

@router.get("/api/export/csv")
async def export_metrics_csv(
    node_id: str = None,
    metric_type: str = None,
    hours: int = 24,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export metrics data as CSV"""
    
    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    # Build query
    query = db.query(Metric).filter(
        Metric.timestamp >= start_time,
        Metric.timestamp <= end_time
    )
    
    if node_id:
        query = query.filter(Metric.node_id == node_id)
    if metric_type:
        query = query.filter(Metric.metric_type == metric_type)
    
    metrics = query.order_by(Metric.timestamp.asc()).all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Timestamp', 'Node ID', 'Metric Type', 'Value'])
    
    # Write data
    for metric in metrics:
        writer.writerow([
            metric.timestamp.isoformat(),
            metric.node_id,
            metric.metric_type,
            float(metric.metric_value)
        ])
    
    # Prepare response
    csv_content = output.getvalue()
    output.close()
    
    filename = f"metrics_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/api/export/prometheus/query")
async def query_prometheus(
    query: str,
    current_user: User = Depends(get_current_user)
):
    """Query Prometheus for historical data"""
    
    prometheus_url = os.getenv('PROMETHEUS_URL', 'http://prometheus:9090')
    
    try:
        response = requests.get(
            f"{prometheus_url}/api/v1/query",
            params={"query": query}
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Prometheus query failed: {str(e)}")

@router.get("/api/export/prometheus/query_range")
async def query_prometheus_range(
    query: str,
    start: str,
    end: str,
    step: str = "15s",
    current_user: User = Depends(get_current_user)
):
    """Query Prometheus for time-series data in a range"""
    
    prometheus_url = os.getenv('PROMETHEUS_URL', 'http://prometheus:9090')
    
    try:
        response = requests.get(
            f"{prometheus_url}/api/v1/query_range",
            params={
                "query": query,
                "start": start,
                "end": end,
                "step": step
            }
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Prometheus query failed: {str(e)}")

@router.get("/api/export/summary")
async def get_metrics_summary(
    node_id: str = None,
    hours: int = 24,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get summary statistics for metrics"""
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    query = db.query(
        Metric.node_id,
        Metric.metric_type,
        func.avg(Metric.metric_value).label('avg'),
        func.min(Metric.metric_value).label('min'),
        func.max(Metric.metric_value).label('max'),
        func.count(Metric.id).label('count')
    ).filter(
        Metric.timestamp >= start_time,
        Metric.timestamp <= end_time
    )
    
    if node_id:
        query = query.filter(Metric.node_id == node_id)
    
    results = query.group_by(Metric.node_id, Metric.metric_type).all()
    
    summary = []
    for result in results:
        summary.append({
            'node_id': result.node_id,
            'metric_type': result.metric_type,
            'average': float(result.avg),
            'minimum': float(result.min),
            'maximum': float(result.max),
            'count': result.count
        })
    
    return {"summary": summary, "time_range_hours": hours}
