"""Core algorithms for point cloud processing.

Reference: Section B1 - RANSAC plane detection and DBSCAN clustering.
Implements exact parameters from knowledge document.
"""
import open3d as o3d
import numpy as np
import logging
from typing import List, Tuple, Dict, Any

from backend.config import settings

logger = logging.getLogger(__name__)


def detect_planes(
    pcd: o3d.geometry.PointCloud,
    max_planes: int = 5
) -> Tuple[List[np.ndarray], List[np.ndarray]]:
    """Detect planes using RANSAC algorithm.
    
    Reference: Section B1 - RANSAC plane detection with exact parameters:
    - distance_threshold: 0.01 (1cm tolerance)
    - ransac_n: 3 (minimum points for plane)
    - num_iterations: 1000
    
    Performance target: 5-15 seconds for 3M points (Section F2).
    
    Args:
        pcd: Point cloud to detect planes in
        max_planes: Maximum number of planes to detect
        
    Returns:
        Tuple of (plane_models, inlier_indices_list):
        - plane_models: List of plane equations [a, b, c, d] where ax+by+cz+d=0
        - inlier_indices_list: List of inlier index arrays for each plane
    """
    logger.info(f"Detecting up to {max_planes} planes using RANSAC...")
    
    plane_models = []
    inlier_indices_list = []
    current_pcd = pcd
    
    for i in range(max_planes):
        if len(current_pcd.points) < 3:
            logger.debug(f"Not enough points for plane detection: {len(current_pcd.points)}")
            break
        
        # Adaptive minimum inlier threshold: 1% of remaining points, but at least 500
        min_inliers = max(500, int(len(current_pcd.points) * 0.01))
        
        # Section B1: RANSAC parameters
        plane_model, inliers = current_pcd.segment_plane(
            distance_threshold=settings.ransac_distance_threshold,  # 0.01m = 1cm
            ransac_n=3,  # Minimum points for plane
            num_iterations=settings.ransac_iterations  # 1000 iterations
        )
        
        # Check if we found a significant plane (adaptive minimum based on point count)
        if len(inliers) < min_inliers:
            logger.debug(f"Plane {i+1}: Insufficient inliers ({len(inliers)} < {min_inliers} minimum)")
            break
        
        plane_models.append(plane_model)
        inlier_indices_list.append(inliers)
        
        logger.info(f"Plane {i+1}: {len(inliers)} inliers, equation: {plane_model}")
        
        # Remove detected plane points for next iteration
        if len(inliers) < len(current_pcd.points):
            current_pcd = current_pcd.select_by_index(inliers, invert=True)
        else:
            break
    
    logger.info(f"Detected {len(plane_models)} planes")
    return plane_models, inlier_indices_list


