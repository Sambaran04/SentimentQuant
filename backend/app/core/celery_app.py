from celery import Celery
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

celery_app = Celery(
    "sentiment_quant",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
    include=["app.tasks.sentiment_tasks", "app.tasks.market_data_tasks"]
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
    task_soft_time_limit=3300,  # 55 minutes
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
        "sentiment": {
            "exchange": "sentiment",
            "routing_key": "sentiment",
        },
        "market_data": {
            "exchange": "market_data",
            "routing_key": "market_data",
        }
    },
    task_routes={
        "app.tasks.sentiment_tasks.*": {"queue": "sentiment"},
        "app.tasks.market_data_tasks.*": {"queue": "market_data"},
    }
)

@celery_app.task(bind=True)
def debug_task(self):
    logger.info(f"Request: {self.request!r}") 