"""Database connection and session management.

Implements async SQLAlchemy engine with connection pooling.
Reference: Section C3 for database architecture.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator
import logging

from backend.config import settings

logger = logging.getLogger(__name__)

# Convert postgresql:// to postgresql+psycopg:// for async support
database_url = settings.database_url.replace("postgresql://", "postgresql+psycopg://")

# Create async engine with connection pooling
# Pool size: 20 connections, max_overflow: 10 (as per plan)
engine = create_async_engine(
    database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    echo=False,  # Set to True for SQL query logging
    future=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get database session.
    
    Yields:
        AsyncSession: Database session for use in route handlers
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database - verify connection."""
    try:
        async with engine.begin() as conn:
            # Test connection
            await conn.execute("SELECT 1")
        logger.info("Database connection established successfully")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
    logger.info("Database connections closed")
