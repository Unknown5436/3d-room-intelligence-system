"""Integration tests for FastAPI endpoints.

Tests all API endpoints including file upload, room data retrieval,
fit checking, and optimization with both valid and invalid inputs.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path
import io


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_check(self, test_client: TestClient):
        """Test health check endpoint returns correct status."""
        response = test_client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "version" in data
    
    def test_root_endpoint(self, test_client: TestClient):
        """Test root endpoint returns API information."""
        response = test_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data


class TestUploadEndpoint:
    """Tests for file upload endpoint."""
    
    def test_upload_scan_valid_ply(self, test_client: TestClient, synthetic_ply_file: str):
        """Test uploading a valid PLY file."""
        with open(synthetic_ply_file, "rb") as f:
            files = {"file": ("test_room.ply", f, "application/octet-stream")}
            response = test_client.post("/api/upload-scan", files=files)
        
        # Upload should succeed (200 or 201)
        assert response.status_code in [200, 201]
        
        data = response.json()
        assert data["status"] == "success"
        assert "room_id" in data
        assert "objects_detected" in data
        assert isinstance(data["objects_detected"], int)
        assert data["objects_detected"] >= 0
    
    def test_upload_scan_invalid_format(self, test_client: TestClient):
        """Test uploading an invalid file format."""
        # Create a fake non-PLY file
        fake_file = io.BytesIO(b"fake content")
        files = {"file": ("test.txt", fake_file, "text/plain")}
        response = test_client.post("/api/upload-scan", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "PLY" in data["detail"] or "SPZ" in data["detail"]
    
    def test_upload_scan_missing_file(self, test_client: TestClient):
        """Test upload endpoint without file."""
        response = test_client.post("/api/upload-scan")
        
        assert response.status_code == 422  # Validation error
    
    def test_upload_scan_empty_file(self, test_client: TestClient):
        """Test uploading an empty file."""
        empty_file = io.BytesIO(b"")
        files = {"file": ("empty.ply", empty_file, "application/octet-stream")}
        response = test_client.post("/api/upload-scan", files=files)
        
        # Should either reject empty file or process it (implementation dependent)
        assert response.status_code in [400, 500]  # Should error on empty file
    
    def test_upload_scan_invalid_ply_structure(self, test_client: TestClient):
        """Test uploading a file with invalid PLY structure."""
        invalid_ply = io.BytesIO(b"ply\nformat ascii 1.0\ninvalid content")
        files = {"file": ("invalid.ply", invalid_ply, "application/octet-stream")}
        response = test_client.post("/api/upload-scan", files=files)
        
        # Should reject invalid PLY structure
        assert response.status_code in [400, 500]


class TestRoomDimensionsEndpoint:
    """Tests for room dimensions endpoint."""
    
    def test_get_room_dimensions_existing(self, test_client: TestClient, synthetic_ply_file: str):
        """Test getting dimensions for an existing room."""
        # First upload a scan
        with open(synthetic_ply_file, "rb") as f:
            files = {"file": ("test_room.ply", f, "application/octet-stream")}
            upload_response = test_client.post("/api/upload-scan", files=files)
        
        if upload_response.status_code not in [200, 201]:
            pytest.skip("Upload failed, cannot test dimensions endpoint")
        
        room_id = upload_response.json()["room_id"]
        
        # Get dimensions
        response = test_client.get(f"/api/room/{room_id}/dimensions")
        
        assert response.status_code == 200
        data = response.json()
        assert "length" in data
        assert "width" in data
        assert "height" in data
        assert "accuracy" in data
        
        # Verify positive dimensions
        assert data["length"] > 0
        assert data["width"] > 0
        assert data["height"] > 0
    
    def test_get_room_dimensions_nonexistent(self, test_client: TestClient):
        """Test getting dimensions for non-existent room."""
        response = test_client.get("/api/room/nonexistent_room/dimensions")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


class TestRoomObjectsEndpoint:
    """Tests for room objects endpoint."""
    
    def test_get_room_objects_existing(self, test_client: TestClient, synthetic_ply_file: str):
        """Test getting objects for an existing room."""
        # First upload a scan
        with open(synthetic_ply_file, "rb") as f:
            files = {"file": ("test_room.ply", f, "application/octet-stream")}
            upload_response = test_client.post("/api/upload-scan", files=files)
        
        if upload_response.status_code not in [200, 201]:
            pytest.skip("Upload failed, cannot test objects endpoint")
        
        room_id = upload_response.json()["room_id"]
        
        # Get objects
        response = test_client.get(f"/api/room/{room_id}/objects")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Verify object structure if objects exist
        for obj in data:
            assert "type" in obj
            assert "position" in obj
            assert "dimensions" in obj
            assert "volume" in obj
            assert "confidence" in obj
    
    def test_get_room_objects_nonexistent(self, test_client: TestClient):
        """Test getting objects for non-existent room."""
        response = test_client.get("/api/room/nonexistent_room/objects")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


class TestRoomDataEndpoint:
    """Tests for complete room data endpoint."""
    
    def test_get_room_data_existing(self, test_client: TestClient, synthetic_ply_file: str):
        """Test getting complete room data."""
        # First upload a scan
        with open(synthetic_ply_file, "rb") as f:
            files = {"file": ("test_room.ply", f, "application/octet-stream")}
            upload_response = test_client.post("/api/upload-scan", files=files)
        
        if upload_response.status_code not in [200, 201]:
            pytest.skip("Upload failed, cannot test room data endpoint")
        
        room_id = upload_response.json()["room_id"]
        
        # Get complete room data
        response = test_client.get(f"/api/room/{room_id}/data")
        
        assert response.status_code == 200
        data = response.json()
        assert "room_id" in data
        assert "dimensions" in data
        assert "objects" in data
        assert "point_count" in data
        assert "processed_points" in data
        
        # Verify dimensions structure
        assert "length" in data["dimensions"]
        assert "width" in data["dimensions"]
        assert "height" in data["dimensions"]
        
        # Verify objects is a list
        assert isinstance(data["objects"], list)
    
    def test_get_room_data_nonexistent(self, test_client: TestClient):
        """Test getting data for non-existent room."""
        response = test_client.get("/api/room/nonexistent_room/data")
        
        assert response.status_code == 404


class TestCheckFitEndpoint:
    """Tests for item fit checking endpoint."""
    
    def test_check_fit_valid_item(self, test_client: TestClient, synthetic_ply_file: str):
        """Test checking if an item fits in a room."""
        # First upload a scan
        with open(synthetic_ply_file, "rb") as f:
            files = {"file": ("test_room.ply", f, "application/octet-stream")}
            upload_response = test_client.post("/api/upload-scan", files=files)
        
        if upload_response.status_code not in [200, 201]:
            pytest.skip("Upload failed, cannot test fit check endpoint")
        
        room_id = upload_response.json()["room_id"]
        
        # Check fit for a small item
        item_data = {
            "item_type": "table",
            "dimensions": [1.0, 0.8, 0.75]  # Small table
        }
        response = test_client.post(
            f"/api/room/{room_id}/check-fit",
            json=item_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "fits" in data
        assert isinstance(data["fits"], bool)
        assert "available_positions" in data
        assert isinstance(data["available_positions"], list)
        assert "constraints" in data
        assert isinstance(data["constraints"], list)
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)
    
    def test_check_fit_too_large_item(self, test_client: TestClient, synthetic_ply_file: str):
        """Test checking fit for an item that's too large."""
        # First upload a scan
        with open(synthetic_ply_file, "rb") as f:
            files = {"file": ("test_room.ply", f, "application/octet-stream")}
            upload_response = test_client.post("/api/upload-scan", files=files)
        
        if upload_response.status_code not in [200, 201]:
            pytest.skip("Upload failed, cannot test fit check endpoint")
        
        room_id = upload_response.json()["room_id"]
        
        # Check fit for a very large item
        item_data = {
            "item_type": "sofa",
            "dimensions": [10.0, 5.0, 3.0]  # Way too large
        }
        response = test_client.post(
            f"/api/room/{room_id}/check-fit",
            json=item_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["fits"] == False  # Should not fit
        assert len(data["constraints"]) > 0
    
    def test_check_fit_invalid_dimensions(self, test_client: TestClient, synthetic_ply_file: str):
        """Test checking fit with invalid item dimensions."""
        with open(synthetic_ply_file, "rb") as f:
            files = {"file": ("test_room.ply", f, "application/octet-stream")}
            upload_response = test_client.post("/api/upload-scan", files=files)
        
        if upload_response.status_code not in [200, 201]:
            pytest.skip("Upload failed")
        
        room_id = upload_response.json()["room_id"]
        
        # Invalid dimensions (wrong length)
        item_data = {
            "item_type": "table",
            "dimensions": [1.0, 0.8]  # Missing height
        }
        response = test_client.post(
            f"/api/room/{room_id}/check-fit",
            json=item_data
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_check_fit_nonexistent_room(self, test_client: TestClient):
        """Test checking fit for non-existent room."""
        item_data = {
            "item_type": "table",
            "dimensions": [1.0, 0.8, 0.75]
        }
        response = test_client.post(
            "/api/room/nonexistent_room/check-fit",
            json=item_data
        )
        
        assert response.status_code == 404


class TestOptimizeEndpoint:
    """Tests for layout optimization endpoint."""
    
    def test_optimize_existing_room(self, test_client: TestClient, synthetic_ply_file: str):
        """Test getting optimization suggestions for existing room."""
        # First upload a scan
        with open(synthetic_ply_file, "rb") as f:
            files = {"file": ("test_room.ply", f, "application/octet-stream")}
            upload_response = test_client.post("/api/upload-scan", files=files)
        
        if upload_response.status_code not in [200, 201]:
            pytest.skip("Upload failed, cannot test optimize endpoint")
        
        room_id = upload_response.json()["room_id"]
        
        # Get optimization suggestions
        response = test_client.get(f"/api/room/{room_id}/optimize")
        
        assert response.status_code == 200
        data = response.json()
        assert "room_id" in data
        assert "optimization_suggestions" in data
        assert isinstance(data["optimization_suggestions"], list)
        assert "current_layout_score" in data
        assert 0 <= data["current_layout_score"] <= 1
        assert "improvement_potential" in data
    
    def test_optimize_nonexistent_room(self, test_client: TestClient):
        """Test optimization for non-existent room."""
        response = test_client.get("/api/room/nonexistent_room/optimize")
        
        assert response.status_code == 404


class TestErrorHandling:
    """Tests for error handling and edge cases."""
    
    def test_invalid_room_id_format(self, test_client: TestClient):
        """Test endpoints with invalid room ID formats."""
        # Test various invalid formats
        invalid_ids = ["", " ", "room@#$%", "room with spaces"]
        
        for invalid_id in invalid_ids:
            response = test_client.get(f"/api/room/{invalid_id}/dimensions")
            # Should either 404 or validate format (implementation dependent)
            assert response.status_code in [404, 422]
    
    def test_malformed_json_request(self, test_client: TestClient):
        """Test endpoints with malformed JSON."""
        # Try to send malformed JSON
        response = test_client.post(
            "/api/room/test_room/check-fit",
            data="not json",
            headers={"Content-Type": "application/json"}
        )
        
        # Should return 422 (Unprocessable Entity)
        assert response.status_code == 422
    
    def test_response_time_acceptable(self, test_client: TestClient):
        """Test that API responses are within acceptable time limits."""
        import time
        
        start = time.time()
        response = test_client.get("/api/health")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        # Health check should be very fast (< 1 second)
        assert elapsed < 1.0

