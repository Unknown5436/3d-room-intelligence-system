"""Room data retrieval routes.

Handles room dimensions, objects, and complete room data queries.
Reference: Section E1 for room endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging

from backend.database.connection import get_db_session
from backend.database.repositories import RoomRepository
from backend.api.models.schemas import RoomDimensions, SpatialObject, RoomData

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{room_id}/dimensions", response_model=RoomDimensions)
async def get_room_dimensions(
    room_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Get room dimensions.
    
    Reference: Section E1 - GET /room/{id}/dimensions.
    Response time target: <1 second (Section F2).
    
    Args:
        room_id: Room identifier
        session: Database session
        
    Returns:
        RoomDimensions: Room dimensions with accuracy
    """
    repo = RoomRepository(session)
    dimensions = await repo.get_room_dimensions(room_id)
    
    if not dimensions:
        raise HTTPException(status_code=404, detail=f"Room {room_id} not found")
    
    return RoomDimensions(**dimensions)


@router.get("/{room_id}/objects", response_model=List[SpatialObject])
async def get_room_objects(
    room_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Get detected objects for a room.
    
    Reference: Section E1 - GET /room/{id}/objects.
    
    Args:
        room_id: Room identifier
        session: Database session
        
    Returns:
        List[SpatialObject]: List of detected objects
    """
    repo = RoomRepository(session)
    room = await repo.get_room_by_id(room_id)
    
    if not room:
        raise HTTPException(status_code=404, detail=f"Room {room_id} not found")
    
    objects = await repo.get_room_objects(room_id)
    
    # Convert database objects to Pydantic models
    spatial_objects = []
    for obj in objects:
        # Extract position from geometry (simplified - real implementation needs proper WKT parsing)
        position = [0.0, 0.0, 0.0]  # Placeholder
        
        # Extract dimensions from JSONB
        dims_dict = obj.dimensions if obj.dimensions else {}
        dimensions = [
            dims_dict.get("length", 0.0),
            dims_dict.get("width", 0.0),
            dims_dict.get("height", 0.0)
        ]
        
        spatial_objects.append(SpatialObject(
            type=obj.object_type or "unknown",
            position=position,
            dimensions=dimensions,
            volume=obj.volume or 0.0,
            confidence=obj.confidence or 0.0
        ))
    
    return spatial_objects


@router.get("/{room_id}/data", response_model=RoomData)
async def get_room_data(
    room_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Get complete room data.
    
    Reference: Section E1 - GET /room/{id}/data.
    
    Args:
        room_id: Room identifier
        session: Database session
        
    Returns:
        RoomData: Complete room data including dimensions, objects, point counts
    """
    repo = RoomRepository(session)
    room = await repo.get_room_by_id(room_id)
    
    if not room:
        raise HTTPException(status_code=404, detail=f"Room {room_id} not found")
    
    # Get dimensions
    dimensions = await repo.get_room_dimensions(room_id)
    if not dimensions:
        raise HTTPException(status_code=404, detail=f"Room {room_id} dimensions not found")
    
    # Get objects
    objects = await repo.get_room_objects(room_id)
    
    # Convert to Pydantic models (simplified - same as get_room_objects)
    spatial_objects = []
    for obj in objects:
        position = [0.0, 0.0, 0.0]  # Placeholder
        dims_dict = obj.dimensions if obj.dimensions else {}
        dimensions_list = [
            dims_dict.get("length", 0.0),
            dims_dict.get("width", 0.0),
            dims_dict.get("height", 0.0)
        ]
        spatial_objects.append(SpatialObject(
            type=obj.object_type or "unknown",
            position=position,
            dimensions=dimensions_list,
            volume=obj.volume or 0.0,
            confidence=obj.confidence or 0.0
        ))
    
    return RoomData(
        room_id=room_id,
        dimensions=RoomDimensions(**dimensions),
        objects=spatial_objects,
        point_count=room.point_count or 0,
        processed_points=room.processed_points or 0
    )
