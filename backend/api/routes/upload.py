"""File upload routes.

Handles PLY file uploads and triggers point cloud processing.
Reference: Section E1 for upload endpoint specifications.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from pathlib import Path
import time

from backend.database.connection import get_db_session
from backend.database.repositories import RoomRepository, ObjectRepository
from backend.api.models.schemas import UploadResponse
from backend.utils.file_handler import save_temp_file, cleanup_file
from backend.utils.validators import validate_ply_file, validate_filename
from backend.processing.process_room import process_room_scan
from backend.config import settings
import uuid
import numpy as np

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload-scan", response_model=UploadResponse)
async def upload_scan(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session)
):
    """Upload and process PLY/SPZ scan from Scaniverse.
    
    Reference: Section E1 - POST /upload-scan endpoint.
    Accepts PLY files up to 250MB (Section A2).
    
    Args:
        file: Uploaded PLY file
        session: Database session
        
    Returns:
        UploadResponse: Processing status and room_id
    """
    # Validate filename
    is_valid, error = validate_filename(file.filename)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    
    # Check file extension
    if not file.filename.lower().endswith(('.ply', '.spz')):
        raise HTTPException(
            status_code=400,
            detail="Only PLY and SPZ formats supported. Phase 1-2: PLY support only."
        )
    
    # Read file content
    try:
        content = await file.read()
    except Exception as e:
        logger.error(f"Error reading uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Failed to read uploaded file")
    
    # Check file size
    if len(content) > settings.max_upload_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {len(content)} bytes (max: {settings.max_upload_size})"
        )
    
    # Save to temporary file
    temp_file_path = None
    try:
        temp_file_path = await save_temp_file(content, suffix=".ply")
        
        # Validate PLY file format
        is_valid, error = validate_ply_file(str(temp_file_path), settings.max_upload_size)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid PLY file: {error}")
        
        # Process point cloud (complete pipeline)
        logger.info("Processing room scan...")
        # Run in background to avoid blocking event loop
        import asyncio
        room_data = await asyncio.to_thread(process_room_scan, str(temp_file_path))
        
        # Generate unique room ID
        room_id = f"room_{uuid.uuid4().hex[:8]}"
        
        # Convert numpy types to native Python types for JSON serialization
        def convert_numpy_types(obj):
            """Convert numpy types to native Python types for JSON serialization."""
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_numpy_types(item) for item in obj]
            return obj
        
        # Prepare metadata with converted types
        metadata = {
            "processing_time": convert_numpy_types(room_data["processing_time"]),
            "cluster_stats": convert_numpy_types(room_data.get("cluster_stats", {}))
        }
        
        # Store in database
        room_repo = RoomRepository(session)
        room = await room_repo.create_room(
            room_id=room_id,
            point_count=int(room_data["point_count"]),
            processed_points=int(room_data["processed_points"]),
            length=float(room_data["dimensions"]["length"]),
            width=float(room_data["dimensions"]["width"]),
            height=float(room_data["dimensions"]["height"]),
            accuracy=room_data["dimensions"]["accuracy"],
            scan_quality=float(room_data["scan_quality"]),
            metadata=metadata
        )
        
        # Store detected objects
        obj_repo = ObjectRepository(session)
        for obj in room_data["objects"]:
            await obj_repo.create_object(
                room_id=room_id,
                object_type=obj["type"],
                position=[float(x) for x in obj["position"]],  # Ensure floats
                dimensions={
                    "length": float(obj["dimensions"][0]),
                    "width": float(obj["dimensions"][1]),
                    "height": float(obj["dimensions"][2])
                },
                volume=float(obj["volume"]),
                confidence=float(obj["confidence"]),
                classification_method="geometric"
            )
        
        # Commit transaction
        await session.commit()
        
        logger.info(f"Room processed and stored: {room_id}, {len(room_data['objects'])} objects detected")
        
        return UploadResponse(
            status="success",
            room_id=room_id,
            message=f"Processed {room_data['point_count']} points, detected {len(room_data['objects'])} objects",
            objects_detected=len(room_data["objects"])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
    finally:
        # Cleanup temporary file
        if temp_file_path:
            cleanup_file(str(temp_file_path))
