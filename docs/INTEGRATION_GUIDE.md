# Integration Guide: Using the 3D Room Intelligence API

This guide shows how to integrate the 3D Room Intelligence System into other projects.

## Quick Start: Get Your Room ID

### Step 1: Start the System

```bash
cd "/home/nathan/Documents/Cursor Projects/3d Scan integration"
source venv311/bin/activate

# Start PostgreSQL database
docker-compose up -d postgres

# Wait 10 seconds for database to be ready
sleep 10

# Start the API
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be running at: http://localhost:8000

### Step 2: Upload Your Scan (First Time Only)

If you haven't uploaded your bedroom scan yet:

```bash
curl -X POST "http://localhost:8000/api/upload-scan" \
  -F "file=@Room scan v1.ply" \
  | jq '.'
```

**Response will include:**
```json
{
  "status": "success",
  "room_id": "room_001",
  "objects_detected": 5,
  "processing_time": 45.2
}
```

**Save this `room_id` - you'll use it in your other project!**

### Step 3: Query Room Data

Once you have your `room_id`, query the API:

```bash
# Get room dimensions
curl http://localhost:8000/api/room/room_001/dimensions | jq '.'

# Get detected objects (furniture)
curl http://localhost:8000/api/room/room_001/objects | jq '.'

# Get complete room data
curl http://localhost:8000/api/room/room_001/data | jq '.'
```

---

## Integration Workflow for Your New Project

### Recommended Approach: Query During Development

**Answer to Cursor's question: "Yes, query the API now to get real data"**

This way you can:
1. Build your project with **real room dimensions**
2. Use **actual furniture positions** from your bedroom
3. Design features based on **real spatial data**

### Alternative: Build Infrastructure First

If you want to build the structure first:
1. Create mock data matching the API response format
2. Build your features with the mock data
3. Swap in real API calls later

---

## API Response Format Reference

### Room Dimensions
```json
{
  "length": 4.2,
  "width": 3.5,
  "height": 2.6,
  "accuracy": "±2-5cm",
  "confidence": 0.85
}
```

### Detected Objects
```json
[
  {
    "id": 1,
    "type": "bed",
    "position": [1.5, 0.45, 2.0],
    "dimensions": [2.0, 1.6, 0.5],
    "volume": 1.6,
    "confidence": 0.80
  },
  {
    "id": 2,
    "type": "nightstand",
    "position": [0.5, 0.55, 2.5],
    "dimensions": [0.5, 0.4, 0.6],
    "volume": 0.12,
    "confidence": 0.75
  }
]
```

### Complete Room Data
```json
{
  "room": {
    "room_id": "room_001",
    "scan_date": "2025-11-07T12:00:00",
    "point_count": 3500000,
    "processed_points": 1200000
  },
  "dimensions": { ... },
  "objects": [ ... ],
  "relationships": [ ... ]
}
```

---

## Python Client Example

Use this in your new project:

```python
import requests

class Room3DScanClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def get_room_dimensions(self, room_id):
        """Get room dimensions."""
        response = requests.get(f"{self.base_url}/api/room/{room_id}/dimensions")
        return response.json()
    
    def get_room_objects(self, room_id):
        """Get detected furniture objects."""
        response = requests.get(f"{self.base_url}/api/room/{room_id}/objects")
        return response.json()
    
    def get_complete_room_data(self, room_id):
        """Get complete room data."""
        response = requests.get(f"{self.base_url}/api/room/{room_id}/data")
        return response.json()
    
    def check_item_fit(self, room_id, item_type, dimensions):
        """Check if a new item fits in the room."""
        payload = {
            "item_type": item_type,
            "dimensions": dimensions  # [length, width, height]
        }
        response = requests.post(
            f"{self.base_url}/api/room/{room_id}/check-fit",
            json=payload
        )
        return response.json()

# Usage
client = Room3DScanClient()
room_id = "room_001"  # Your bedroom scan

# Get data
dimensions = client.get_room_dimensions(room_id)
objects = client.get_room_objects(room_id)

print(f"Room: {dimensions['length']}m x {dimensions['width']}m x {dimensions['height']}m")
print(f"Furniture detected: {len(objects)}")
```

---

## Environment Variables

Add to your new project's `.env`:

```bash
# 3D Room Intelligence API
ROOM_API_URL=http://localhost:8000
BEDROOM_ROOM_ID=room_001  # Replace with your actual room_id
```

---

## Next Steps

1. **Start the API** (see Step 1 above)
2. **Upload your scan** if you haven't already (Step 2)
3. **Get your room_id** from the upload response
4. **Tell Cursor**: "My room_id is `room_001` (or whatever you got). Please query the API now to get real dimensions and furniture data."
5. **Build your project** using the real spatial data

---

## Troubleshooting

### "Connection refused"
- Make sure the API is running on port 8000
- Check: `curl http://localhost:8000/api/health`

### "Room not found"
- You need to upload your scan first
- Check available rooms: `curl http://localhost:8000/api/rooms` (if implemented)

### "No objects detected"
- The scan might need better DBSCAN parameters
- Check logs: `docker-compose logs api`

---

## API Documentation

Full interactive API docs: http://localhost:8000/api/docs

