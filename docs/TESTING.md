# Testing Guide

Complete guide for testing the 3D Room Intelligence System.

## Test Setup

### Quick Start - Run Tests Without Database

Processing tests don't require a database and will pass immediately:

```bash
source venv311/bin/activate
pytest tests/test_processing.py -v
```

**Result:** 16/16 tests passing ✅

### Run All Tests with Docker PostgreSQL

**Start PostgreSQL database:**
```bash
# Start only the database service
docker-compose up -d postgres

# Wait for database to be ready (takes ~10-30 seconds)
docker-compose ps

# Run all tests
pytest -v
```

**Note:** Tests will automatically skip if database is not available (graceful degradation).

### Run All Tests with Local PostgreSQL

If you have PostgreSQL installed locally:

1. **Create test database:**
```bash
createdb room_intelligence_test
```

2. **Run migrations:**
```bash
psql -d room_intelligence_test -f backend/database/migrations/init.sql
```

3. **Set environment variable:**
```bash
export TEST_DATABASE_URL="postgresql+psycopg://room_intel:secure_password@localhost:5432/room_intelligence_test"
```

4. **Run tests:**
```bash
pytest -v
```

### Test Database Configuration

The test suite uses a separate test database to avoid affecting production data.

- **Default test DB URL:** `postgresql+psycopg://room_intel:secure_password@localhost:5432/room_intelligence_test`
- **Override:** Set `TEST_DATABASE_URL` environment variable

### API Configuration for Testing

**No API configuration needed for testing!** The test suite:
- Uses `TEST_MODE=true` to prevent import-time database connections
- Overrides database dependencies with test sessions
- Isolates tests using transaction rollback

## Test Commands

```bash
# All tests
pytest -v

# Only processing tests (no DB needed)
pytest tests/test_processing.py -v

# Only API tests (requires DB)
pytest tests/test_api.py -v

# Skip database-required tests
pytest -v -m "not db_required"

# Run with coverage
pytest --cov=backend --cov-report=html
```

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
- Or use the API: `curl -X POST "http://localhost:8000/api/upload-scan" -F "file=@your_scan.ply"`

## Migration Notes

If you have an existing database with the old `metadata` column name, run:

```bash
psql -d your_database_name -f backend/database/migrations/migrate_metadata_to_extra_metadata.sql
```

This will rename `metadata` → `extra_metadata` in both `rooms` and `detected_objects` tables.

## Troubleshooting

### "Connection refused" errors
- Start PostgreSQL: `docker-compose up -d postgres`
- Or skip API tests: `pytest tests/test_processing.py`

### "Module not found" errors
- Ensure you're in the project root
- Activate virtual environment: `source venv311/bin/activate`
- `pytest.ini` should handle Python path automatically

### Test isolation issues
- Tests use transaction rollback for isolation
- Each test gets a fresh transaction that's rolled back
- If issues persist, restart the test database

### Other Issues

See [QUICK_START.md](QUICK_START.md#troubleshooting) for additional troubleshooting.

