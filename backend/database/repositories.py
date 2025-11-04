"""
Repository pattern for database access.

Implements data access layer with spatial queries using PostGIS functions.
All methods use async SQLAlchemy sessions for non-blocking database access.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sql_func
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
import logging

from backend.database.models import Room, PointCloudPatch, DetectedObject

logger = logging.getLogger(__name__)


class RoomRepository:
    """Repository for room-related database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_room(
        self,
        room_id: str,
        point_count: int,
        processed_points: int,
        length: Optional[float] = None,
        width: Optional[float] = None,
        height: Optional[float] = None,
        accuracy: Optional[str] = None,
        scan_quality: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Room:
        """
        Create a new room record.
        
        Args:
            room_id: Unique room identifier
            point_count: Total point count in original scan
            processed_points: Point count after processing
            length: Room length in meters
            width: Room width in meters
            height: Room height in meters
            accuracy: Accuracy estimate (e.g., "±2-5cm")
            scan_quality: Quality score 0-1
            metadata: Additional metadata dict
            
        Returns:
            Room: Created room object
        """
        room = Room(
            room_id=room_id,
            point_count=point_count,
            processed_points=processed_points,
            length=length,
            width=width,
            height=height,
            accuracy=accuracy,
            scan_quality=scan_quality,
            extra_metadata=metadata or {}
        )
        self.session.add(room)
        await self.session.flush()
        await self.session.refresh(room)
        logger.info(f"Created room: {room_id}")
        return room
    
    async def get_room_by_id(self, room_id: str) -> Optional[Room]:
        """
        Get room by room_id.
        
        Args:
            room_id: Room identifier
            
        Returns:
            Room or None if not found
        """
        result = await self.session.execute(
            select(Room).where(Room.room_id == room_id)
        )
        return result.scalar_one_or_none()
    
    async def get_room_dimensions(self, room_id: str) -> Optional[Dict[str, Any]]:
        """
        Get room dimensions by room_id.
        
        Args:
            room_id: Room identifier
            
        Returns:
            Dict with length, width, height, accuracy or None
        """
        room = await self.get_room_by_id(room_id)
        if not room:
            return None
        
        return {
            "length": room.length,
            "width": room.width,
            "height": room.height,
            "accuracy": room.accuracy
        }
    
    async def get_room_objects(
        self,
        room_id: str,
        object_type: Optional[str] = None
    ) -> List[DetectedObject]:
        """
        Get detected objects for a room.
        
        Args:
            room_id: Room identifier
            object_type: Optional filter by object type
            
        Returns:
            List of DetectedObject objects
        """
        # First get the room to get its ID
        room = await self.get_room_by_id(room_id)
        if not room:
            return []
        
        query = select(DetectedObject).where(DetectedObject.room_id == room.id)
        
        if object_type:
            query = query.where(DetectedObject.object_type == object_type)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_room_quality(
        self,
        room_id: str,
        scan_quality: float
    ) -> bool:
        """
        Update scan quality for a room.
        
        Args:
            room_id: Room identifier
            scan_quality: Quality score 0-1
            
        Returns:
            True if updated, False if room not found
        """
        room = await self.get_room_by_id(room_id)
        if not room:
            return False
        
        room.scan_quality = scan_quality
        await self.session.flush()
        return True


class ObjectRepository:
    """Repository for detected object operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_object(
        self,
        room_id: str,
        object_type: str,
        position: List[float],  # [x, y, z]
        dimensions: Dict[str, float],  # {length, width, height}
        volume: float,
        confidence: float,
        classification_method: str = "geometric",
        metadata: Optional[Dict[str, Any]] = None
    ) -> DetectedObject:
        """
        Create a detected object record.
        
        Args:
            room_id: Room identifier
            object_type: Object type (e.g., "table", "chair")
            position: 3D position [x, y, z]
            dimensions: Dict with length, width, height
            volume: Volume in cubic meters
            confidence: Classification confidence 0-1
            classification_method: "geometric" or "ml"
            metadata: Additional metadata
            
        Returns:
            DetectedObject: Created object
        """
        # Get room to get its ID
        room_repo = RoomRepository(self.session)
        room = await room_repo.get_room_by_id(room_id)
        if not room:
            raise ValueError(f"Room {room_id} not found")
        
        # Create WKT for PointZ: POINTZ(x y z)
        wkt = f"POINTZ({position[0]} {position[1]} {position[2]})"
        
        obj = DetectedObject(
            room_id=room.id,
            object_type=object_type,
            position=wkt,  # GeoAlchemy2 will handle conversion
            dimensions=dimensions,
            volume=volume,
            confidence=confidence,
            classification_method=classification_method,
            extra_metadata=metadata or {}
        )
        
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        logger.info(f"Created object: {object_type} in room {room_id}")
        return obj
    
    async def get_objects_in_radius(
        self,
        room_id: str,
        center: List[float],  # [x, y, z]
        radius: float
    ) -> List[DetectedObject]:
        """
        Get objects within radius of a point (spatial query).
        
        Args:
            room_id: Room identifier
            center: Center point [x, y, z]
            radius: Radius in meters
            
        Returns:
            List of DetectedObject within radius
        """
        room_repo = RoomRepository(self.session)
        room = await room_repo.get_room_by_id(room_id)
        if not room:
            return []
        
        # Use PostGIS ST_DWithin for 3D distance query
        center_wkt = f"POINTZ({center[0]} {center[1]} {center[2]})"
        
        query = select(DetectedObject).where(
            DetectedObject.room_id == room.id,
            sql_func.ST_DWithin(
                DetectedObject.position,
                sql_func.ST_GeomFromText(center_wkt, 4326),
                radius
            )
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

