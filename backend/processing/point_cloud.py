"""Point cloud loading and preprocessing module.

Reference: Section C1 (Open3D), Section F1 (Preprocessing pipeline).
Implements complete preprocessing: outlier removal, voxel downsampling, normal estimation.
"""
import open3d as o3d
import numpy as np
import logging
from pathlib import Path
from typing import Tuple, Optional

from backend.config import settings

logger = logging.getLogger(__name__)


def load_point_cloud(file_path: str) -> o3d.geometry.PointCloud:
    """Load point cloud from PLY file.
    
    Reference: Section C1 - Open3D point cloud loading.
    Supports PLY format (Phase 1-2: PLY-only, SPZ deferred to Phase 5).
    
    Args:
        file_path: Path to PLY file
        
    Returns:
        PointCloud: Loaded point cloud
        
    Raises:
        ValueError: If file cannot be loaded or format unsupported
    """
    path = Path(file_path)
    
    if not path.exists():
        raise ValueError(f"File does not exist: {file_path}")
    
    if path.suffix.lower() not in [".ply"]:
        # SPZ support deferred to Phase 5
        raise ValueError(f"Unsupported format: {path.suffix}. Only PLY supported in Phase 1-2.")
    
    try:
        logger.info(f"Loading point cloud from: {file_path}")
        pcd = o3d.io.read_point_cloud(str(path))
        
        if len(pcd.points) == 0:
            raise ValueError("Point cloud is empty")
        
        logger.info(f"Loaded {len(pcd.points)} points")
        
        # Warn if point count is low (Section F1: typical room ~1-3M points)
        if len(pcd.points) < 100000:
            logger.warning(f"Low point count: {len(pcd.points)}. Scan may be incomplete.")
        
        return pcd
        
    except Exception as e:
        logger.error(f"Error loading point cloud: {e}")
        raise ValueError(f"Failed to load point cloud: {str(e)}")


def preprocess_point_cloud(pcd: o3d.geometry.PointCloud) -> o3d.geometry.PointCloud:
    """Complete preprocessing pipeline for point cloud.
    
    Reference: Section F1 - Preprocessing operations:
    1. Statistical outlier removal (20 neighbors, 2.0 std ratio)
    2. Voxel downsampling (0.05m voxels)
    3. Normal estimation
    
    Args:
        pcd: Input point cloud
        
    Returns:
        PointCloud: Preprocessed point cloud
    """
    logger.info(f"Preprocessing point cloud with {len(pcd.points)} points")
    original_count = len(pcd.points)
    
    # Step 1: Statistical Outlier Removal
    # Section F1: 20 neighbors, 2.0 std ratio
    logger.debug("Removing statistical outliers...")
    pcd_clean, outlier_indices = pcd.remove_statistical_outlier(
        nb_neighbors=settings.outlier_neighbors,
        std_ratio=settings.outlier_std_ratio
    )
    
    removed_outliers = original_count - len(pcd_clean.points)
    logger.info(f"Removed {removed_outliers} outliers ({removed_outliers/original_count*100:.1f}%)")
    
    # Step 2: Voxel Downsampling
    # Section F1: 0.05m (5cm) voxels
    logger.debug(f"Downsampling with voxel size: {settings.voxel_size}m...")
    pcd_down = pcd_clean.voxel_down_sample(voxel_size=settings.voxel_size)
    
    logger.info(f"Downsampled to {len(pcd_down.points)} points ({(1 - len(pcd_down.points)/len(pcd_clean.points))*100:.1f}% reduction)")
    
    # Step 3: Normal Estimation
    # Required for surface reconstruction and plane detection
    logger.debug("Estimating normals...")
    pcd_down.estimate_normals(
        search_param=o3d.geometry.KDTreeSearchParamHybrid(
            radius=0.1,  # 10cm search radius
            max_nn=30    # Maximum 30 neighbors
        )
    )
    
    logger.info("Normal estimation complete")
    logger.info(f"Preprocessing complete: {original_count} -> {len(pcd_down.points)} points")
    
    return pcd_down


def assess_scan_quality(pcd: o3d.geometry.PointCloud) -> dict:
    """Assess point cloud scan quality.
    
    Reference: Section G2 - Quality metrics for scan validation.
    
    Args:
        pcd: Point cloud to assess
        
    Returns:
        dict: Quality metrics including score, point count, density
    """
    point_count = len(pcd.points)
    
    # Calculate bounding box and volume
    bbox = pcd.get_axis_aligned_bounding_box()
    volume = bbox.volume()
    
    point_density = point_count / volume if volume > 0 else 0
    
    # Quality scoring (0-1)
    quality_score = 0.0
    
    # Point count scoring
    if point_count > 1_000_000:
        quality_score += 0.4
    elif point_count > 500_000:
        quality_score += 0.3
    elif point_count > 100_000:
        quality_score += 0.2
    
    # Density scoring
    if point_density > 50000:
        quality_score += 0.3
    elif point_density > 20000:
        quality_score += 0.2
    
    # Completeness checks
    if pcd.has_normals():
        quality_score += 0.15
    if pcd.has_colors():
        quality_score += 0.15
    
    rating = "excellent" if quality_score > 0.8 else \
             "good" if quality_score > 0.6 else \
             "acceptable" if quality_score > 0.4 else "poor"
    
    return {
        "quality_score": quality_score,
        "point_count": point_count,
        "point_density": point_density,
        "rating": rating,
        "bbox": {
            "min": bbox.min_bound.tolist(),
            "max": bbox.max_bound.tolist(),
        },
        "volume": volume
    }
