from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
import time
from prometheus_client import Counter, Histogram, Gauge, Summary
from app.core.logging import logger
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import psutil
import aiohttp
import asyncio
from app.core.config_manager import config_manager
from app.core.cache import cache_manager

# Metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint']
)

ERROR_COUNT = Counter(
    "http_errors_total",
    "Total HTTP errors",
    ["method", "endpoint", "error_type"]
)

CACHE_HITS = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["cache_name"]
)

CACHE_MISSES = Counter(
    "cache_misses_total",
    "Total cache misses",
    ["cache_name"]
)

DB_QUERY_DURATION = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["query_type"]
)

DB_CONNECTION_POOL = Gauge(
    "db_connection_pool_size",
    "Database connection pool size",
    ["state"]
)

SYSTEM_MEMORY = Gauge(
    "system_memory_bytes",
    "System memory usage in bytes",
    ["type"]
)

SYSTEM_CPU = Gauge(
    "system_cpu_percent",
    "System CPU usage percentage",
    ["core"]
)

SYSTEM_DISK = Gauge(
    "system_disk_bytes",
    "System disk usage in bytes",
    ["type"]
)

DB_OPERATION_LATENCY = Histogram(
    'db_operation_duration_seconds',
    'Database operation latency',
    ['operation']
)

TRADING_OPERATION_LATENCY = Histogram(
    'trading_operation_duration_seconds',
    'Trading operation latency',
    ['operation']
)

class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for monitoring request performance"""
    
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint
    ) -> Response:
        # Get request path and method
        path = request.url.path
        method = request.method
        
        # Increment active requests
        ACTIVE_REQUESTS.labels(method=method, endpoint=path).inc()
        
        # Start timer
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            REQUEST_COUNT.labels(
                method=method,
                endpoint=path,
                status=response.status_code
            ).inc()
            REQUEST_LATENCY.labels(
                method=method,
                endpoint=path
            ).observe(duration)
            
            # Log request details
            logger.info(
                "Request completed",
                extra={
                    "request_id": getattr(request.state, "request_id", "unknown"),
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_ms": duration * 1000,
                    "client_ip": request.client.host if request.client else "unknown",
                    "user_id": getattr(request.state, "user_id", "unknown")
                }
            )
            
            return response
            
        except Exception as e:
            # Record error metrics
            REQUEST_COUNT.labels(
                method=method,
                endpoint=path,
                status=500
            ).inc()
            
            # Log error
            logger.error(
                "Request failed",
                extra={
                    "request_id": getattr(request.state, "request_id", "unknown"),
                    "method": method,
                    "path": path,
                    "error": str(e)
                },
                exc_info=True
            )
            
            raise
            
        finally:
            # Decrement active requests
            ACTIVE_REQUESTS.labels(method=method, endpoint=path).dec()

class DatabaseMonitoringMiddleware:
    """Middleware for monitoring database operations"""
    
    def __init__(self, db_session):
        self.db_session = db_session
    
    async def __call__(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Start timer
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            DB_OPERATION_LATENCY.labels(
                operation=request.url.path
            ).observe(duration)
            
            return response
            
        except Exception as e:
            # Log error
            logger.error(
                "Database operation failed",
                extra={
                    "request_id": getattr(request.state, "request_id", "unknown"),
                    "operation": request.url.path,
                    "error": str(e)
                },
                exc_info=True
            )
            raise

class TradingMonitoringMiddleware:
    """Middleware for monitoring trading operations"""
    
    def __init__(self, trading_service):
        self.trading_service = trading_service
    
    async def __call__(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Start timer
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            TRADING_OPERATION_LATENCY.labels(
                operation=request.url.path
            ).observe(duration)
            
            return response
            
        except Exception as e:
            # Log error
            logger.error(
                "Trading operation failed",
                extra={
                    "request_id": getattr(request.state, "request_id", "unknown"),
                    "operation": request.url.path,
                    "error": str(e)
                },
                exc_info=True
            )
            raise 

class HealthCheck:
    """Health check manager"""
    
    def __init__(self):
        self._checks: Dict[str, callable] = {}
        self._status: Dict[str, Any] = {}
    
    def register_check(self, name: str, check_func: callable):
        """Register a health check"""
        self._checks[name] = check_func
    
    async def run_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {}
        for name, check in self._checks.items():
            try:
                result = await check()
                results[name] = {
                    "status": "healthy" if result else "unhealthy",
                    "timestamp": datetime.utcnow().isoformat()
                }
            except Exception as e:
                results[name] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
        self._status = results
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """Get current health status"""
        return self._status

class PerformanceMonitor:
    """Performance monitoring"""
    
    def __init__(self):
        self._metrics: Dict[str, Any] = {}
    
    async def collect_metrics(self):
        """Collect performance metrics"""
        # System metrics
        self._metrics["system"] = {
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "used": psutil.virtual_memory().used,
                "percent": psutil.virtual_memory().percent
            },
            "cpu": {
                "percent": psutil.cpu_percent(interval=1),
                "count": psutil.cpu_count(),
                "per_cpu": psutil.cpu_percent(interval=1, percpu=True)
            },
            "disk": {
                "total": psutil.disk_usage("/").total,
                "used": psutil.disk_usage("/").used,
                "free": psutil.disk_usage("/").free,
                "percent": psutil.disk_usage("/").percent
            }
        }
        
        # Update Prometheus metrics
        SYSTEM_MEMORY.labels(type="total").set(self._metrics["system"]["memory"]["total"])
        SYSTEM_MEMORY.labels(type="available").set(self._metrics["system"]["memory"]["available"])
        SYSTEM_MEMORY.labels(type="used").set(self._metrics["system"]["memory"]["used"])
        
        SYSTEM_CPU.labels(core="total").set(self._metrics["system"]["cpu"]["percent"])
        for i, percent in enumerate(self._metrics["system"]["cpu"]["per_cpu"]):
            SYSTEM_CPU.labels(core=f"core_{i}").set(percent)
        
        SYSTEM_DISK.labels(type="total").set(self._metrics["system"]["disk"]["total"])
        SYSTEM_DISK.labels(type="used").set(self._metrics["system"]["disk"]["used"])
        SYSTEM_DISK.labels(type="free").set(self._metrics["system"]["disk"]["free"])
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return self._metrics

class UsageTracker:
    """Usage statistics tracking"""
    
    def __init__(self):
        self._stats: Dict[str, Dict[str, Any]] = {}
    
    def track_request(self, request: Request, response: Response, duration: float):
        """Track HTTP request"""
        endpoint = request.url.path
        method = request.method
        status = response.status_code
        
        if endpoint not in self._stats:
            self._stats[endpoint] = {
                "requests": 0,
                "errors": 0,
                "total_duration": 0,
                "methods": {}
            }
        
        self._stats[endpoint]["requests"] += 1
        self._stats[endpoint]["total_duration"] += duration
        
        if method not in self._stats[endpoint]["methods"]:
            self._stats[endpoint]["methods"][method] = 0
        self._stats[endpoint]["methods"][method] += 1
        
        if status >= 400:
            self._stats[endpoint]["errors"] += 1
    
    def track_cache(self, cache_name: str, hit: bool):
        """Track cache usage"""
        if cache_name not in self._stats:
            self._stats[cache_name] = {
                "hits": 0,
                "misses": 0
            }
        
        if hit:
            self._stats[cache_name]["hits"] += 1
        else:
            self._stats[cache_name]["misses"] += 1
    
    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get usage statistics"""
        return self._stats

