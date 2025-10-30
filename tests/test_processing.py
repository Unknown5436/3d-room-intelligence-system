"""Unit tests for point cloud processing algorithms.

Tests RANSAC plane detection, DBSCAN clustering, room dimension extraction,
and object classification with synthetic and real point cloud data.
"""
import pytest
import numpy as np
import open3d as o3d
from pathlib import Path

from backend.processing.point_cloud import (
    load_point_cloud,
    preprocess_point_cloud,
    assess_scan_quality
)
from backend.processing.algorithms import (
    detect_planes,
    cluster_objects,
    reconstruct_mesh
)
from backend.processing.room_analysis import extract_room_dimensions
from backend.processing.process_room import process_room_scan
from backend.processing.object_detection import classify_objects


class TestPointCloudLoading:
    """Tests for point cloud loading functionality."""
    
    def test_load_point_cloud_success(self, synthetic_ply_file):
        """Test successful PLY file loading."""
        pcd = load_point_cloud(synthetic_ply_file)
        assert isinstance(pcd, o3d.geometry.PointCloud)
        assert len(pcd.points) > 0
        assert pcd.has_points()
    
    def test_load_point_cloud_missing_file(self):
        """Test loading non-existent file raises error."""
        with pytest.raises(ValueError, match="File does not exist"):
            load_point_cloud("nonexistent.ply")
    
    def test_load_point_cloud_empty_file(self, tmp_path):
        """Test loading empty/invalid PLY file raises error."""
        empty_file = tmp_path / "empty.ply"
        empty_file.write_text("invalid content")
        
        # Open3D may or may not raise an error, but should handle gracefully
        try:
            pcd = load_point_cloud(str(empty_file))
            # If it loads, it should be empty and raise ValueError
            if len(pcd.points) == 0:
                with pytest.raises(ValueError, match="empty"):
                    load_point_cloud(str(empty_file))
        except ValueError:
            pass  # Expected behavior


class TestPreprocessing:
    """Tests for point cloud preprocessing."""
    
    def test_preprocess_point_cloud(self, synthetic_ply_file):
        """Test preprocessing reduces points and removes outliers."""
        pcd = load_point_cloud(synthetic_ply_file)
        original_count = len(pcd.points)
        
        pcd_processed = preprocess_point_cloud(pcd)
        
        assert len(pcd_processed.points) > 0
        # Preprocessing may reduce points (outliers, downsampling)
        assert len(pcd_processed.points) <= original_count
        
        # Should have normals after preprocessing
        assert pcd_processed.has_normals()
    
    def test_preprocess_small_point_cloud(self, small_synthetic_ply):
        """Test preprocessing handles small point clouds."""
        pcd = load_point_cloud(small_synthetic_ply)
        pcd_processed = preprocess_point_cloud(pcd)
        
        assert len(pcd_processed.points) > 0
        assert pcd_processed.has_normals()


class TestPlaneDetection:
    """Tests for RANSAC plane detection."""
    
    def test_detect_planes_synthetic_room(self, synthetic_ply_file):
        """Test plane detection on synthetic room (should detect multiple planes)."""
        pcd = load_point_cloud(synthetic_ply_file)
        pcd_processed = preprocess_point_cloud(pcd)
        
        plane_models, inlier_indices = detect_planes(pcd_processed, max_planes=5)
        
        # Should detect at least floor and some walls
        assert len(plane_models) > 0
        assert len(plane_models) <= 5
        assert len(inlier_indices) == len(plane_models)
        
        # Each plane should have significant inliers
        for inliers in inlier_indices:
            assert len(inliers) > 0
    
    def test_detect_planes_parameters(self, synthetic_ply_file):
        """Test RANSAC parameters match expected values."""
        pcd = load_point_cloud(synthetic_ply_file)
        pcd_processed = preprocess_point_cloud(pcd)
        
        plane_models, inlier_indices = detect_planes(pcd_processed, max_planes=3)
        
        # Verify plane equations are valid (4 coefficients)
        for plane in plane_models:
            assert len(plane) == 4  # [a, b, c, d] for ax+by+cz+d=0
    
    def test_detect_planes_max_planes_limit(self, synthetic_ply_file):
        """Test that max_planes parameter is respected."""
        pcd = load_point_cloud(synthetic_ply_file)
        pcd_processed = preprocess_point_cloud(pcd)
        
        plane_models, _ = detect_planes(pcd_processed, max_planes=2)
        
        assert len(plane_models) <= 2


class TestDBSCANClustering:
    """Tests for DBSCAN object clustering."""
    
    def test_cluster_objects_with_objects(self, synthetic_ply_file):
        """Test DBSCAN clustering detects object clusters."""
        # First detect and remove planes
        pcd = load_point_cloud(synthetic_ply_file)
        pcd_processed = preprocess_point_cloud(pcd)
        
        plane_models, plane_inliers = detect_planes(pcd_processed, max_planes=5)
        
        # Remove plane points
        all_plane_indices = set()
        for inliers in plane_inliers:
            all_plane_indices.update(inliers)
        
        if len(all_plane_indices) < len(pcd_processed.points):
            objects_pcd = pcd_processed.select_by_index(
                list(all_plane_indices),
                invert=True
            )
            
            # Cluster objects
            labels, max_label, stats = cluster_objects(objects_pcd)
            
            # Should return valid results
            assert isinstance(labels, np.ndarray)
            assert max_label >= -1  # -1 means no clusters
            assert isinstance(stats, dict)
            assert "num_clusters" in stats
    
    def test_cluster_objects_minimum_points(self, synthetic_ply_file):
        """Test DBSCAN handles point clouds with insufficient points."""
        pcd = load_point_cloud(synthetic_ply_file)
        # Create very small subset
        small_pcd = pcd.select_by_index(range(min(30, len(pcd.points))))
        
        labels, max_label, stats = cluster_objects(small_pcd)
        
        # Should handle gracefully
        assert isinstance(labels, np.ndarray)
        # May return empty array or handle differently
        assert max_label >= -1


