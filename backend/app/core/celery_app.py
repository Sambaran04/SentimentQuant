from celery import Celery
from app.core.config import settings
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Note: This file is prepared for future migration to ARQ (Redis-based async task queue)
# Arq offers better integration with asyncio, is more lightweight and simpler than Celery
# See the ARQ_MIGRATION.md for migration instructions when ready

# For a smooth migration, we're keeping both implementations side by side
# The current Celery implementation will continue to work while ARQ is being integrated
# Ref: https://arq-docs.helpmanual.io/

celery_app = Celery(
    "sentiment_quant",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
    include=["app.tasks.sentiment_tasks", "app.tasks.market_data_tasks"]
)

# Celery configuration optimized for better performance
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution settings
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 minutes
    worker_max_tasks_per_child=1000,
    worker_prefetch_multiplier=1,  # Set to 1 for fair task distribution
    
    # Task ack settings
    task_acks_late=True,  # ACK after task finishes
    task_reject_on_worker_lost=True,  # Requeue tasks if worker crashes
    
    # Result settings
    task_ignore_result=False,  # Set to True for tasks that don't need results
    result_expires=3600,  # 1 hour for results to expire
    
    # Retry settings
    task_default_retry_delay=60,  # 1 minute before retrying
    task_max_retries=3,  # Maximum 3 retries
    
    # Queue settings
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

# Create ARQ migration doc if it doesn't exist
def create_arq_migration_doc():
    migration_doc_path = Path(os.path.dirname(os.path.abspath(__file__))) / "ARQ_MIGRATION.md"
    if not migration_doc_path.exists():
        with open(migration_doc_path, "w") as f:
            f.write("""# Migrating from Celery to ARQ

ARQ is a lightweight async task queue built on Redis and designed to work with asyncio.
This document outlines how to migrate tasks from Celery to ARQ.

## Benefits of ARQ

- Lightweight: ARQ is much simpler and lightweight than Celery
- AsyncIO Compatible: Built for asyncio, works naturally with FastAPI
- Redis-focused: Uses Redis as its only backend, simplifying the infrastructure
- Fast: Minimal overhead and designed for high throughput

## Migration Steps

1. Install ARQ:
   ```
   pip install arq
   ```

2. Create ARQ worker class:
   ```python
   from arq import Worker, create_pool
   from arq.connections import RedisSettings

   async def startup(ctx):
       # Initialization code here
       ctx['db'] = await connect_to_db()

   async def shutdown(ctx):
       # Cleanup code here
       await ctx['db'].close()

   class WorkerSettings:
       redis_settings = RedisSettings(
           host=settings.REDIS_HOST,
           port=settings.REDIS_PORT,
           password=settings.REDIS_PASSWORD,
           database=settings.REDIS_DB
       )
       functions = [
           process_sentiment,
           fetch_market_data,
       ]
       on_startup = startup
       on_shutdown = shutdown
       max_jobs = 10
       job_timeout = 3600  # 1 hour
   ```

3. Convert Celery tasks to ARQ functions:

   Celery task:
   ```python
   @celery_app.task
   def analyze_sentiment(symbol):
       # Task code
       return result
   ```

   ARQ function:
   ```python
   async def analyze_sentiment(ctx, symbol):
       # Task code
       return result
   ```

4. Enqueue tasks:

   Celery:
   ```python
   analyze_sentiment.delay(symbol)
   ```

   ARQ:
   ```python
   redis = await create_pool(RedisSettings(...))
   await redis.enqueue_job('analyze_sentiment', symbol)
   ```

5. Run the worker:
   ```
   arq WorkerSettings
   ```

## Gradual Migration Strategy

1. Start by migrating non-critical tasks
2. Run both Celery and ARQ workers in parallel
3. Gradually move more tasks to ARQ
4. Once all tasks are migrated, remove Celery

For more details, see the [ARQ Documentation](https://arq-docs.helpmanual.io/).
""")
        logger.info("Created ARQ migration document")

# Create ARQ migration doc on startup
create_arq_migration_doc()

@celery_app.task(bind=True)
def debug_task(self):
    logger.info(f"Request: {self.request!r}") 