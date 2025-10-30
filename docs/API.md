# 3D Room Intelligence API Documentation

Complete API endpoint reference for the 3D Room Intelligence System. This API processes 3D room scans from iPhone 17 Pro Max + Scaniverse and provides spatial intelligence endpoints.

**Base URL**: `http://localhost:8000`  
**API Version**: 1.0.0

---

## Table of Contents

- [Authentication](#authentication)
- [Health Check](#health-check)
- [Upload Scan](#upload-scan)
- [Room Endpoints](#room-endpoints)
  - [Get Room Dimensions](#get-room-dimensions)
  - [Get Room Objects](#get-room-objects)
  - [Get Complete Room Data](#get-complete-room-data)
- [Analysis Endpoints](#analysis-endpoints)
  - [Check Item Fit](#check-item-fit)
  - [Optimize Layout](#optimize-layout)
- [Error Handling](#error-handling)

---

## Authentication

Currently, the API does not require authentication. In production, implement JWT or API key authentication.

---

## Health Check

### GET `/api/health`

Check API health status.

**Response**: `200 OK`

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected"
}
```

**Example Request**:
```bash
curl -X GET http://localhost:8000/api/health
```

---

## Upload Scan

### POST `/api/upload-scan`

Upload and process a PLY/SPZ file from Scaniverse.

**Content-Type**: `multipart/form-data`

**Parameters**:
- `file` (required): PLY or SPZ file (max 250MB)

**Constraints**:
- Maximum file size: 250MB (262,144,000 bytes)
- Supported formats: `.ply`, `.spz` (SPZ support in Phase 5)
- Processing time: 60-120 seconds for typical room scans (1-3M points)

**Response**: `200 OK` or `201 Created`

```json
{
  "status": "success",
  "room_id": "room_a1b2c3d4",
  "message": "Processed 585756 points, detected 3 objects",
  "objects_detected": 3
}
```

**Error Responses**:
- `400 Bad Request`: Invalid file format or file too large
- `500 Internal Server Error`: Processing error

**Example Request**:
```bash
curl -X POST \
  http://localhost:8000/api/upload-scan \
  -F "file=@/path/to/room_scan.ply"
```

**Using Python**:
```python
import requests

with open("room_scan.ply", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/upload-scan",
        files={"file": ("room_scan.ply", f, "application/octet-stream")}
    )
    print(response.json())
```

---

## Room Endpoints

All room endpoints require a `room_id` obtained from the upload endpoint.

### Get Room Dimensions

### GET `/api/room/{room_id}/dimensions`

Get room dimensions with accuracy estimates.

**Parameters**:
- `room_id` (path, required): Room identifier from upload response

**Response**: `200 OK`

```json
{
  "length": 6.10,
  "width": 4.74,
  "height": 2.58,
  "accuracy": "±2-5cm"
}
```

**Response Fields**:
- `length`: Room length in meters (float)
- `width`: Room width in meters (float)
- `height`: Room height in meters (float)
- `accuracy`: Accuracy estimate string (typically "±2-5cm")

**Error Responses**:
- `404 Not Found`: Room not found

**Example Request**:
```bash
curl -X GET http://localhost:8000/api/room/room_a1b2c3d4/dimensions
```

---

### Get Room Objects

### GET `/api/room/{room_id}/objects`

Get list of detected furniture/objects in the room.

**Parameters**:
- `room_id` (path, required): Room identifier

**Response**: `200 OK`

```json
[
  {
    "type": "table",
    "position": [2.0, 1.5, 0.75],
    "dimensions": [1.2, 0.8, 0.75],
    "volume": 0.72,
    "confidence": 0.78
  },
  {
    "type": "chair",
    "position": [1.5, 1.0, 0.0],
    "dimensions": [0.5, 0.5, 0.45],
    "volume": 0.11,
    "confidence": 0.72
  }
]
```

**Response Fields** (per object):
- `type`: Object type (table, chair, sofa, bed, desk, cabinet, unknown)
- `position`: 3D position [x, y, z] in meters
- `dimensions`: Dimensions [length, width, height] in meters
- `volume`: Volume in cubic meters (float)
- `confidence`: Classification confidence score (0.0-1.0)

**Error Responses**:
- `404 Not Found`: Room not found

**Example Request**:
```bash
curl -X GET http://localhost:8000/api/room/room_a1b2c3d4/objects
```

---

### Get Complete Room Data

### GET `/api/room/{room_id}/data`

Get complete room data including dimensions, objects, and point counts.

**Parameters**:
- `room_id` (path, required): Room identifier

**Response**: `200 OK`

```json
{
  "room_id": "room_a1b2c3d4",
  "dimensions": {
    "length": 6.10,
    "width": 4.74,
    "height": 2.58,
    "accuracy": "±2-5cm"
  },
  "objects": [
    {
      "type": "table",
      "position": [2.0, 1.5, 0.75],
      "dimensions": [1.2, 0.8, 0.75],
      "volume": 0.72,
      "confidence": 0.78
    }
  ],
  "point_count": 585756,
  "processed_points": 440000
}
```

**Response Fields**:
- `room_id`: Room identifier
- `dimensions`: Room dimensions (see Get Room Dimensions)
- `objects`: List of detected objects (see Get Room Objects)
- `point_count`: Total points in original scan
- `processed_points`: Points after preprocessing

**Error Responses**:
- `404 Not Found`: Room not found

**Example Request**:
```bash
curl -X GET http://localhost:8000/api/room/room_a1b2c3d4/data
```

---

## Analysis Endpoints

### Check Item Fit

### POST `/api/room/{room_id}/check-fit`

Check if a furniture item fits in the room and find available positions.

**Parameters**:
- `room_id` (path, required): Room identifier

**Request Body**:
```json
{
  "item_type": "table",
  "dimensions": [1.5, 0.9, 0.75],
        "preferred_position": [2.0, 1.5, 0.0]
}
```

**Request Fields**:
- `item_type` (required): Item type (e.g., "table", "sofa", "desk")
- `dimensions` (required): Item dimensions [length, width, height] in meters (array of 3 floats)
- `preferred_position` (optional): Preferred position [x, y, z] in meters (array of 3 floats)

**Response**: `200 OK`

```json
{
  "fits": true,
  "available_positions": [
    [1.0, 1.0, 0.0],
    [2.0, 1.5, 0.0],
    [0.5, 2.0, 0.0]
  ],
  "constraints": [],
  "recommendations": [
    "Consider placement near walls for stability",
    "Ensure adequate clearance for movement (60cm minimum)"
  ]
}
```

**Response Fields**:
- `fits`: Boolean indicating if item fits
- `available_positions`: List of available positions [x, y, z] where item can be placed
- `constraints`: List of constraints preventing placement (empty if fits=true)
- `recommendations`: List of placement recommendations

**Error Responses**:
- `404 Not Found`: Room not found
- `422 Unprocessable Entity`: Invalid request body (validation error)

**Example Request**:
```bash
curl -X POST \
  http://localhost:8000/api/room/room_a1b2c3d4/check-fit \
  -H "Content-Type: application/json" \
  -d '{
    "item_type": "table",
    "dimensions": [1.5, 0.9, 0.75]
  }'
```

**Using Python**:
```python
import requests

response = requests.post(
    "http://localhost:8000/api/room/room_a1b2c3d4/check-fit",
    json={
        "item_type": "table",
        "dimensions": [1.5, 0.9, 0.75],
        "preferred_position": [2.0, 1.5, 0.0]
    }
)
print(response.json())
```

---

### Optimize Layout

### GET `/api/room/{room_id}/optimize`

Get AI-powered layout optimization suggestions.

**Parameters**:
- `room_id` (path, required): Room identifier

**Response**: `200 OK`

```json
{
  "room_id": "room_a1b2c3d4",
  "optimization_suggestions": [
    "Room has plenty of space for additional furniture",
    "Create clear pathways between furniture",
    "Group related items for better workflow"
  ],
  "current_layout_score": 0.75,
  "improvement_potential": "Medium"
}
```

**Response Fields**:
- `room_id`: Room identifier
- `optimization_suggestions`: List of optimization suggestions (strings)
- `current_layout_score`: Layout score from 0.0 to 1.0 (float)
- `improvement_potential`: Improvement potential level ("Low", "Medium", "High")

**Error Responses**:
- `404 Not Found`: Room not found

**Example Request**:
```bash
curl -X GET http://localhost:8000/api/room/room_a1b2c3d4/optimize
```

---

## Error Handling

### Standard Error Response Format

All errors return JSON in the following format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters or file
- `404 Not Found`: Resource (room) not found
- `422 Unprocessable Entity`: Validation error (invalid request body)
- `500 Internal Server Error`: Server error during processing

### Common Error Scenarios

**Invalid File Format**:
```bash
# Uploading non-PLY file
curl -X POST http://localhost:8000/api/upload-scan -F "file=@test.txt"

# Response: 400 Bad Request
{
  "detail": "Only PLY and SPZ formats supported. Phase 1-2: PLY support only."
}
```

**File Too Large**:
```bash
# Uploading file exceeding 250MB limit
# Response: 400 Bad Request
{
  "detail": "File too large: 300000000 bytes (max: 262144000)"
}
```

**Room Not Found**:
```bash
# Requesting non-existent room
curl -X GET http://localhost:8000/api/room/nonexistent/dimensions

# Response: 404 Not Found
{
  "detail": "Room nonexistent not found"
}
```

**Invalid Request Body**:
```bash
# Missing required fields
curl -X POST http://localhost:8000/api/room/room_123/check-fit \
  -H "Content-Type: application/json" \
  -d '{"item_type": "table"}'

# Response: 422 Unprocessable Entity
{
  "detail": [
    {
      "loc": ["body", "dimensions"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Interactive API Documentation

FastAPI provides interactive API documentation:

- **Swagger UI**: `http://localhost:8000/api/docs`
- **ReDoc**: `http://localhost:8000/api/redoc`
- **OpenAPI Schema**: `http://localhost:8000/api/openapi.json`

You can use these interfaces to explore endpoints, test requests, and view request/response schemas interactively.

---

## Rate Limiting

Currently, no rate limiting is implemented. In production, implement rate limiting to prevent abuse.

---

## Performance Considerations

### Processing Times

- **Typical room scan (1-3M points)**: 60-120 seconds
- **Small room (<500K points)**: 30-60 seconds
- **Large room (>3M points)**: 120-180 seconds

### Response Times

- **Health check**: < 100ms
- **Dimension/object queries**: < 1 second
- **Fit checking**: < 500ms
- **Layout optimization**: < 1 second

### Recommendations

- Process uploads asynchronously for better user experience
- Cache frequently accessed room data
- Use pagination for rooms with many objects (future enhancement)

---

## Version History

- **v1.0.0** (Current): Initial release with PLY support, RANSAC/DBSCAN processing, all core endpoints

---

**Note**: This documentation corresponds to API version 1.0.0. For updates, check the OpenAPI schema at `/api/openapi.json`.