def cluster_objects(
    pcd: o3d.geometry.PointCloud
) -> Tuple[np.ndarray, int, Dict[str, Any]]:
    """Cluster objects using DBSCAN algorithm with adaptive parameters.
    
    Reference: Section B1 - DBSCAN clustering with adaptive parameters:
    - Base eps: 0.1 (10cm neighborhood radius - room scale)
    - Base min_samples: 50 (minimum cluster size)
    - Parameters adapt based on point cloud density and size
    
    Tuning strategy:
    - eps scales with voxel size (typically 2-3x voxel size)
    - min_points adapts to point cloud size (10-30% of points for small clouds)
    
    Complexity: O(n log n) with spatial indexing.
    
    Args:
        pcd: Point cloud to cluster
        
    Returns:
        Tuple of (labels, max_label, statistics):
        - labels: Array of cluster labels for each point (-1 for noise)
        - max_label: Maximum cluster label
        - statistics: Dictionary with cluster statistics
    """
    logger.info(f"Clustering objects using DBSCAN...")
    
    point_count = len(pcd.points)
    
    # Minimum threshold: need at least 10 points for clustering
    if point_count < 10:
        logger.warning(f"Not enough points for DBSCAN clustering: {point_count}")
        return np.array([]), -1, {}
    
    # Adaptive parameter calculation
    # eps: 2-3x voxel size, but not less than 0.05m or more than 0.15m
    base_eps = settings.dbscan_eps  # 0.1m default
    voxel_ratio = 2.5  # eps should be ~2.5x voxel size for good connectivity
    adaptive_eps = max(0.05, min(0.15, settings.voxel_size * voxel_ratio))
    # Use the larger of base_eps and adaptive_eps for better detection
    eps = max(base_eps, adaptive_eps)
    
    # min_points: adapt based on point cloud size
    # For small clouds (< 200 points): use 20-30% of points
    # For medium clouds (200-1000): use 10-20% of points  
    # For large clouds (> 1000): use base min_samples (50)
    if point_count < 200:
        min_points = max(10, int(point_count * 0.25))  # 25% of points, min 10
    elif point_count < 1000:
        min_points = max(20, int(point_count * 0.15))  # 15% of points, min 20
    else:
        min_points = settings.dbscan_min_samples  # Default 50 for large clouds
    
    # Ensure min_points doesn't exceed point_count
    min_points = min(min_points, max(10, point_count - 5))
    
    logger.info(
        f"DBSCAN parameters: eps={eps:.3f}m, min_points={min_points} "
        f"(point_count={point_count}, voxel_size={settings.voxel_size}m)"
    )
    
    # Run DBSCAN clustering
    labels = np.array(pcd.cluster_dbscan(
        eps=eps,
        min_points=min_points
    ))
    
    max_label = labels.max()
    num_clusters = max_label + 1
    noise_points = int(np.sum(labels == -1))
    
    logger.info(
        f"DBSCAN clustering complete: {num_clusters} clusters "
        f"(noise: {noise_points} points, {noise_points/point_count*100:.1f}%)"
    )
    
    # Calculate cluster statistics
    cluster_stats = {
        "total_points": len(labels),
        "num_clusters": num_clusters,
        "noise_points": noise_points,
        "noise_ratio": noise_points / point_count if point_count > 0 else 0.0,
        "eps_used": eps,
        "min_points_used": min_points,
        "cluster_sizes": {}
    }
    
    for i in range(num_clusters):
        cluster_size = np.sum(labels == i)
        cluster_stats["cluster_sizes"][i] = int(cluster_size)
    
    return labels, max_label, cluster_stats


def reconstruct_mesh(
    pcd: o3d.geometry.PointCloud,
    depth: int = 9
) -> Tuple[o3d.geometry.TriangleMesh, np.ndarray]:
    """Reconstruct mesh from point cloud using Poisson surface reconstruction.
    
    Reference: Section B2 - Poisson reconstruction with parameters:
    - depth: 8-10 (room scale), default 9
    - scale: 1.1 (cube ratio to bounding box)
    - samples_per_node: 1.5 (smoothness vs detail)
    
    This is an optional advanced feature.
    
    Args:
        pcd: Point cloud with normals
        depth: Octree depth (resolution = 2^depth)
        
    Returns:
        Tuple of (mesh, densities):
        - mesh: Reconstructed triangle mesh
        - densities: Point densities for filtering
    """
    logger.info(f"Reconstructing mesh using Poisson surface reconstruction (depth={depth})...")
    
    if not pcd.has_normals():
        logger.warning("Point cloud lacks normals. Estimating normals for reconstruction...")
        pcd.estimate_normals(
            search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30)
        )
    
    # Section B2: Poisson reconstruction parameters
    mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
        pcd,
        depth=depth,  # Octree resolution = 2^9 = 512
        width=0,  # Automatic width
        scale=1.1,  # Cube ratio to bounding box
        linear_fit=False,
        samples_per_node=1.5  # Smoothness vs detail
    )
    
    # Remove low-density vertices (Section B2 optimization)
    vertices_to_remove = densities < np.quantile(densities, 0.01)
    mesh.remove_vertices_by_mask(vertices_to_remove)
    
    logger.info(f"Mesh reconstruction complete: {len(mesh.vertices)} vertices, {len(mesh.triangles)} triangles")
    return mesh, densities
