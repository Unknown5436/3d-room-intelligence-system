"""Pydantic models for API request/response validation.

Reference: Section E1 for API model specifications.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional


class RoomDimensions(BaseModel):
    """Room dimensions model.
    
    Reference: Section D1 - Room dimensional extraction with ±2-5cm accuracy.
    """
    length: float = Field(..., description="Room length in meters", gt=0)
    width: float = Field(..., description="Room width in meters", gt=0)
    height: float = Field(..., description="Room height in meters", gt=0)
    accuracy: str = Field(..., description="Accuracy estimate (e.g., '±2-5cm')")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "length": 4.5,
                "width": 3.2,
                "height": 2.5,
                "accuracy": "±2-5cm"
            }
        }
    )


class SpatialObject(BaseModel):
    """Spatial object model for detected furniture/objects.
    
    Reference: Section D2 - Object detection with 70-85% geometric accuracy.
    """
    type: str = Field(..., description="Furniture type (e.g., 'table', 'chair', 'sofa')")
    position: List[float] = Field(
        ..., 
        description="3D position [x, y, z] in meters",
        min_length=3,
        max_length=3
    )
    dimensions: List[float] = Field(
        ..., 
        description="Dimensions [length, width, height] in meters",
        min_length=3,
        max_length=3
    )
    volume: float = Field(..., description="Volume in cubic meters", ge=0)
    confidence: float = Field(
        ..., 
        description="Classification confidence (0-1)",
        ge=0,
        le=1
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "table",
                "position": [2.0, 1.5, 0.75],
                "dimensions": [1.2, 0.8, 0.75],
                "volume": 0.72,
                "confidence": 0.78
            }
        }
    )


class RoomData(BaseModel):
    """Complete room data model."""
    room_id: str = Field(..., description="Room identifier")
    dimensions: RoomDimensions = Field(..., description="Room dimensions")
    objects: List[SpatialObject] = Field(..., description="Detected objects")
    point_count: int = Field(..., description="Total point count in original scan", ge=0)
    processed_points: int = Field(..., description="Point count after processing", ge=0)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "room_id": "room_001",
                "dimensions": {
                    "length": 4.5,
                    "width": 3.2,
                    "height": 2.5,
                    "accuracy": "±2-5cm"
                },
                "objects": [],
                "point_count": 1500000,
                "processed_points": 800000
            }
        }
    )


class ItemFitCheck(BaseModel):
    """Model for item fit checking request."""
    item_type: str = Field(..., description="Item type (e.g., 'table', 'sofa')")
    dimensions: List[float] = Field(
        ..., 
        description="Item dimensions [length, width, height] in meters",
        min_length=3,
        max_length=3
    )
    preferred_position: Optional[List[float]] = Field(
        None,
        description="Preferred position [x, y, z] in meters (optional)",
        min_length=3,
        max_length=3
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "item_type": "table",
                "dimensions": [1.5, 0.9, 0.75],
                "preferred_position": [2.0, 1.5, 0.0]
            }
        }
    )


class FitResult(BaseModel):
    """Model for item fit checking result."""
    fits: bool = Field(..., description="Whether item fits in room")
    available_positions: List[List[float]] = Field(
        ..., 
        description="List of available positions [x, y, z] where item can be placed"
    )
    constraints: List[str] = Field(..., description="Constraints preventing placement")
    recommendations: List[str] = Field(..., description="Recommendations for placement")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "fits": True,
                "available_positions": [[1.0, 1.0, 0.0], [2.0, 1.5, 0.0]],
                "constraints": [],
                "recommendations": [
                    "Consider placement near walls for stability",
                    "Ensure adequate clearance for movement"
                ]
            }
        }
    )


class UploadResponse(BaseModel):
    """Response model for file upload endpoint."""
    status: str = Field(..., description="Processing status")
    room_id: str = Field(..., description="Unique room identifier")
    message: Optional[str] = Field(None, description="Additional message")
    objects_detected: int = Field(..., description="Number of objects detected", ge=0)


class OptimizationResult(BaseModel):
    """Model for layout optimization result."""
    room_id: str = Field(..., description="Room identifier")
    optimization_suggestions: List[str] = Field(..., description="List of optimization suggestions")
    current_layout_score: float = Field(..., description="Current layout score (0-1)", ge=0, le=1)
    improvement_potential: str = Field(..., description="Improvement potential level")
