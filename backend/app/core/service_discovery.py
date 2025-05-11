from typing import Dict, List, Optional, Any
import aiohttp
import asyncio
from datetime import datetime, timedelta
import json
from app.core.logging import logger
from app.core.config_manager import config_manager

class ServiceRegistry:
    """Service registry for managing service discovery"""
    
    def __init__(self):
        self._services: Dict[str, Dict[str, Any]] = {}
        self._health_checks: Dict[str, asyncio.Task] = {}
        self._last_health_check: Dict[str, datetime] = {}
    
    def register_service(
        self,
        name: str,
        url: str,
        health_check_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Register a service"""
        self._services[name] = {
            "url": url,
            "health_check_url": health_check_url or f"{url}/health",
            "metadata": metadata or {},
            "status": "unknown",
            "last_updated": datetime.utcnow()
        }
        logger.info(f"Registered service: {name} at {url}")
    
    def unregister_service(self, name: str):
        """Unregister a service"""
        if name in self._services:
            del self._services[name]
            if name in self._health_checks:
                self._health_checks[name].cancel()
                del self._health_checks[name]
            logger.info(f"Unregistered service: {name}")
    
    def get_service(self, name: str) -> Optional[Dict[str, Any]]:
        """Get service information"""
        return self._services.get(name)
    
    def get_all_services(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered services"""
        return self._services.copy()
    
    def update_service_status(self, name: str, status: str):
        """Update service status"""
        if name in self._services:
            self._services[name]["status"] = status
            self._services[name]["last_updated"] = datetime.utcnow()
            logger.info(f"Updated service status: {name} -> {status}")
    
    async def check_service_health(self, name: str) -> bool:
        """Check service health"""
        service = self.get_service(name)
        if not service:
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(service["health_check_url"], timeout=5) as response:
                    is_healthy = response.status == 200
                    self.update_service_status(name, "healthy" if is_healthy else "unhealthy")
                    return is_healthy
        except Exception as e:
            logger.error(f"Health check failed for {name}: {str(e)}")
            self.update_service_status(name, "unhealthy")
            return False
    
    async def start_health_checks(self):
        """Start health check monitoring"""
        for name in self._services:
            if name not in self._health_checks:
                self._health_checks[name] = asyncio.create_task(
                    self._monitor_service_health(name)
                )
    
    async def stop_health_checks(self):
        """Stop health check monitoring"""
        for task in self._health_checks.values():
            task.cancel()
        self._health_checks.clear()
    
    async def _monitor_service_health(self, name: str):
        """Monitor service health"""
        while True:
            try:
                await self.check_service_health(name)
                await asyncio.sleep(
                    config_manager.get_settings().services.SERVICE_HEALTH_CHECK_INTERVAL
                )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check monitoring failed for {name}: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying
    
    def get_healthy_services(self) -> Dict[str, Dict[str, Any]]:
        """Get all healthy services"""
        return {
            name: service
            for name, service in self._services.items()
            if service["status"] == "healthy"
        }
    
    def get_unhealthy_services(self) -> Dict[str, Dict[str, Any]]:
        """Get all unhealthy services"""
        return {
            name: service
            for name, service in self._services.items()
            if service["status"] == "unhealthy"
        }

class ServiceDiscovery:
    """Service discovery manager"""
    
    def __init__(self):
        self.registry = ServiceRegistry()
    
    async def register_service(
        self,
        name: str,
        url: str,
        health_check_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Register a service"""
        self.registry.register_service(name, url, health_check_url, metadata)
    
    def unregister_service(self, name: str):
        """Unregister a service"""
        self.registry.unregister_service(name)
    
    def get_service(self, name: str) -> Optional[Dict[str, Any]]:
        """Get service information"""
        return self.registry.get_service(name)
    
    def get_all_services(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered services"""
        return self.registry.get_all_services()
    
    def get_healthy_services(self) -> Dict[str, Dict[str, Any]]:
        """Get all healthy services"""
        return self.registry.get_healthy_services()
    
    def get_unhealthy_services(self) -> Dict[str, Dict[str, Any]]:
        """Get all unhealthy services"""
        return self.registry.get_unhealthy_services()
    
    async def start(self):
        """Start service discovery"""
        await self.registry.start_health_checks()
        logger.info("Service discovery started")
    
    async def stop(self):
        """Stop service discovery"""
        await self.registry.stop_health_checks()
        logger.info("Service discovery stopped")

# Initialize service discovery
service_discovery = ServiceDiscovery() 