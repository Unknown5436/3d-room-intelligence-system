"""Pytest configuration and fixtures for testing.

Provides test fixtures for FastAPI client, database sessions, and synthetic PLY file generation.
"""
import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from typing import AsyncGenerator, Generator
import numpy as np
import open3d as o3d
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from backend.api.main import app
from backend.database.connection import get_db_session, engine, AsyncSessionLocal
from backend.config import settings


# Test database URL (use in-memory or test database)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://room_intel:secure_password@localhost:5432/room_intelligence_test"
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_db_engine():
    """Create a test database engine."""
    test_engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )
    yield test_engine
    test_engine.dispose()


@pytest.fixture
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session with transaction rollback."""
    async_session_maker = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    async with async_session_maker() as session:
        async with session.begin():
            yield session
            await session.rollback()


@pytest.fixture
def test_client(test_db_session: AsyncSession) -> TestClient:
    """Create a FastAPI test client with dependency overrides."""
    
    def override_get_db():
        """Override database session dependency for testing."""
        return test_db_session
    
    app.dependency_overrides[get_db_session] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def mock_room_data() -> dict:
    """Mock room data for testing."""
    return {
        "dimensions": {
            "length": 4.5,
            "width": 3.2,
            "height": 2.5,
            "accuracy": "±2-5cm"
        },
        "objects": [
            {
                "type": "table",
                "position": [2.0, 1.5, 0.0],
                "dimensions": [1.2, 0.8, 0.75],
                "volume": 0.72,
                "confidence": 0.78
            },
            {
                "type": "chair",
                "position": [1.5, 1.0, 0.0],
                "dimensions": [0.5, 0.5, 0.45],
                "volume": 0.11,
                "confidence": 0.72
            }
        ]
    }


@pytest.fixture
def synthetic_ply_file() -> Generator[str, None, None]:
    """Generate a synthetic PLY file for testing.
    
    Creates a simple room-like point cloud with:
    - Floor plane (z=0)
    - Walls (x=0, x=4, y=0, y=3)
    - Ceiling (z=2.5)
    - Simple object (table-like cluster)
    
    Returns:
        Path to temporary PLY file
    """
    # Create synthetic room point cloud
    points = []
    colors = []
    
    # Floor (z=0, 4m x 3m, spaced every 5cm)
    for x in np.arange(0, 4.0, 0.05):
        for y in np.arange(0, 3.0, 0.05):
            points.append([x, y, 0.0])
            colors.append([0.9, 0.9, 0.9])  # Light gray
    
    # Walls (vertical planes)
    # Wall at x=0
    for y in np.arange(0, 3.0, 0.05):
        for z in np.arange(0, 2.5, 0.05):
            points.append([0.0, y, z])
            colors.append([0.8, 0.8, 0.8])
    
    # Wall at x=4
    for y in np.arange(0, 3.0, 0.05):
        for z in np.arange(0, 2.5, 0.05):
            points.append([4.0, y, z])
            colors.append([0.8, 0.8, 0.8])
    
    # Wall at y=0
    for x in np.arange(0, 4.0, 0.05):
        for z in np.arange(0, 2.5, 0.05):
            points.append([x, 0.0, z])
            colors.append([0.8, 0.8, 0.8])
    
    # Wall at y=3
    for x in np.arange(0, 4.0, 0.05):
        for z in np.arange(0, 2.5, 0.05):
            points.append([x, 3.0, z])
            colors.append([0.8, 0.8, 0.8])
    
    # Ceiling (z=2.5)
    for x in np.arange(0, 4.0, 0.05):
        for y in np.arange(0, 3.0, 0.05):
            points.append([x, y, 2.5])
            colors.append([0.9, 0.9, 0.9])
    
    # Simple object: table-like (1.2m x 0.8m x 0.75m, centered at [2.0, 1.5, 0.75])
    table_center = [2.0, 1.5, 0.75]
    table_dims = [1.2, 0.8, 0.75]
    
    # Table top (horizontal rectangle)
    for x in np.arange(table_center[0] - table_dims[0]/2, 
                       table_center[0] + table_dims[0]/2, 0.03):
        for y in np.arange(table_center[1] - table_dims[1]/2,
                           table_center[1] + table_dims[1]/2, 0.03):
            points.append([x, y, table_center[2]])
            colors.append([0.6, 0.4, 0.2])  # Brown
    
    # Table legs (4 corners)
    leg_positions = [
        [table_center[0] - table_dims[0]/2 + 0.1, table_center[1] - table_dims[1]/2 + 0.1],
        [table_center[0] + table_dims[0]/2 - 0.1, table_center[1] - table_dims[1]/2 + 0.1],
        [table_center[0] - table_dims[0]/2 + 0.1, table_center[1] + table_dims[1]/2 - 0.1],
        [table_center[0] + table_dims[0]/2 - 0.1, table_center[1] + table_dims[1]/2 - 0.1],
    ]
    
    for leg_x, leg_y in leg_positions:
        for z in np.arange(0, table_center[2], 0.02):
            points.append([leg_x, leg_y, z])
            colors.append([0.6, 0.4, 0.2])
    
    # Convert to numpy arrays
    points_array = np.array(points, dtype=np.float32)
    colors_array = np.array(colors, dtype=np.float32)
    
    # Create Open3D point cloud
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points_array)
    pcd.colors = o3d.utility.Vector3dVector(colors_array)
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix=".ply", delete=False) as tmp:
        tmp_path = tmp.name
    
    o3d.io.write_point_cloud(tmp_path, pcd)
    
    yield tmp_path
    
    # Cleanup
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


@pytest.fixture
def small_synthetic_ply() -> Generator[str, None, None]:
    """Generate a small synthetic PLY file for fast tests.
    
    Similar to synthetic_ply_file but with fewer points.
    """
    # Create minimal room (2m x 2m x 2m)
    points = []
    colors = []
    
    # Floor (sparse, every 20cm)
    for x in np.arange(0, 2.0, 0.20):
        for y in np.arange(0, 2.0, 0.20):
            points.append([x, y, 0.0])
            colors.append([0.9, 0.9, 0.9])
    
    # Walls (sparse)
    for y in np.arange(0, 2.0, 0.20):
        for z in np.arange(0, 2.0, 0.20):
            points.append([0.0, y, z])
            colors.append([0.8, 0.8, 0.8])
            points.append([2.0, y, z])
            colors.append([0.8, 0.8, 0.8])
    
    for x in np.arange(0, 2.0, 0.20):
        for z in np.arange(0, 2.0, 0.20):
            points.append([x, 0.0, z])
            colors.append([0.8, 0.8, 0.8])
            points.append([x, 2.0, z])
            colors.append([0.8, 0.8, 0.8])
    
    # Ceiling
    for x in np.arange(0, 2.0, 0.20):
        for y in np.arange(0, 2.0, 0.20):
            points.append([x, y, 2.0])
            colors.append([0.9, 0.9, 0.9])
    
    points_array = np.array(points, dtype=np.float32)
    colors_array = np.array(colors, dtype=np.float32)
    
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points_array)
    pcd.colors = o3d.utility.Vector3dVector(colors_array)
    
    with tempfile.NamedTemporaryFile(suffix=".ply", delete=False) as tmp:
        tmp_path = tmp.name
    
    o3d.io.write_point_cloud(tmp_path, pcd)
    
    yield tmp_path
    
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)

