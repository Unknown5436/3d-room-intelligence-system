# Documentation

Complete documentation for the 3D Room Intelligence System.

## Getting Started

- **[QUICK_START.md](QUICK_START.md)** - Get running in minutes
- **[INSTALLATION.md](INSTALLATION.md)** - Complete installation guide

## Guides

- **[PROJECT.md](PROJECT.md)** - Complete project documentation (architecture, design, algorithms)
- **[TESTING.md](TESTING.md)** - Testing and validation guide
- **[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)** - Complete integration guide for other projects
- **[QUICK_INTEGRATION.md](QUICK_INTEGRATION.md)** - Quick start for using this API in other projects


## Quick Reference

### Common Commands

```bash
# Activate environment
source venv311/bin/activate

# Run tests
pytest -v

# Start API (requires database)
docker-compose up -d postgres  # Start database first
uvicorn backend.api.main:app --reload
```

### File Locations

- **Main README**: `../README.md`
- **Configuration**: `../backend/config/settings.py`
- **API Code**: `../backend/api/`
- **Processing**: `../backend/processing/`
- **Database**: `../backend/database/`

## Need Help?

1. Check **[QUICK_START.md](QUICK_START.md)** for common operations
2. Review **[INSTALLATION.md](INSTALLATION.md)** for setup issues
3. See **[TESTING.md](TESTING.md)** for testing procedures
