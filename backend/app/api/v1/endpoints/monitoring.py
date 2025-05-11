from fastapi import APIRouter, Request, Response, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.core.monitoring import (
    health_check,
    performance_monitor,
    usage_tracker,
    error_tracker,
    system_monitor
)
from app.core.config_manager import config_manager
from app.core.security import validate_api_key
from prometheus_client import generate_latest

router = APIRouter()

@router.get("/health")
async def health_check_endpoint():
    """Health check endpoint"""
    results = await health_check.run_checks()
    is_healthy = all(check["status"] == "healthy" for check in results.values())
    
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": results
    }

@router.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    return Response(
        generate_latest(),
        media_type="text/plain"
    )

@router.get("/status")
async def status_endpoint():
    """System status endpoint"""
    status = await system_monitor.check_system_status()
    return status

@router.get("/usage")
async def usage_endpoint(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
):
    """Usage statistics endpoint"""
    stats = usage_tracker.get_stats()
    
    if start_time or end_time:
        # Filter stats by time range
        filtered_stats = {}
        for endpoint, data in stats.items():
            if "timestamp" in data:
                timestamp = datetime.fromisoformat(data["timestamp"])
                if start_time and timestamp < start_time:
                    continue
                if end_time and timestamp > end_time:
                    continue
                filtered_stats[endpoint] = data
        stats = filtered_stats
    
    return stats

@router.get("/errors")
async def errors_endpoint(
    error_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100
):
    """Error tracking endpoint"""
    errors = error_tracker.get_errors(
        error_type=error_type,
        start_time=start_time,
        end_time=end_time
    )
    return errors[-limit:]  # Return last N errors

@router.get("/performance")
async def performance_endpoint():
    """Performance metrics endpoint"""
    await performance_monitor.collect_metrics()
    return performance_monitor.get_metrics()

@router.get("/services")
async def services_endpoint():
    """Service status endpoint"""
    settings = config_manager.get_settings()
    services = {}
    
    for name, url in settings.services.get_all_services().items():
        service = health_check.get_status().get(name, {})
        services[name] = {
            "url": url,
            "status": service.get("status", "unknown"),
            "last_check": service.get("timestamp")
        }
    
    return services

@router.get("/alerts")
async def alerts_endpoint():
    """System alerts endpoint"""
    alerts = []
    
    # Check system resources
    status = await system_monitor.check_system_status()
    resources = status["resources"]
    
    # Memory alerts
    if resources["memory"]["percent"] > 90:
        alerts.append({
            "type": "memory",
            "level": "critical",
            "message": f"High memory usage: {resources['memory']['percent']}%",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    # CPU alerts
    if resources["cpu"]["percent"] > 90:
        alerts.append({
            "type": "cpu",
            "level": "critical",
            "message": f"High CPU usage: {resources['cpu']['percent']}%",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    # Disk alerts
    if resources["disk"]["percent"] > 90:
        alerts.append({
            "type": "disk",
            "level": "critical",
            "message": f"High disk usage: {resources['disk']['percent']}%",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    # Service alerts
    for service_name, service_status in status["services"].items():
        if service_status["status"] == "unhealthy":
            alerts.append({
                "type": "service",
                "level": "critical",
                "message": f"Service {service_name} is unhealthy",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    return alerts

@router.get("/summary")
async def summary_endpoint():
    """System summary endpoint"""
    # Get all monitoring data
    health_status = await health_check.run_checks()
    system_status = await system_monitor.check_system_status()
    usage_stats = usage_tracker.get_stats()
    performance_metrics = performance_monitor.get_metrics()
    
    # Calculate summary
    summary = {
        "timestamp": datetime.utcnow().isoformat(),
        "health": {
            "overall": "healthy" if all(check["status"] == "healthy" for check in health_status.values()) else "unhealthy",
            "checks": health_status
        },
        "system": {
            "resources": system_status["resources"],
            "services": system_status["services"]
        },
        "usage": {
            "total_requests": sum(data["requests"] for data in usage_stats.values() if "requests" in data),
            "total_errors": sum(data["errors"] for data in usage_stats.values() if "errors" in data),
            "endpoints": len(usage_stats)
        },
        "performance": performance_metrics
    }
    
    return summary 