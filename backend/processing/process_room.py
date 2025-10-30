"""Main room processing pipeline orchestrator.

Integrates all processing modules into complete end-to-end pipeline.
Reference: Section F1 - Complete workflow pipeline.
"""
import open3d as o3d
import logging
from typing import Dict, Any
import time

from backend.processing.point_cloud import load_point_cloud, preprocess_point_cloud, assess_scan_quality
from backend.processing.algorithms import detect_planes, cluster_objects
from backend.processing.room_analysis import extract_room_dimensions
from backend.processing.object_detection import classify_objects
from backend.processing.spatial_relations import calculate_spatial_relationships

logger = logging.getLogger(__name__)


def process_room_scan(file_path: str) -> Dict[str, Any]:
    """Complete room processing pipeline.
    
    Reference: Section F1 - End-to-End Processing Chain:
    1. Load and preprocess point cloud
    2. RANSAC plane detection (floor, walls, ceiling)
    3. Extract room dimensions
    4. DBSCAN object clustering
    5. Object classification
    6. Spatial relationship analysis
    
    Args:
        file_path: Path to PLY file
        
    Returns:
        Dictionary with room data:
        {
            "dimensions": {length, width, height, accuracy},
            "objects": [{type, position, dimensions, volume, confidence}],
            "relationships": [{object1, object2, distance, relationship}],
            "point_count": int,
            "processed_points": int,
            "scan_quality": float
        }
    """
    start_time = time.time()
    logger.info(f"Starting room processing pipeline for: {file_path}")
    
    try:
        # Stage 1: Load point cloud
        logger.info("Stage 1: Loading point cloud...")
        pcd = load_point_cloud(file_path)
        original_point_count = len(pcd.points)
        
        # Assess scan quality
        quality_metrics = assess_scan_quality(pcd)
        logger.info(f"Scan quality: {quality_metrics['rating']} (score: {quality_metrics['quality_score']:.2f})")
        
        # Stage 2: Preprocessing
        logger.info("Stage 2: Preprocessing point cloud...")
        pcd_processed = preprocess_point_cloud(pcd)
        processed_point_count = len(pcd_processed.points)
        
        # Stage 3: Plane detection (RANSAC)
        logger.info("Stage 3: Detecting planes using RANSAC...")
        plane_models, plane_inliers = detect_planes(pcd_processed, max_planes=5)
        
        if not plane_models:
            logger.warning("No planes detected - room dimensions may be inaccurate")
        
        # Stage 4: Extract room dimensions
        logger.info("Stage 4: Extracting room dimensions...")
        dimensions = extract_room_dimensions(pcd_processed, plane_models, plane_inliers)
        
        # Stage 5: Remove planes from point cloud to isolate objects
        # Combine all plane inliers
        all_plane_indices = set()
        for inliers in plane_inliers:
            all_plane_indices.update(inliers)
        
        # Get remaining points (objects/furniture)
        if len(all_plane_indices) < len(pcd_processed.points):
            objects_pcd = pcd_processed.select_by_index(
                list(all_plane_indices), 
                invert=True
            )
        else:
            objects_pcd = pcd_processed
        
        # Stage 6: Object clustering (DBSCAN)
        logger.info("Stage 6: Clustering objects using DBSCAN...")
        if len(objects_pcd.points) > 50:  # Minimum points for clustering
            labels, max_label, cluster_stats = cluster_objects(objects_pcd)
            
            # Stage 7: Object classification
            logger.info("Stage 7: Classifying objects...")
            objects = classify_objects(objects_pcd, labels)
        else:
            logger.info("Insufficient points for object clustering")
            objects = []
            cluster_stats = {}
        
        # Stage 8: Spatial relationships
        logger.info("Stage 8: Analyzing spatial relationships...")
        relationships = []
        if len(objects) > 1:
            relationships = calculate_spatial_relationships(objects)
        
        processing_time = time.time() - start_time
        logger.info(f"Room processing complete in {processing_time:.2f} seconds")
        
        return {
            "dimensions": dimensions,
            "objects": objects,
            "relationships": relationships,
            "point_count": original_point_count,
            "processed_points": processed_point_count,
            "scan_quality": quality_metrics["quality_score"],
            "processing_time": processing_time,
            "cluster_stats": cluster_stats
        }
        
    except Exception as e:
        logger.error(f"Error in room processing pipeline: {e}", exc_info=True)
        raise

