# Quick Integration: Use This In Your Other Project

## 1. Get Your Room ID (Run This First)

In a terminal:
```bash
cd "/home/nathan/Documents/Cursor Projects/3d Scan integration"
./get_room_id.sh
```

This will:
- Start the database and API
- Upload your bedroom scan
- Give you a `room_id` (e.g., "room_001")
- Show you the dimensions and furniture detected

## 2. Tell Cursor This

Once you have your room_id, tell Cursor in your other project:

```
My room_id is "room_001" (or whatever you got).

The 3D Room Intelligence API is running at http://localhost:8000

Please query these endpoints to get real room data:

1. Dimensions: GET http://localhost:8000/api/room/room_001/dimensions
2. Objects: GET http://localhost:8000/api/room/room_001/objects
3. Complete data: GET http://localhost:8000/api/room/room_001/data

Use this real spatial data to build the project features.
```

## 3. Sample Response Data

**Dimensions Response:**
```json
{
  "length": 4.2,
  "width": 3.5,
  "height": 2.6,
  "accuracy": "±2-5cm",
  "confidence": 0.85
}
```

**Objects Response:**
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

## 4. Python Code to Use in Your Project

```python
import requests

# Configuration
ROOM_API_URL = "http://localhost:8000"
ROOM_ID = "room_001"  # Replace with your actual room_id

# Get room dimensions
response = requests.get(f"{ROOM_API_URL}/api/room/{ROOM_ID}/dimensions")
dimensions = response.json()

print(f"Room size: {dimensions['length']}m x {dimensions['width']}m x {dimensions['height']}m")

# Get furniture
response = requests.get(f"{ROOM_API_URL}/api/room/{ROOM_ID}/objects")
furniture = response.json()

for item in furniture:
    print(f"- {item['type']}: {item['dimensions']} @ position {item['position']}")
```

## 5. If You Want Mock Data First

If the API isn't running yet, use this mock data structure:

```python
# Mock room data (matches API format)
MOCK_ROOM_DATA = {
    "dimensions": {
        "length": 4.2,
        "width": 3.5,
        "height": 2.6,
        "accuracy": "±2-5cm",
        "confidence": 0.85
    },
    "objects": [
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
}
```

---

## Quick Reference

**API Endpoints:**
- Health: `GET /api/health`
- Upload: `POST /api/upload-scan` (multipart/form-data)
- Dimensions: `GET /api/room/{room_id}/dimensions`
- Objects: `GET /api/room/{room_id}/objects`
- Complete: `GET /api/room/{room_id}/data`
- Check fit: `POST /api/room/{room_id}/check-fit`
- Optimize: `GET /api/room/{room_id}/optimize`

**Interactive Docs:** http://localhost:8000/api/docs

