# Testing Guide

Complete guide for testing the 3D Room Intelligence System.

## Local Processing Test (No Database)

Test the processing pipeline directly:

```bash
source venv311/bin/activate
python test_local.py
```

This tests:
- Point cloud loading
- Preprocessing (outlier removal, downsampling)
- Plane detection (RANSAC)
- Room dimension extraction
- Object clustering (DBSCAN)
- Object classification

## API Testing (Requires Database)

### Setup Database

See [INSTALLATION.md](INSTALLATION.md#database-setup) for database setup.

### Start API Server

```bash
source venv311/bin/activate
uvicorn backend.api.main:app --reload
```

### Test Endpoints

#### 1. Health Check

```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected"
}
```

#### 2. Upload PLY File

**Using curl:**
```bash
curl -X POST "http://localhost:8000/api/upload-scan" \
  -F "file=@Room scan v1.ply"
```

**Using Python:**
```bash
python test_upload.py
```

**Expected response:**
```json
{
  "status": "success",
  "room_id": "room_abc123",
  "message": "Processed 585756 points, detected 5 objects",
  "objects_detected": 5
}
```

#### 3. Get Room Dimensions

```bash
curl "http://localhost:8000/api/room/{room_id}/dimensions"
```

**Expected response:**
```json
{
  "length": 4.2,
  "width": 3.5,
  "height": 2.5,
  "accuracy": "±2-5cm",
  "confidence": 0.85
}
```

#### 4. Get Detected Objects

```bash
curl "http://localhost:8000/api/room/{room_id}/objects"
```

#### 5. Get Complete Room Data

```bash
curl "http://localhost:8000/api/room/{room_id}/data"
```

#### 6. Check Item Fit

```bash
curl -X POST "http://localhost:8000/api/room/{room_id}/check-fit" \
  -H "Content-Type: application/json" \
  -d '{
    "item_type": "table",
    "dimensions": [1.5, 0.9, 0.75]
  }'
```

#### 7. Get Layout Optimization

```bash
curl "http://localhost:8000/api/room/{room_id}/optimize"
```

### Interactive API Documentation

Open in browser: http://localhost:8000/api/docs

Swagger UI provides interactive testing interface.

## Performance Benchmarks

Expected processing times (for ~585K point room scan):

- Point cloud loading: ~0.1 seconds
- Outlier removal: ~0.8 seconds
- Voxel downsampling: ~0.1 seconds
- Normal estimation: ~0.1 seconds
- RANSAC plane detection: ~0.3 seconds
- DBSCAN clustering: ~0.1 seconds
- Object classification: ~0.01 seconds
- **Total: ~1.5 seconds**

## Validation

### Accuracy Targets

- **Room Dimensions**: ±2-5cm (Section D1)
- **Object Classification**: 70-85% geometric, 85-95% with ML
- **Point Cloud Registration**: <0.2mm excellent

### Test Data

Place your PLY files in the project root for testing:
- `Room scan v1.ply` (already included)
- Or use: `python test_local.py --file your_scan.ply`

## Troubleshooting

See [QUICK_START.md](QUICK_START.md#troubleshooting) for common issues.

