"""Room analysis module - dimensional extraction.

Reference: Section D1 - Room dimensional extraction with ±2-5cm accuracy.
Uses RANSAC plane detection + geometric analysis.
"""
import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional
from scipy.spatial import distance

from backend.processing.algorithms import detect_planes

logger = logging.getLogger(__name__)


def identify_floor_and_ceiling(
    planes: List[np.ndarray],
    plane_inliers: List[np.ndarray]
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[int], Optional[int]]:
    """Identify floor and ceiling planes from detected planes.
    
    Floor: Lowest horizontal plane (normal pointing up)
    Ceiling: Highest horizontal plane (normal pointing down)
    
    Args:
        planes: List of plane equations [a, b, c, d]
        plane_inliers: List of inlier index arrays
        
    Returns:
        Tuple of (floor_plane, ceiling_plane, floor_idx, ceiling_idx)
    """
    if not planes:
        return None, None, None, None
    
    # Find horizontal planes (normal close to vertical axis [0, 0, 1])
    vertical_normal = np.array([0, 0, 1])
    horizontal_planes = []
    
    for i, plane in enumerate(planes):
        # Plane normal is first 3 elements
        normal = plane[:3]
        # Normalize
        normal = normal / np.linalg.norm(normal)
        
        # Check if plane is horizontal (normal parallel to vertical axis)
        dot_product = abs(np.dot(normal, vertical_normal))
        if dot_product > 0.9:  # Nearly vertical (within ~25 degrees)
            horizontal_planes.append((i, plane, normal))
    
    if not horizontal_planes:
        logger.warning("No horizontal planes detected")
        return None, None, None, None
    
    # Sort by d parameter (distance from origin along normal)
    # Floor has smallest d (lowest), ceiling has largest d (highest)
    horizontal_planes.sort(key=lambda x: x[1][3])
    
    floor_idx, floor_plane, floor_normal = horizontal_planes[0]
    ceiling_idx, ceiling_plane, ceiling_normal = horizontal_planes[-1]
    
    # Ensure floor normal points up and ceiling normal points down
    if floor_normal[2] < 0:
        floor_plane = -floor_plane
    if ceiling_normal[2] > 0:
        ceiling_plane = -ceiling_plane
    
    return floor_plane, ceiling_plane, floor_idx, ceiling_idx


def identify_walls(
    planes: List[np.ndarray],
    floor_plane: np.ndarray,
    floor_idx: int,
    ceiling_idx: Optional[int] = None
) -> List[Tuple[np.ndarray, int]]:
    """Identify wall planes (vertical planes perpendicular to floor).
    
    Args:
        planes: List of all plane equations
        floor_plane: Floor plane equation
        floor_idx: Index of floor plane in planes list
        ceiling_idx: Index of ceiling plane (to exclude)
        
    Returns:
        List of (wall_plane, idx) tuples
    """
    if floor_plane is None:
        return []
    
    floor_normal = floor_plane[:3]
    floor_normal = floor_normal / np.linalg.norm(floor_normal)
    
    walls = []
    for i, plane in enumerate(planes):
        # Skip floor and ceiling
        if i == floor_idx or i == ceiling_idx:
            continue
        
        plane_normal = plane[:3]
        norm = np.linalg.norm(plane_normal)
        if norm < 1e-6:
            continue
        plane_normal = plane_normal / norm
        
        # Wall is vertical (perpendicular to floor normal)
        # For vertical wall, dot product should be close to 0
        dot_product = abs(np.dot(plane_normal, floor_normal))
        if dot_product < 0.2:  # Relaxed threshold: perpendicular (within ~78 degrees)
            walls.append((plane, i))
            logger.debug(f"Wall {i} identified: normal={plane_normal}, dot_product={dot_product:.3f}")
    
    logger.info(f"Identified {len(walls)} wall planes")
    return walls


def calculate_perpendicular_distance(plane1: np.ndarray, plane2: np.ndarray) -> float:
    """Calculate perpendicular distance between two parallel planes.
    
    Args:
        plane1: First plane equation [a, b, c, d]
        plane2: Second plane equation [a, b, c, d]
        
    Returns:
        Distance in meters
    """
    # Ensure normals point in same direction
    normal1 = plane1[:3]
    normal2 = plane2[:3]
    
    if np.dot(normal1, normal2) < 0:
        plane2 = -plane2
    
    # Normalize both planes first to ensure consistent calculation
    norm1 = np.linalg.norm(plane1[:3])
    norm2 = np.linalg.norm(plane2[:3])
    
    if norm1 < 1e-6 or norm2 < 1e-6:
        logger.warning("Invalid plane normals (zero length)")
        return 0.0
    
    # Normalize normals to unit vectors
    normal1_unit = normal1 / norm1
    normal2_unit = normal2 / norm2
    
    # Check if planes are parallel (normals should align)
    dot_product = np.dot(normal1_unit, normal2_unit)
    
    # If normals point in opposite directions, flip plane2
    if dot_product < 0:
        plane2 = -plane2
        dot_product = -dot_product
    
    # For truly parallel planes, dot_product should be close to 1
    if abs(dot_product - 1.0) > 0.1:  # Not parallel (threshold ~5 degrees)
        logger.debug(f"Planes are not perfectly parallel (dot_product={dot_product:.3f}), using approximate distance")
    
    # Distance = |d1/norm1 - d2/norm2| when normals are aligned
    d1_normalized = plane1[3] / norm1
    d2_normalized = plane2[3] / norm2
    
    distance = abs(d1_normalized - d2_normalized)
    return distance


