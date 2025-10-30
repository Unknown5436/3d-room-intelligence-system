# Quick Start Guide

Get up and running with the 3D Room Intelligence System in minutes.

## Prerequisites

- Python 3.11 installed (see [INSTALLATION.md](INSTALLATION.md))
- Virtual environment activated
- PLY file ready for processing

## Step 1: Activate Virtual Environment

```bash
source venv311/bin/activate
```

## Step 2: Process a PLY File

Process your PLY file directly without database:

```bash
python test_local.py
```

This will:
- Load and preprocess the point cloud
- Detect room dimensions
- Identify objects and furniture
- Display results and save to `processing_results.json`

### Example Output

```
Processing Room scan v1.ply...
This may take 1-2 minutes depending on file size...

============================================================
PROCESSING RESULTS
============================================================

Point Cloud:
  Original points: 585,756
  Processed points: 43,338
  Scan quality: 0.45
  Processing time: 1.53 seconds

Room Dimensions:
  Length: 4.00m
  Width: 3.00m
  Height: 2.50m
  Accuracy: ±2-5cm

Detected Objects: 0
```

## Step 3: Start API Server (Optional)

**Requires database setup** (see [INSTALLATION.md](INSTALLATION.md)):

```bash
uvicorn backend.api.main:app --reload
```

API endpoints:
- **Interactive docs**: http://localhost:8000/api/docs
- **Health check**: http://localhost:8000/api/health
- **Upload scan**: `POST /api/upload-scan`

### Test API Upload

In another terminal:

```bash
python test_upload.py
```

## Common Commands

```bash
# Process PLY file locally
python test_local.py

# Start API server
uvicorn backend.api.main:app --reload

# Check API health
curl http://localhost:8000/api/health

# Upload file via API
curl -X POST "http://localhost:8000/api/upload-scan" \
  -F "file=@Room scan v1.ply"
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'open3d'"

You need Python 3.11. See [INSTALLATION.md](INSTALLATION.md#step-1-install-python-311).

### "Database connection failed"

For local processing: Not needed - use `test_local.py`
For API: Ensure PostgreSQL is running and `.env` is configured correctly.

### Processing takes too long

- Normal for large PLY files (1-2 minutes)
- Check `logs/api.log` for progress
- Reduce point count if needed (pre-process PLY file)

## Next Steps

- **[TESTING.md](TESTING.md)** - Complete testing guide
- **[INSTALLATION.md](INSTALLATION.md)** - Detailed installation instructions