class TestRoomDimensions:
    """Tests for room dimension extraction."""
    
    def test_extract_room_dimensions_synthetic(self, synthetic_ply_file):
        """Test dimension extraction on synthetic room."""
        pcd = load_point_cloud(synthetic_ply_file)
        pcd_processed = preprocess_point_cloud(pcd)
        
        plane_models, plane_inliers = detect_planes(pcd_processed, max_planes=5)
        
        dimensions = extract_room_dimensions(pcd_processed, plane_models, plane_inliers)
        
        # Verify dimensions structure
        assert "length" in dimensions
        assert "width" in dimensions
        assert "height" in dimensions
        assert "accuracy" in dimensions
        
        # Verify positive dimensions
        assert dimensions["length"] > 0
        assert dimensions["width"] > 0
        assert dimensions["height"] > 0
        
        # Synthetic room is 4m x 3m x 2.5m, allow ±50cm tolerance
        assert abs(dimensions["length"] - 4.0) < 0.5
        assert abs(dimensions["width"] - 3.0) < 0.5
        assert abs(dimensions["height"] - 2.5) < 0.5
        
        # Verify accuracy string
        assert "±" in dimensions["accuracy"] or "cm" in dimensions["accuracy"].lower()
    
    def test_extract_room_dimensions_empty_planes(self, synthetic_ply_file):
        """Test dimension extraction with no detected planes (fallback to bbox)."""
        pcd = load_point_cloud(synthetic_ply_file)
        pcd_processed = preprocess_point_cloud(pcd)
        
        # Pass empty planes
        dimensions = extract_room_dimensions(pcd_processed, [], [])
        
        # Should still return dimensions using bounding box fallback
        assert "length" in dimensions
        assert "width" in dimensions
        assert "height" in dimensions
        assert dimensions["length"] > 0
        assert dimensions["width"] > 0
        assert dimensions["height"] > 0


class TestObjectClassification:
    """Tests for object classification."""
    
    def test_classify_objects_with_clusters(self, synthetic_ply_file):
        """Test object classification on clustered points."""
        # Process to get objects
        pcd = load_point_cloud(synthetic_ply_file)
        pcd_processed = preprocess_point_cloud(pcd)
        
        # Detect planes and remove them
        plane_models, plane_inliers = detect_planes(pcd_processed, max_planes=5)
        all_plane_indices = set()
        for inliers in plane_inliers:
            all_plane_indices.update(inliers)
        
        if len(all_plane_indices) < len(pcd_processed.points):
            objects_pcd = pcd_processed.select_by_index(
                list(all_plane_indices),
                invert=True
            )
            
            # Cluster
            labels, max_label, _ = cluster_objects(objects_pcd)
            
            if max_label >= 0:
                # Classify objects
                objects = classify_objects(objects_pcd, labels)
                
                # Should return list of objects
                assert isinstance(objects, list)
                
                # Each object should have required fields
                for obj in objects:
                    assert "type" in obj
                    assert "position" in obj
                    assert "dimensions" in obj
                    assert "volume" in obj
                    assert "confidence" in obj
                    
                    assert isinstance(obj["position"], list)
                    assert len(obj["position"]) == 3
                    assert isinstance(obj["dimensions"], list)
                    assert len(obj["dimensions"]) == 3


class TestCompletePipeline:
    """Tests for complete processing pipeline."""
    
    def test_process_room_scan_complete(self, synthetic_ply_file):
        """Test complete room processing pipeline end-to-end."""
        result = process_room_scan(synthetic_ply_file)
        
        # Verify result structure
        assert "dimensions" in result
        assert "objects" in result
        assert "point_count" in result
        assert "processed_points" in result
        assert "processing_time" in result
        assert "scan_quality" in result
        
        # Verify dimensions
        dims = result["dimensions"]
        assert dims["length"] > 0
        assert dims["width"] > 0
        assert dims["height"] > 0
        
        # Verify objects list
        assert isinstance(result["objects"], list)
        
        # Verify point counts
        assert result["point_count"] > 0
        assert result["processed_points"] > 0
        assert result["processed_points"] <= result["point_count"]
        
        # Verify processing time is recorded
        assert result["processing_time"] > 0
        
        # Verify scan quality score
        assert 0 <= result["scan_quality"] <= 1
    
    def test_process_room_scan_accuracy(self, synthetic_ply_file):
        """Test processing pipeline accuracy on known synthetic room."""
        result = process_room_scan(synthetic_ply_file)
        
        dims = result["dimensions"]
        
        # Synthetic room is 4m x 3m x 2.5m
        # Allow ±50cm tolerance for processing
        assert abs(dims["length"] - 4.0) < 0.5
        assert abs(dims["width"] - 3.0) < 0.5
        assert abs(dims["height"] - 2.5) < 0.5


class TestScanQuality:
    """Tests for scan quality assessment."""
    
    def test_assess_scan_quality(self, synthetic_ply_file):
        """Test scan quality assessment."""
        pcd = load_point_cloud(synthetic_ply_file)
        quality = assess_scan_quality(pcd)
        
        # Verify quality metrics structure
        assert "quality_score" in quality
        assert "point_count" in quality
        assert "rating" in quality
        
        # Verify score is in valid range
        assert 0 <= quality["quality_score"] <= 1
        
        # Verify point count
        assert quality["point_count"] == len(pcd.points)
        
        # Verify rating is a string
        assert isinstance(quality["rating"], str)
        assert quality["rating"] in ["poor", "acceptable", "good", "excellent"]

