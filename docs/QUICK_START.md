# Quick Start Guide

Get up and running with the 3D Room Intelligence System in minutes.

## 🚀 Running Tests

### Without Database (Processing Tests Only)
```bash
source venv311/bin/activate
pytest tests/test_processing.py -v
```
**Result:** 16/16 tests passing ✅

### With Database (All Tests)
```bash
# Start PostgreSQL
docker-compose up -d postgres

# Wait for database (~10-30 seconds)
sleep 15

# Run all tests
source venv311/bin/activate
pytest -v
```

**Note:** Tests will automatically skip if database is not available (graceful degradation).

## 🐳 Running the API

### Option 1: Docker Compose (Recommended)
```bash
# Start all services (API + Database)
docker-compose up

# Or run in background
docker-compose up -d

# View logs
docker-compose logs -f api
```

**API will be available at:**
- Main API: http://localhost:8000
- Documentation: http://localhost:8000/api/docs
- Health Check: http://localhost:8000/api/health

### Option 2: Local Development
```bash
# Start database only
docker-compose up -d postgres

# Activate virtual environment
source venv311/bin/activate

# Run API locally
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

## 📋 Prerequisites Check

### Docker & Docker Compose
```bash
# Check if installed
docker --version
docker-compose --version

# If not installed (Ubuntu/Debian)
sudo apt update
sudo apt install docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
```

### Python Environment
```bash
# Check Python version (needs 3.11+)
python3 --version

# Virtual environment is already created at venv311/
source venv311/bin/activate

# Verify dependencies
pip list | grep -E "(fastapi|open3d|sqlalchemy)"
```

## 🧪 Test Commands

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

## 🔧 Troubleshooting

### "Connection refused" in tests
- **Solution:** Start database: `docker-compose up -d postgres`
- **Alternative:** Skip DB tests: `pytest -v -m "not db_required"`

### "Module not found: backend"
- **Solution:** Ensure you're in project root and `pytest.ini` exists
- **Check:** `python -c "import backend; print(backend)"`

### Docker Compose not found
- **Install:** `sudo apt install docker-compose`
- **Or use:** `docker compose` (newer Docker versions)

### Database initialization fails
- **Check:** `docker-compose logs postgres`
- **Verify:** `init.sql` exists at `backend/database/migrations/init.sql`
- **Recreate:** `docker-compose down -v && docker-compose up -d postgres`

### "ModuleNotFoundError: No module named 'open3d'"
- You need Python 3.11. See [INSTALLATION.md](INSTALLATION.md#step-1-install-python-311).

### "Database connection failed"
- For local processing: Not needed - use `python test_local.py`
- For API: Ensure PostgreSQL is running and `.env` is configured correctly.

### Processing takes too long
- Normal for large PLY files (1-2 minutes)
- Check `logs/api.log` for progress
- Reduce point count if needed (pre-process PLY file)

## 📝 Environment Variables

All configuration is in `.env` file. Key variables:

```bash
# Database
DATABASE_URL=postgresql://room_intel:secure_password@localhost:5432/room_intelligence

# API
API_HOST=0.0.0.0
API_PORT=8000

# Processing (see .env for all parameters)
VOXEL_SIZE=0.05
RANSAC_DISTANCE_THRESHOLD=0.01
DBSCAN_EPS=0.1
```

## 🎯 First Steps

1. **Verify setup:**
   ```bash
   pytest tests/test_processing.py -v  # Should pass
   ```

2. **Start database:**
   ```bash
   docker-compose up -d postgres
   ```

3. **Run full test suite:**
   ```bash
   pytest -v
   ```

4. **Start API:**
   ```bash
   docker-compose up
   # OR
   uvicorn backend.api.main:app --reload
   ```

5. **Test API:**
   ```bash
   curl http://localhost:8000/api/health
   ```

## 📚 Documentation

- **API Docs:** http://localhost:8000/api/docs (when API is running)
- **Test Setup:** See [TESTING.md](TESTING.md)
- **Completion Status:** See [COMPLETION_CHECKLIST.md](COMPLETION_CHECKLIST.md)
- **Project Plan:** See [3d-room-intelligence-system.plan.md](3d-room-intelligence-system.plan.md)
