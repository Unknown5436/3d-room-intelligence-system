# 3D Room Intelligence System

A production-ready system for processing 3D room scans from iPhone 17 Pro Max + Scaniverse, extracting spatial intelligence (dimensions, objects, relationships), and exposing capabilities via REST API for AI integration.

## Features

- **3D Point Cloud Processing**: Complete pipeline using Open3D
- **Room Analysis**: Automatic dimension extraction, object detection, and classification
- **REST API**: FastAPI-based endpoints for AI integration
- **Spatial Database**: PostgreSQL + PostGIS for spatial data storage
- **Scalable Architecture**: Async processing, connection pooling, optimized algorithms

## Quick Start

### 1. Activate Virtual Environment

```bash
source venv311/bin/activate
```

### 2. Start API Server (requires database)

First, ensure PostgreSQL is running:
```bash
docker-compose up -d postgres
```

### 3. Start API

```bash
uvicorn backend.api.main:app --reload
```

API will be available at: http://localhost:8000
Interactive docs: http://localhost:8000/api/docs

## Project Structure

```
.
├── backend/              # Main application code
│   ├── api/             # FastAPI application and routes
│   ├── processing/      # Point cloud processing modules
│   ├── database/        # Database models and repositories
│   ├── config/          # Configuration management
│   └── utils/           # Utility functions
├── tests/               # Test suite
├── docs/                # Documentation
├── requirements.txt     # Python dependencies
├── docker-compose.yml   # Docker services configuration
└── Dockerfile           # Docker container definition
```

## Installation

See **[docs/README.md](docs/README.md)** for complete installation instructions.

**Quick setup:**
- Python 3.11+ required (for Open3D support)
- Install dependencies: `pip install -r requirements.txt`
- Set up PostgreSQL with PostGIS extensions
- See `docs/` for detailed guides

## API Endpoints

- `POST /api/upload-scan` - Upload and process PLY/SPZ files
- `GET /api/room/{room_id}/dimensions` - Get room dimensions
- `GET /api/room/{room_id}/objects` - Get detected objects
- `GET /api/room/{room_id}/data` - Get complete room data
- `POST /api/room/{room_id}/check-fit` - Check if item fits
- `GET /api/room/{room_id}/optimize` - Layout optimization suggestions
- `GET /api/health` - Health check

## Documentation

All documentation is in the `docs/` folder:

- **[docs/README.md](docs/README.md)** - Documentation index
- **[docs/QUICK_START.md](docs/QUICK_START.md)** - Quick start guide
- **[docs/TESTING.md](docs/TESTING.md)** - Testing instructions
- **[docs/INSTALLATION.md](docs/INSTALLATION.md)** - Installation guide
- **[docs/API.md](docs/API.md)** - Complete API reference
- **[docs/PROJECT.md](docs/PROJECT.md)** - Project architecture and design

## Technology Stack

- **FastAPI** 0.104.0 - Modern async web framework
- **Open3D** 0.19.0 - Point cloud processing
- **PostgreSQL + PostGIS** - Spatial database
- **SQLAlchemy** 2.0.23 - ORM
- **NumPy/SciPy** - Numerical computing

## Requirements

- Python 3.11+ (Open3D support)
- PostgreSQL 12+ with PostGIS extension
- 4GB+ RAM (for point cloud processing)
- Linux/macOS/Windows

## License

See LICENSE file for details.

## Contributing

See CONTRIBUTING.md (if exists) for contribution guidelines.

