from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Urban Watch API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Urban Watch Backend API for reporting and managing urban issues"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_DB: int = 0
    
    # Cache TTL (seconds)
    CACHE_TTL_USER_REPORTS: int = 300  # 5 minutes
    CACHE_TTL_PRIORITY_REPORTS: int = 180  # 3 minutes
    CACHE_TTL_REPORTS_SUMMARY: int = 600  # 10 minutes
    CACHE_TTL_NEARBY_REPORTS: int = 900  # 15 minutes
    CACHE_TTL_USER_PROFILE: int = 1800  # 30 minutes
    
    # AI Models Configuration
    POTHOLE_MODEL_PATH: str = "app/ai/models/pothole.pt"
    TRASH_MODEL_PATH: str = "app/ai/models/trash_new.pt"
    
    # Image Upload Configuration
    MAX_IMAGE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_TYPES: list = ["image/jpeg", "image/png", "image/webp"]
    SUPABASE_STORAGE_BUCKET: str = "issues_bucket"
    
    # Geospatial Configuration
    CLUSTERING_RADIUS_METERS: float = 50.0
    
    # Queue Configuration
    REPORT_QUEUE_NAME: str = "report_queue"
    QUEUE_PROCESSING_INTERVAL: int = 1  # seconds
    
    GOOGLE_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
