from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.sql import text
from typing import Optional, List, Any
from app.core.config import settings
from app.core.logging import logger
import time
from functools import wraps

# Create async engine with connection pooling
async_engine = create_async_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,  # Recycle connections after 30 minutes
    echo=settings.DEBUG
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Create sync engine with connection pooling
sync_engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    echo=settings.DEBUG
)

# Create sync session factory
SessionLocal = sessionmaker(
    sync_engine,
    expire_on_commit=False
)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db():
    """Get async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

class QueryOptimizer:
    """Query optimization utilities"""
    
    @staticmethod
    def add_indexes(session: Session, model_class: Any):
        """Add indexes to model if they don't exist"""
        try:
            # Get table name
            table_name = model_class.__tablename__
            
            # Add indexes for common query patterns
            indexes = [
                # Example indexes - adjust based on your query patterns
                f"CREATE INDEX IF NOT EXISTS idx_{table_name}_created_at ON {table_name} (created_at)",
                f"CREATE INDEX IF NOT EXISTS idx_{table_name}_updated_at ON {table_name} (updated_at)",
                f"CREATE INDEX IF NOT EXISTS idx_{table_name}_status ON {table_name} (status)"
            ]
            
            for index in indexes:
                session.execute(text(index))
            
            session.commit()
            logger.info(f"Added indexes for {table_name}")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to add indexes: {str(e)}")
            raise
    
    @staticmethod
    def optimize_query(query: str) -> str:
        """Optimize SQL query"""
        # Remove unnecessary whitespace
        query = " ".join(query.split())
        
        # Add query hints if needed
        if "SELECT" in query.upper():
            # Add index hints for specific tables
            query = query.replace(
                "FROM stocks",
                "FROM stocks USE INDEX (idx_stocks_symbol)"
            )
        
        return query

def query_timer(func):
    """Decorator to measure query execution time"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        # Log slow queries
        if execution_time > 1.0:  # Log queries taking more than 1 second
            logger.warning(
                f"Slow query detected in {func.__name__}",
                extra={
                    "execution_time": execution_time,
                    "args": args,
                    "kwargs": kwargs
                }
            )
        
        return result
    return wrapper

class DatabaseStats:
    """Database statistics and monitoring"""
    
    @staticmethod
    async def get_table_stats(session: AsyncSession, table_name: str) -> dict:
        """Get table statistics"""
        try:
            # Get row count
            row_count = await session.execute(
                text(f"SELECT COUNT(*) FROM {table_name}")
            )
            row_count = row_count.scalar()
            
            # Get table size
            table_size = await session.execute(
                text(f"""
                    SELECT pg_size_pretty(pg_total_relation_size('{table_name}'))
                """)
            )
            table_size = table_size.scalar()
            
            # Get index usage
            index_usage = await session.execute(
                text(f"""
                    SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
                    FROM pg_stat_user_indexes
                    WHERE tablename = '{table_name}'
                """)
            )
            index_usage = index_usage.fetchall()
            
            return {
                "row_count": row_count,
                "table_size": table_size,
                "index_usage": index_usage
            }
        except Exception as e:
            logger.error(f"Failed to get table stats: {str(e)}")
            raise
    
    @staticmethod
    async def get_slow_queries(session: AsyncSession, limit: int = 10) -> List[dict]:
        """Get slow queries from pg_stat_statements"""
        try:
            result = await session.execute(
                text(f"""
                    SELECT query, calls, total_time, mean_time
                    FROM pg_stat_statements
                    ORDER BY mean_time DESC
                    LIMIT {limit}
                """)
            )
            return result.fetchall()
        except Exception as e:
            logger.error(f"Failed to get slow queries: {str(e)}")
            raise

# Initialize query optimizer
query_optimizer = QueryOptimizer()

# Initialize database stats
db_stats = DatabaseStats() 