"""Input validation and sanitization utilities.

Provides validation functions for file uploads, API inputs, and point cloud data.
"""
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def validate_ply_file(file_path: str, max_size: int) -> tuple[bool, Optional[str]]:
    """Validate PLY file format and size.
    
    Args:
        file_path: Path to PLY file
        max_size: Maximum file size in bytes
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    path = Path(file_path)
    
    # Check file exists
    if not path.exists():
        return False, f"File does not exist: {file_path}"
    
    # Check file extension
    if path.suffix.lower() != ".ply":
        return False, f"Invalid file format. Expected .ply, got {path.suffix}"
    
    # Check file size
    file_size = path.stat().st_size
    if file_size > max_size:
        return False, f"File too large: {file_size} bytes (max: {max_size})"
    
    if file_size == 0:
        return False, "File is empty"
    
    # Check PLY file header
    try:
        with open(file_path, "rb") as f:
            header = f.read(100).decode("utf-8", errors="ignore")
            if "ply" not in header.lower():
                return False, "Invalid PLY file header"
    except Exception as e:
        return False, f"Error reading file: {str(e)}"
    
    return True, None


def validate_filename(filename: str) -> tuple[bool, Optional[str]]:
    """Validate uploaded filename for security.
    
    Args:
        filename: Original filename
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not filename:
        return False, "Filename is empty"
    
    # Check for path traversal attempts
    if ".." in filename or "/" in filename or "\\" in filename:
        return False, "Invalid filename: path traversal not allowed"
    
    # Check filename length
    if len(filename) > 255:
        return False, "Filename too long (max 255 characters)"
    
    return True, None


def sanitize_room_id(room_id: str) -> tuple[bool, Optional[str]]:
    """Sanitize and validate room ID.
    
    Args:
        room_id: Room identifier string
        
    Returns:
        Tuple of (is_valid, sanitized_room_id_or_error)
    """
    if not room_id:
        return False, "Room ID cannot be empty"
    
    # Remove whitespace
    sanitized = room_id.strip()
    
    # Check length
    if len(sanitized) > 50:
        return False, "Room ID too long (max 50 characters)"
    
    # Check for valid characters (alphanumeric, underscore, hyphen)
    if not sanitized.replace("_", "").replace("-", "").isalnum():
        return False, "Room ID contains invalid characters"
    
    return True, sanitized


def validate_dimensions(length: float, width: float, height: float) -> tuple[bool, Optional[str]]:
    """Validate room/furniture dimensions.
    
    Args:
        length: Length in meters
        width: Width in meters
        height: Height in meters
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    for name, value in [("length", length), ("width", width), ("height", height)]:
        if value <= 0:
            return False, f"{name} must be positive"
        if value > 100:  # Reasonable maximum
            return False, f"{name} too large (max 100m)"
    
    return True, None
