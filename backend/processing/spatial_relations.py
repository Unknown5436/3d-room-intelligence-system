"""Spatial relationship analysis module.

Reference: Section D3 - KDTree-based proximity analysis + constraint validation.
Analyzes relationships between detected objects (adjacency, containment, clearance).
"""
import numpy as np
from scipy.spatial import KDTree
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


def calculate_spatial_relationships(
    objects: List[Dict[str, Any]],
    distance_threshold: float = 1.0
) -> List[Dict[str, Any]]:
    """Calculate spatial relationships between objects.
    
    Reference: Section D3 - KDTree-based proximity analysis.
    Detects: adjacency, containment, clearance, accessibility.
    
    Args:
        objects: List of object dictionaries with position [x, y, z]
        distance_threshold: Distance threshold for proximity (meters)
        
    Returns:
        List of relationship dictionaries with object pairs, distances, and types
    """
    logger.info(f"Calculating spatial relationships for {len(objects)} objects...")
    
    if len(objects) < 2:
        logger.debug("Insufficient objects for relationship analysis")
        return []
    
    relationships = []
    
    # Extract positions for KDTree
    positions = np.array([obj["position"] for obj in objects])
    
    # Build KDTree for efficient spatial queries
    kdtree = KDTree(positions)
    
    # Find relationships for each object
    for i, obj in enumerate(objects):
        position = np.array(obj["position"])
        
        # Find nearby objects within threshold
        nearby_indices = kdtree.query_ball_point(position, r=distance_threshold)
        
        # Remove self
        nearby_indices = [idx for idx in nearby_indices if idx != i]
        
        for j in nearby_indices:
            other_obj = objects[j]
            other_position = np.array(other_obj["position"])
            
            # Calculate 3D distance
            distance = np.linalg.norm(position - other_position)
            
            # Determine relationship type
            relationship_type = "nearby"
            if distance < 0.5:  # Within 50cm
                relationship_type = "adjacent"
            elif distance < 0.2:  # Very close
                relationship_type = "touching"
            
            relationships.append({
                "object1_id": i,
                "object1_type": obj["type"],
                "object2_id": j,
                "object2_type": other_obj["type"],
                "distance": float(distance),
                "relationship": relationship_type
            })
    
    logger.info(f"Found {len(relationships)} spatial relationships")
    return relationships


def calculate_clearance(
    obj1: Dict[str, Any],
    obj2: Dict[str, Any]
) -> float:
    """Calculate clearance (minimum distance) between two objects.
    
    Accounts for object dimensions, not just center-to-center distance.
    
    Args:
        obj1: First object with position and dimensions
        obj2: Second object with position and dimensions
        
    Returns:
        Clearance distance in meters
    """
    pos1 = np.array(obj1["position"])
    pos2 = np.array(obj2["position"])
    
    # Center-to-center distance
    center_distance = np.linalg.norm(pos1 - pos2)
    
    # Approximate object sizes (half-dimensions from centers)
    # Rough approximation: use largest dimension as radius
    size1 = max(obj1.get("dimensions", [0, 0, 0])) / 2
    size2 = max(obj2.get("dimensions", [0, 0, 0])) / 2
    
    # Clearance = center distance - object radii
    clearance = center_distance - size1 - size2
    
    return max(0, clearance)  # No negative clearance


def find_accessibility_paths(
    objects: List[Dict[str, Any]],
    room_dimensions: Dict[str, float]
) -> Dict[str, Any]:
    """Analyze accessibility and movement paths in room.
    
    Identifies potential walkways and accessibility constraints.
    
    Args:
        objects: List of detected objects
        room_dimensions: Room dimensions {length, width, height}
        
    Returns:
        Dictionary with accessibility analysis results
    """
    logger.info("Analyzing accessibility paths...")
    
    # Simple analysis: check for clear pathways
    # More sophisticated: pathfinding algorithms could be added
    
    min_pathway_width = 0.6  # Minimum 60cm for accessibility
    
    # Grid-based analysis of floor space
    # Simplified approach - real implementation could use A* pathfinding
    
    clear_areas = []
    blocked_areas = []
    
    # Check if objects create major obstructions
    total_floor_area = room_dimensions.get("length", 4.0) * room_dimensions.get("width", 3.0)
    occupied_area = sum(obj.get("volume", 0) / obj.get("dimensions", [1, 1, 1])[2] for obj in objects)
    
    free_space_ratio = 1.0 - (occupied_area / total_floor_area) if total_floor_area > 0 else 1.0
    
    accessibility = {
        "free_space_ratio": float(free_space_ratio),
        "min_pathway_width": min_pathway_width,
        "has_clear_pathways": free_space_ratio > 0.3,
        "clear_areas": clear_areas,
        "blocked_areas": blocked_areas
    }
    
    logger.info(f"Accessibility analysis: {free_space_ratio*100:.1f}% free space")
    return accessibility
