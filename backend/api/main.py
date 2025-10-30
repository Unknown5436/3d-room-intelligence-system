"""FastAPI application main module.

Reference: Section E1 for API architecture.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from backend.config import settings
from backend.utils.logger import setup_logging, log_request_time
from backend.api.routes import upload, rooms, analysis

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="3D Room Intelligence API",
    description="iPhone 17 Pro Max + Scaniverse Integration - Room Scanning and Spatial Intelligence System",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request timing middleware
app.middleware("http")(log_request_time)

# Include routers
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(rooms.router, prefix="/api/room", tags=["Rooms"])
app.include_router(analysis.router, prefix="/api/room", tags=["Analysis"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "3D Room Intelligence API",
        "version": "1.0.0",
        "description": "iPhone 17 Pro Max + Scaniverse Integration",
        "endpoints": {
            "docs": "/api/docs",
            "health": "/api/health",
            "upload": "POST /api/upload-scan",
            "room_dimensions": "GET /api/room/{room_id}/dimensions",
            "room_objects": "GET /api/room/{room_id}/objects",
            "room_data": "GET /api/room/{room_id}/data",
            "check_fit": "POST /api/room/{room_id}/check-fit",
            "optimize": "GET /api/room/{room_id}/optimize",
        }
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    # TODO: Add database connectivity check
    # TODO: Add processing queue status
    return {
        "status": "healthy",
        "version": "1.0.0",
        "database": "connected",  # Placeholder - implement actual check
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )
