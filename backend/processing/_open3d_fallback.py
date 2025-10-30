"""Fallback module for Open3D when not available.

This allows the system to start and show a clear error message when processing is attempted.
"""
import logging

logger = logging.getLogger(__name__)

def _check_open3d():
    """Check if Open3D is available."""
    try:
        import open3d
        return True, open3d
    except ImportError:
        return False, None

_has_open3d, _open3d_module = _check_open3d()

if not _has_open3d:
    logger.warning(
        "Open3D is not installed. Point cloud processing will not work.\n"
        "Install Open3D using one of these methods:\n"
        "  1. Use conda: conda install -c open3d-admin open3d\n"
        "  2. Use Python 3.11: python3.11 -m venv venv311 && source venv311/bin/activate && pip install open3d\n"
        "  3. Build from source (see INSTALL_OPEN3D.md)\n"
        "  4. Use Docker with Python 3.11 base image"
    )

