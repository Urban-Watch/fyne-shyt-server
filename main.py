from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import asyncio
import os

from app.core.config import settings
from app.api.v1.api import api_router
from app.db.redis_client import close_redis_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Urban Watch API...")
    
    # Start background queue processor
    # queue_task = asyncio.create_task(queue_processor.start())
    logger.info("Queue processor disabled temporarily")
    
    try:
        yield
    finally:
        # Shutdown
        logger.info("Shutting down Urban Watch API...")
        
        # Stop queue processor
        # await queue_processor.stop()
        # queue_task.cancel()
        logger.info("Queue processor was disabled")
        
        # Close Redis connection
        await close_redis_client()

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for serving images (disabled since using Supabase storage)
# app.mount("/images", StaticFiles(directory=settings.UPLOAD_DIR), name="images")

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "message": "Urban Watch API",
        "version": settings.VERSION,
        "status": "running"
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.VERSION
    }