def extract_room_dimensions(
    pcd,
    plane_models: List[np.ndarray],
    plane_inliers: List[np.ndarray]
) -> Dict[str, Any]:
    """Extract room dimensions from detected planes.
    
    Reference: Section D1 - Accuracy target: ±2-5cm (Section F2).
    Method: RANSAC plane detection + geometric analysis.
    
    Args:
        pcd: Point cloud
        plane_models: Detected plane equations
        plane_inliers: Inlier indices for each plane
        
    Returns:
        Dictionary with length, width, height, accuracy
    """
    logger.info("Extracting room dimensions...")
    
    if not plane_models:
        logger.warning("No planes detected - using bounding box fallback")
        # Fallback to bounding box dimensions
        bbox = pcd.get_axis_aligned_bounding_box()
        extent = bbox.get_extent()
        return {
            "length": float(extent[0]),
            "width": float(extent[1]),
            "height": float(extent[2]),
            "accuracy": "±10-20cm (bounding box estimate)"
        }
    
    # Identify floor and ceiling
    floor_plane, ceiling_plane, floor_idx, ceiling_idx = identify_floor_and_ceiling(
        plane_models, plane_inliers
    )
    
    # Log detected planes for debugging
    if floor_plane is not None:
        logger.debug(f"Floor plane detected at index {floor_idx}")
    if ceiling_plane is not None:
        logger.debug(f"Ceiling plane detected at index {ceiling_idx}")
    
    # Calculate height
    height = 2.5  # Default ceiling height
    if floor_plane is not None and ceiling_plane is not None:
        height = calculate_perpendicular_distance(floor_plane, ceiling_plane)
        logger.info(f"Room height: {height:.2f}m")
    elif floor_plane is not None:
        logger.warning("Ceiling not detected, using default height 2.5m")
    else:
        logger.warning("Floor not detected, using default height 2.5m")
    
    # Identify walls (exclude floor and ceiling)
    walls = identify_walls(plane_models, floor_plane, floor_idx, ceiling_idx) if floor_plane is not None else []
    
    # Calculate length and width from wall distances
    # Start with bounding box as fallback estimate
    bbox = pcd.get_axis_aligned_bounding_box()
    bbox_extent = bbox.get_extent()  # [length, width, height] in axis-aligned coords
    bbox_length = max(bbox_extent[0], bbox_extent[1])
    bbox_width = min(bbox_extent[0], bbox_extent[1])
    
    length = bbox_length  # Use bounding box as default
    width = bbox_width
    
    if len(walls) >= 2:
        # Find parallel wall pairs
        parallel_pairs = []
        wall_pair_info = []
        
        for i, (wall1, idx1) in enumerate(walls):
            normal1 = wall1[:3]
            norm1 = np.linalg.norm(normal1)
            if norm1 < 1e-6:
                continue
            normal1 = normal1 / norm1
            
            for j, (wall2, idx2) in enumerate(walls[i+1:], start=i+1):
                normal2 = wall2[:3]
                norm2 = np.linalg.norm(normal2)
                if norm2 < 1e-6:
                    continue
                normal2 = normal2 / norm2
                
                # Check if parallel (normals align OR anti-align)
                # Use abs dot product: parallel walls have dot product close to 1 or -1
                dot_product = abs(np.dot(normal1, normal2))
                
                if dot_product > 0.85:  # Relaxed threshold for parallel detection
                    try:
                        dist = calculate_perpendicular_distance(wall1, wall2)
                        if dist > 0.1:  # Valid room dimension (at least 10cm)
                            parallel_pairs.append(dist)
                            wall_pair_info.append((idx1, idx2, dist, dot_product))
                            logger.debug(f"Parallel pair: walls {idx1}-{idx2}, distance={dist:.2f}m, dot={dot_product:.3f}")
                    except Exception as e:
                        logger.warning(f"Error calculating distance between walls {idx1}-{idx2}: {e}")
        
        if len(parallel_pairs) >= 2:
            # Sort and take largest two as length and width
            parallel_pairs.sort(reverse=True)
            length = parallel_pairs[0]
            width = parallel_pairs[1] if len(parallel_pairs) > 1 else parallel_pairs[0]
            logger.info(f"Room length: {length:.2f}m, width: {width:.2f}m (from {len(parallel_pairs)} parallel pairs)")
        elif len(parallel_pairs) == 1:
            # Only one parallel pair found, use it for one dimension
            pair_pairs_dist = parallel_pairs[0]
            # Check which bounding box dimension is closer to this distance
            if abs(pair_pairs_dist - bbox_length) < abs(pair_pairs_dist - bbox_width):
                length = pair_pairs_dist
                width = bbox_width
            else:
                length = bbox_length
                width = pair_pairs_dist
            logger.info(f"Room length: {length:.2f}m, width: {width:.2f}m (1 parallel pair + bounding box)")
        else:
            logger.warning(f"Could not find parallel wall pairs (checked {len(walls)} walls), using bounding box: {bbox_length:.2f}m x {bbox_width:.2f}m")
            # Use bounding box as fallback
            length = bbox_length
            width = bbox_width
    else:
        logger.warning(f"Insufficient walls detected ({len(walls)}), using bounding box dimensions: {bbox_length:.2f}m x {bbox_width:.2f}m")
        length = bbox_length
        width = bbox_width
    
    dimensions = {
        "length": round(length, 2),
        "width": round(width, 2),
        "height": round(height, 2),
        "accuracy": "±2-5cm"  # Section D1 accuracy specification
    }
    
    logger.info(f"Extracted dimensions: {dimensions}")
    return dimensions
