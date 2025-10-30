"""Logging configuration and middleware.

Provides structured logging for the application.
"""
import logging
import sys
from pathlib import Path
from typing import Callable
import time

from backend.config import settings


def setup_logging() -> None:
    """Configure application logging."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    log_file_path = Path(settings.log_file)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file_path),
            logging.StreamHandler(sys.stdout),
        ],
    )
    
    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger: Configured logger instance
    """
    return logging.getLogger(name)


# Request/response logging middleware (to be used in FastAPI)
async def log_request_time(request, call_next: Callable):
    """Middleware to log request processing time."""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    # Log slow requests (>1 second)
    if process_time > 1.0:
        logging.warning(
            f"Slow request: {request.method} {request.url.path} took {process_time:.2f}s"
        )
    
    return response
