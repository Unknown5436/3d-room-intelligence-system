"""Application configuration with Pydantic Settings.

Reference: Section C of 3dscanknowledge.md for algorithm parameters.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database Configuration
    database_url: str = "postgresql://room_intel:secure_password@localhost:5432/room_intelligence"
    database_pool_size: int = 20
    database_max_overflow: int = 10
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    
    # File Upload Settings
    max_upload_size: int = 262144000  # 250MB - Section A2: typical room scan size
    upload_directory: str = "./uploads"
    temp_directory: str = "./temp"
    
    # Processing Parameters (Section F1, B1 from knowledge doc)
    voxel_size: float = 0.05  # 5cm voxels - Section F1
    outlier_neighbors: int = 20  # Statistical outlier removal - Section F1
    outlier_std_ratio: float = 2.0  # 2 standard deviations - Section F1
    ransac_distance_threshold: float = 0.01  # 1cm tolerance - Section B1
    ransac_iterations: int = 1000  # RANSAC iterations - Section B1
    dbscan_eps: float = 0.1  # 10cm neighborhood - Section B1
    dbscan_min_samples: int = 50  # Minimum cluster size - Section B1
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/api.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
