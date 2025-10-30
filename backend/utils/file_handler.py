"""
Async file upload and temporary file management.

Handles file uploads using aiofiles for async I/O, temporary file management,
and cleanup on error. Supports PLY file format validation.
"""
import aiofiles
import tempfile
import os
import time
from pathlib import Path
from typing import Optional
import logging

from backend.config import settings

logger = logging.getLogger(__name__)


async def save_uploaded_file(
    file_content: bytes,
    filename: str,
    upload_dir: Optional[str] = None
) -> str:
    """
    Save uploaded file to disk asynchronously.
    
    Args:
        file_content: File content as bytes
        filename: Original filename
        upload_dir: Upload directory (defaults to settings.upload_directory)
        
    Returns:
        str: Path to saved file
        
    Raises:
        OSError: If directory creation or file write fails
    """
    upload_dir = upload_dir or settings.upload_directory
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, filename)
    
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(file_content)
    
    logger.info(f"Saved uploaded file: {file_path}")
    return file_path


async def save_temp_file(file_content: bytes, suffix: str = ".ply") -> str:
    """
    Save file to temporary directory.
    
    Args:
        file_content: File content as bytes
        suffix: File suffix (default: .ply)
        
    Returns:
        str: Path to temporary file
    """
    temp_dir = settings.temp_directory
    os.makedirs(temp_dir, exist_ok=True)
    
    # Create named temporary file
    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
        dir=temp_dir
    ) as tmp_file:
        tmp_file.write(file_content)
        temp_path = tmp_file.name
    
    logger.debug(f"Created temporary file: {temp_path}")
    return temp_path


async def read_file_async(file_path: str) -> bytes:
    """
    Read file asynchronously.
    
    Args:
        file_path: Path to file
        
    Returns:
        bytes: File content
    """
    async with aiofiles.open(file_path, 'rb') as f:
        content = await f.read()
    return content


def cleanup_file(file_path: str) -> None:
    """
    Delete a file if it exists.
    
    Args:
        file_path: Path to file to delete
    """
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
            logger.debug(f"Cleaned up file: {file_path}")
    except OSError as e:
        logger.warning(f"Failed to cleanup file {file_path}: {e}")


def cleanup_temp_directory(temp_dir: Optional[str] = None, age_hours: int = 24) -> None:
    """
    Clean up old temporary files.
    
    Args:
        temp_dir: Temporary directory (defaults to settings.temp_directory)
        age_hours: Delete files older than this many hours
    """
    temp_dir = temp_dir or settings.temp_directory
    
    if not os.path.exists(temp_dir):
        return
    
    import time
    current_time = time.time()
    age_seconds = age_hours * 3600
    
    deleted_count = 0
    for filename in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, filename)
        try:
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > age_seconds:
                    os.unlink(file_path)
                    deleted_count += 1
        except OSError as e:
            logger.warning(f"Failed to delete old temp file {file_path}: {e}")
    
    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} old temporary files")


def validate_file_size(file_size: int, max_size: Optional[int] = None) -> bool:
    """
    Validate file size against maximum allowed size.
    
    Args:
        file_size: File size in bytes
        max_size: Maximum allowed size in bytes (defaults to settings.max_upload_size)
        
    Returns:
        bool: True if file size is valid
    """
    max_size = max_size or settings.max_upload_size
    return file_size <= max_size

