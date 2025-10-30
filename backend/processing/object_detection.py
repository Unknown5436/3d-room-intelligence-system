"""Object detection and classification module.

Reference: Section D2 - Object detection with 70-85% geometric accuracy.
Uses DBSCAN clustering + geometric feature extraction + heuristic classification.
"""
import open3d as o3d
import numpy as np
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


def extract_geometric_features(
    cluster_pcd: o3d.geometry.PointCloud
) -> Dict[str, float]:
    """Extract geometric features from a point cloud cluster.
    
    Features: height, aspect_ratio, volume, surface_area, bounding box dimensions.
    
    Args:
        cluster_pcd: Point cloud cluster representing an object
        
    Returns:
        Dictionary with geometric features
    """
    bbox = cluster_pcd.get_axis_aligned_bounding_box()
    
    # Get dimensions (extent gives length, width, height)
    dimensions = bbox.get_extent()  # [length, width, height]
    center = bbox.get_center()
    
    length, width, height = dimensions[0], dimensions[1], dimensions[2]
    
    # Calculate volume
    volume = length * width * height
    
    # Calculate aspect ratios
    aspect_ratio_xy = length / width if width > 0 else 0
    aspect_ratio_xz = length / height if height > 0 else 0
    aspect_ratio_yz = width / height if height > 0 else 0
    
    # Calculate surface area approximation
    # For rectangular box: 2*(l*w + l*h + w*h)
    surface_area = 2 * (length * width + length * height + width * height)
    
    return {
        "length": float(length),
        "width": float(width),
        "height": float(height),
        "volume": float(volume),
        "aspect_ratio_xy": float(aspect_ratio_xy),
        "aspect_ratio_xz": float(aspect_ratio_xz),
        "aspect_ratio_yz": float(aspect_ratio_yz),
        "surface_area": float(surface_area),
        "center": center.tolist(),
    }


def classify_by_geometry(
    dims: Dict[str, float],
    volume: float,
    aspect_ratio: float,
    height: float
) -> Tuple[str, float]:
    """Classify object by geometric heuristics.
    
    Reference: Section D2 - Geometric classification rules:
    - Tables: 0.6-0.8m height, aspect_ratio > 0.5
    - Chairs: 0.4-0.5m height, volume < 0.3m³
    - Desks: 0.7-0.8m height, aspect_ratio > 1.2
    - Beds: 0.4-0.6m height, volume > 2.0m³
    - Sofas: 0.7-0.9m height, length > 1.5m
    - Cabinets: height > 1.2m, volume > 0.5m³
    
    Accuracy: 70-85% geometric accuracy per Section D2.
    
    Args:
        dims: Dimensions dictionary {length, width, height}
        volume: Volume in cubic meters
        aspect_ratio: Aspect ratio (length/width)
        height: Height in meters
        
    Returns:
        Tuple of (object_type, confidence)
    """
    length = dims.get("length", 0)
    width = dims.get("width", 0)
    
    # Table detection: 0.6-0.8m height, aspect_ratio > 0.5
    if 0.6 <= height <= 0.8 and aspect_ratio > 0.5:
        return "table", 0.75
    
    # Chair detection: 0.4-0.5m height, volume < 0.3m³
    if 0.4 <= height <= 0.5 and volume < 0.3:
        return "chair", 0.70
    
    # Desk detection: 0.7-0.8m height, aspect_ratio > 1.2
    if 0.7 <= height <= 0.8 and aspect_ratio > 1.2:
        return "desk", 0.72
    
    # Bed detection: 0.4-0.6m height, volume > 2.0m³
    if 0.4 <= height <= 0.6 and volume > 2.0:
        return "bed", 0.80
    
    # Sofa detection: 0.7-0.9m height, length > 1.5m
    if 0.7 <= height <= 0.9 and length > 1.5:
        return "sofa", 0.75
    
    # Cabinet detection: height > 1.2m, volume > 0.5m³
    if height > 1.2 and volume > 0.5:
        return "cabinet", 0.68
    
    # Bookshelf: tall and narrow
    if height > 1.5 and aspect_ratio < 0.3:
        return "bookshelf", 0.65
    
    # Unknown
    return "unknown", 0.0


def classify_objects(
    pcd: o3d.geometry.PointCloud,
    labels: np.ndarray,
    min_cluster_size: int = 50
) -> List[Dict[str, Any]]:
    """Classify objects from DBSCAN cluster labels.
    
    Process each cluster, extract geometric features, and classify.
    
    Args:
        pcd: Point cloud with clusters
        labels: DBSCAN cluster labels array (-1 for noise)
        min_cluster_size: Minimum cluster size to classify
        
    Returns:
        List of object dictionaries with type, position, dimensions, volume, confidence
    """
    logger.info(f"Classifying objects from {labels.max() + 1} clusters...")
    
    objects = []
    max_label = labels.max()
    
    if max_label < 0:
        logger.warning("No clusters found for classification")
        return objects
    
    for i in range(max_label + 1):
        cluster_indices = np.where(labels == i)[0]
        
        # Skip small clusters
        if len(cluster_indices) < min_cluster_size:
            continue
        
        # Extract cluster point cloud
        cluster_pcd = pcd.select_by_index(cluster_indices)
        
        # Extract geometric features
        features = extract_geometric_features(cluster_pcd)
        
        # Classify by geometry
        aspect_ratio = features["aspect_ratio_xy"]
        obj_type, confidence = classify_by_geometry(
            {
                "length": features["length"],
                "width": features["width"],
                "height": features["height"]
            },
            features["volume"],
            aspect_ratio,
            features["height"]
        )
        
        # Skip unknown objects with very low confidence
        if obj_type == "unknown" and confidence < 0.1:
            continue
        
        objects.append({
            "type": obj_type,
            "position": features["center"],  # [x, y, z]
            "dimensions": [
                features["length"],
                features["width"],
                features["height"]
            ],
            "volume": features["volume"],
            "confidence": confidence,
            "cluster_id": i,
            "point_count": len(cluster_indices),
        })
        
        logger.debug(
            f"Classified cluster {i}: {obj_type} "
            f"(confidence: {confidence:.2f}, points: {len(cluster_indices)})"
        )
    
    logger.info(f"Classified {len(objects)} objects from {max_label + 1} clusters")
    return objects
