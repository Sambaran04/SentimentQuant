from celery import Celery
from celery.schedules import crontab
from app.core.config import settings
from app.core.logging import logger
from typing import Any, Dict, Optional
import asyncio
from functools import wraps
import time

# Initialize Celery
celery_app = Celery(
    "sentimentquant",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    worker_max_tasks_per_child=1000,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_queue="default",
    task_queues={
        "default": {
            "exchange": "default",
            "routing_key": "default",
        },
        "high_priority": {
            "exchange": "high_priority",
            "routing_key": "high_priority",
        },
        "low_priority": {
            "exchange": "low_priority",
            "routing_key": "low_priority",
        }
    }
)

# Periodic tasks
celery_app.conf.beat_schedule = {
    "update-market-data": {
        "task": "app.tasks.market_data.update_market_data",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
        "options": {"queue": "high_priority"}
    },
    "cleanup-old-data": {
        "task": "app.tasks.cleanup.cleanup_old_data",
        "schedule": crontab(hour=0, minute=0),  # Daily at midnight
        "options": {"queue": "low_priority"}
    }
}

def async_task(func):
    """Decorator to run async functions in Celery tasks"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(func(*args, **kwargs))
    return wrapper

class TaskManager:
    """Task management utilities"""
    
    @staticmethod
    def create_task(
        task_name: str,
        args: tuple = None,
        kwargs: dict = None,
        queue: str = "default",
        priority: int = 0,
        countdown: int = 0,
        eta: Optional[float] = None,
        expires: Optional[float] = None,
        retry: bool = True,
        retry_policy: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new task"""
        try:
            task = celery_app.send_task(
                task_name,
                args=args,
                kwargs=kwargs,
                queue=queue,
                priority=priority,
                countdown=countdown,
                eta=eta,
                expires=expires,
                retry=retry,
                retry_policy=retry_policy or {
                    "max_retries": 3,
                    "interval_start": 0,
                    "interval_step": 0.2,
                    "interval_max": 0.5
                }
            )
            return task.id
        except Exception as e:
            logger.error(f"Failed to create task {task_name}: {str(e)}")
            raise
    
    @staticmethod
    def get_task_status(task_id: str) -> Dict[str, Any]:
        """Get task status"""
        try:
            task = celery_app.AsyncResult(task_id)
            return {
                "task_id": task_id,
                "status": task.status,
                "result": task.result if task.ready() else None,
                "success": task.successful() if task.ready() else None,
                "error": str(task.result) if task.failed() else None
            }
        except Exception as e:
            logger.error(f"Failed to get task status for {task_id}: {str(e)}")
            raise
    
    @staticmethod
    def revoke_task(task_id: str, terminate: bool = False) -> bool:
        """Revoke a task"""
        try:
            celery_app.control.revoke(task_id, terminate=terminate)
            return True
        except Exception as e:
            logger.error(f"Failed to revoke task {task_id}: {str(e)}")
            return False

def task_timer(func):
    """Decorator to measure task execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        # Log slow tasks
        if execution_time > 60.0:  # Log tasks taking more than 1 minute
            logger.warning(
                f"Slow task detected in {func.__name__}",
                extra={
                    "execution_time": execution_time,
                    "args": args,
                    "kwargs": kwargs
                }
            )
        
        return result
    return wrapper

# Initialize task manager
task_manager = TaskManager() 