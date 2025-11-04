"""Database connection and session management.

Implements async SQLAlchemy engine with connection pooling.
Reference: Section C3 for database architecture.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator, Optional, Any
import logging
import os

from backend.config import settings

logger = logging.getLogger(__name__)

# Lazy engine creation to avoid import-time DB connections during testing
_engine: Optional[Any] = None
_AsyncSessionLocal: Optional[Any] = None

def _initialize_engine():
    """Initialize the database engine (lazy, only when needed)."""
    global _engine, _AsyncSessionLocal
    
    if _engine is None:
        # Skip engine creation during test imports if TEST_MODE is set
        if os.getenv("TEST_MODE") == "true":
            logger.debug("TEST_MODE enabled - skipping engine creation")
            return None
        
        # Convert postgresql:// to postgresql+psycopg:// for async support
        database_url = settings.database_url.replace("postgresql://", "postgresql+psycopg://")
        
        # Create async engine with connection pooling
        # Pool size: 20 connections, max_overflow: 10 (as per plan)
        _engine = create_async_engine(
            database_url,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            echo=False,  # Set to True for SQL query logging
            future=True,
        )
        
        # Create async session factory
        _AsyncSessionLocal = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    
    return _engine

# Create engine/session on module import (but skip in TEST_MODE)
# This maintains backward compatibility while allowing tests to override
if os.getenv("TEST_MODE") != "true":
    _initialize_engine()

# Export engine and session maker (will be None in TEST_MODE, created lazily)
engine = _engine
AsyncSessionLocal = _AsyncSessionLocal


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get database session.
    
    Yields:
        AsyncSession: Database session for use in route handlers
    """
    # Ensure engine is initialized
    if _AsyncSessionLocal is None:
        _initialize_engine()
    
    async with _AsyncSessionLocal() as session:
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
        # Ensure engine is initialized
        if _engine is None:
            _initialize_engine()
        
        async with _engine.begin() as conn:
            # Test connection
            await conn.execute("SELECT 1")
        logger.info("Database connection established successfully")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise


async def close_db() -> None:
    """Close database connections."""
    if _engine is not None:
        await _engine.dispose()
    logger.info("Database connections closed")
