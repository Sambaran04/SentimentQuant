from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
from app.core.config_manager import config_manager
from app.core.monitoring import (
    health_check,
    performance_monitor,
    system_monitor
)
from app.core.middleware import UnifiedMonitoringMiddleware
from app.api.v1.endpoints import monitoring
from app.core.logging import logger

# Create FastAPI app
app = FastAPI(
    title="SentimentQuant API",
    description="API for sentiment analysis and quantitative trading",
    version=config_manager.get_settings().VERSION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config_manager.get_settings().CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add unified monitoring middleware
app.add_middleware(
    UnifiedMonitoringMiddleware,
    exclude_paths={"/metrics", "/health", "/docs", "/redoc", "/openapi.json"},
    enable_logging=True,
    enable_metrics=True,
    enable_performance=True
)

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include routers
app.include_router(
    monitoring.router,
    prefix="/monitoring",
    tags=["monitoring"]
)

@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("Starting up application...")
    
    # Start performance monitoring
    await performance_monitor.start()
    
    # Start system monitoring
    await system_monitor.start()
    
    # Register default health checks
    health_check.register_check("database", health_check.check_database)
    health_check.register_check("redis", health_check.check_redis)
    health_check.register_check("disk", health_check.check_disk_space)
    
    logger.info("Application startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("Shutting down application...")
    
    # Stop performance monitoring
    await performance_monitor.stop()
    
    # Stop system monitoring
    await system_monitor.stop()
    
    logger.info("Application shutdown complete")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "SentimentQuant API",
        "version": config_manager.get_settings().VERSION,
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=config_manager.get_settings().HOST,
        port=config_manager.get_settings().PORT,
        reload=config_manager.get_settings().DEBUG
    ) 