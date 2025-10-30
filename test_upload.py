#!/usr/bin/env python3
"""Simple test script to test PLY file upload.

This script tests the upload endpoint with a local PLY file.
"""
import requests
import os
from pathlib import Path

API_URL = "http://localhost:8000"
PLY_FILE = "Room scan v1.ply"

def test_upload():
    """Test uploading a PLY file to the API."""
    if not Path(PLY_FILE).exists():
        print(f"Error: PLY file not found: {PLY_FILE}")
        print(f"Current directory: {os.getcwd()}")
        print(f"Files in current directory: {os.listdir('.')}")
        return
    
    file_size = Path(PLY_FILE).stat().st_size / (1024 * 1024)  # MB
    print(f"Uploading {PLY_FILE} ({file_size:.2f} MB)...")
    
    with open(PLY_FILE, 'rb') as f:
        files = {'file': (PLY_FILE, f, 'application/octet-stream')}
        
        try:
            response = requests.post(
                f"{API_URL}/api/upload-scan",
                files=files,
                timeout=300  # 5 minute timeout for processing
            )
            
            print(f"\nStatus Code: {response.status_code}")
            print(f"Response: {response.json()}")
            
            if response.status_code == 200:
                data = response.json()
                room_id = data.get('room_id')
                print(f"\n✅ Upload successful!")
                print(f"Room ID: {room_id}")
                print(f"Objects detected: {data.get('objects_detected', 0)}")
                
                # Test getting room dimensions
                print(f"\nFetching room dimensions...")
                dims_response = requests.get(f"{API_URL}/api/room/{room_id}/dimensions")
                if dims_response.status_code == 200:
                    dims = dims_response.json()
                    print(f"Room dimensions: {dims}")
                else:
                    print(f"Error getting dimensions: {dims_response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"\n❌ Error: Could not connect to API at {API_URL}")
            print("Make sure the API server is running: uvicorn backend.api.main:app --reload")
        except requests.exceptions.Timeout:
            print(f"\n❌ Error: Request timed out (processing took longer than 5 minutes)")
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_upload()

