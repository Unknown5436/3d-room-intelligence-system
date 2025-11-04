"""Helper functions for database tests.

Provides utilities for checking database availability and skipping tests gracefully.
"""
import pytest
from sqlalchemy.ext.asyncio import create_async_engine
import os


def check_db_available():
    """Check if test database is available.
    
    Returns:
        bool: True if database is available, False otherwise
    """
    test_db_url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+psycopg://room_intel:secure_password@localhost:5432/room_intelligence_test"
    )
    
    try:
        engine = create_async_engine(
            test_db_url,
            poolclass=None,
            connect_args={"connect_timeout": 2}
        )
        # Try to connect (synchronous check)
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Can't check synchronously in running loop
                return True  # Assume available
            else:
                # Test connection
                async def test_conn():
                    async with engine.begin() as conn:
                        await conn.execute("SELECT 1")
                    await engine.dispose()
                
                loop.run_until_complete(test_conn())
                return True
        except RuntimeError:
            # No event loop
            async def test_conn():
                async with engine.begin() as conn:
                    await conn.execute("SELECT 1")
                await engine.dispose()
            
            asyncio.run(test_conn())
            return True
    except Exception:
        return False


def skip_if_no_db():
    """Pytest fixture helper to skip test if database is not available."""
    if not check_db_available():
        pytest.skip("Database not available - run 'docker-compose up -d postgres' to start database")


