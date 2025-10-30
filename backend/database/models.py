"""SQLAlchemy ORM models matching database schema.

Reference: Hybrid database schema from implementation plan.
Uses GeoAlchemy2 for spatial data types.
"""
from sqlalchemy import Column, Integer, String, Float, TIMESTAMP, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from typing import Optional, Dict, Any

Base = declarative_base()


class Room(Base):
    """Room model - primary room metadata."""
    
    __tablename__ = "rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String(50), unique=True, nullable=False, index=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    point_count = Column(Integer)
    processed_points = Column(Integer)
    length = Column(Float)
    width = Column(Float)
    height = Column(Float)
    accuracy = Column(String(50))
    scan_quality = Column(Float)
    metadata = Column(JSONB, default={})
    
    # Relationships
    point_cloud_patches = relationship("PointCloudPatch", back_populates="room", cascade="all, delete-orphan")
    detected_objects = relationship("DetectedObject", back_populates="room", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Room(id={self.id}, room_id='{self.room_id}')>"


class PointCloudPatch(Base):
    """Point cloud patch model - stores point cloud data using PostGIS Pointcloud extension."""
    
    __tablename__ = "point_cloud_patches"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    patch = Column(String)  # PCPATCH type - stored as string (PostGIS specific type)
    envelope = Column(Geometry("POLYGON", srid=4326), nullable=True)
    patch_index = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    room = relationship("Room", back_populates="point_cloud_patches")
    
    def __repr__(self) -> str:
        return f"<PointCloudPatch(id={self.id}, room_id={self.room_id})>"


class DetectedObject(Base):
    """Detected object model - furniture/object detection results."""
    
    __tablename__ = "detected_objects"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    object_type = Column(String(50))
    position = Column(Geometry("POINTZ", srid=4326), nullable=True)
    dimensions = Column(JSONB)  # {length, width, height} in meters
    volume = Column(Float)  # cubic meters
    confidence = Column(Float)  # 0-1 classification confidence
    classification_method = Column(String(20))  # "geometric" or "ml"
    metadata = Column(JSONB, default={})
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    room = relationship("Room", back_populates="detected_objects")
    
    def __repr__(self) -> str:
        return f"<DetectedObject(id={self.id}, type='{self.object_type}', room_id={self.room_id})>"