class ErrorTracker:
    """Error tracking"""
    
    def __init__(self):
        self._errors: List[Dict[str, Any]] = []
        self._max_errors = 1000  # Keep last 1000 errors
    
    def track_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ):
        """Track an error"""
        error_info = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": type(error).__name__,
            "message": str(error),
            "context": context or {}
        }
        
        self._errors.append(error_info)
        if len(self._errors) > self._max_errors:
            self._errors.pop(0)
        
        # Update Prometheus metrics
        ERROR_COUNT.labels(
            method=context.get("method", "unknown"),
            endpoint=context.get("endpoint", "unknown"),
            error_type=type(error).__name__
        ).inc()
    
    def get_errors(
        self,
        error_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get tracked errors with optional filtering"""
        errors = self._errors
        
        if error_type:
            errors = [e for e in errors if e["type"] == error_type]
        
        if start_time:
            errors = [e for e in errors if datetime.fromisoformat(e["timestamp"]) >= start_time]
        
        if end_time:
            errors = [e for e in errors if datetime.fromisoformat(e["timestamp"]) <= end_time]
        
        return errors

class SystemMonitor:
    """System status monitoring"""
    
    def __init__(self):
        self._status: Dict[str, Any] = {}
        self._last_check: Optional[datetime] = None
    
    async def check_system_status(self) -> Dict[str, Any]:
        """Check system status"""
        self._status = {
            "timestamp": datetime.utcnow().isoformat(),
            "services": {},
            "resources": {
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "used": psutil.virtual_memory().used,
                    "percent": psutil.virtual_memory().percent
                },
                "cpu": {
                    "percent": psutil.cpu_percent(interval=1),
                    "count": psutil.cpu_count()
                },
                "disk": {
                    "total": psutil.disk_usage("/").total,
                    "used": psutil.disk_usage("/").used,
                    "free": psutil.disk_usage("/").free,
                    "percent": psutil.disk_usage("/").percent
                }
            }
        }
        
        # Check service status
        settings = config_manager.get_settings()
        for service_name, service_url in settings.services.get_all_services().items():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{service_url}/health", timeout=5) as response:
                        self._status["services"][service_name] = {
                            "status": "healthy" if response.status == 200 else "unhealthy",
                            "response_time": response.elapsed.total_seconds()
                        }
            except Exception as e:
                self._status["services"][service_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        self._last_check = datetime.utcnow()
        return self._status
    
    def get_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return self._status

# Initialize monitoring components
health_check = HealthCheck()
performance_monitor = PerformanceMonitor()
usage_tracker = UsageTracker()
error_tracker = ErrorTracker()
system_monitor = SystemMonitor()

# Register default health checks
async def check_database():
    """Check database connection"""
    try:
        # Add your database health check logic here
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False

async def check_redis():
    """Check Redis connection"""
    try:
        await cache_manager.init()
        return True
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return False

async def check_disk_space():
    """Check disk space"""
    try:
        disk_usage = psutil.disk_usage("/")
        return disk_usage.percent < 90  # Alert if disk usage is above 90%
    except Exception as e:
        logger.error(f"Disk space check failed: {str(e)}")
        return False

health_check.register_check("database", check_database)
health_check.register_check("redis", check_redis)
health_check.register_check("disk_space", check_disk_space) 