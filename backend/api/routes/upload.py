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
        
        # Store in database
        room_repo = RoomRepository(session)
        room = await room_repo.create_room(
            room_id=room_id,
            point_count=room_data["point_count"],
            processed_points=room_data["processed_points"],
            length=room_data["dimensions"]["length"],
            width=room_data["dimensions"]["width"],
            height=room_data["dimensions"]["height"],
            accuracy=room_data["dimensions"]["accuracy"],
            scan_quality=room_data["scan_quality"],
            metadata={
                "processing_time": room_data["processing_time"],
                "cluster_stats": room_data.get("cluster_stats", {})
            }
        )
        
        # Store detected objects
        obj_repo = ObjectRepository(session)
        for obj in room_data["objects"]:
            await obj_repo.create_object(
                room_id=room_id,
                object_type=obj["type"],
                position=obj["position"],
                dimensions={
                    "length": obj["dimensions"][0],
                    "width": obj["dimensions"][1],
                    "height": obj["dimensions"][2]
                },
                volume=obj["volume"],
                confidence=obj["confidence"],
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
