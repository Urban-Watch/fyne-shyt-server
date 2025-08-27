from redis.asyncio import Redis
import json
from typing import Any, Optional, Union
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Global Redis client instance
_redis_client: Optional[Redis] = None

async def get_redis_client() -> Redis:
    """Get or create Redis client instance"""
    global _redis_client
    
    if _redis_client is None:
        try:
            _redis_client = Redis.from_url(
                settings.REDIS_URL,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            # Test connection
            await _redis_client.ping()
            logger.info("Redis client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            raise
    
    return _redis_client

async def close_redis_client():
    """Close Redis client connection"""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None

class CacheService:
    """Redis cache service for storing and retrieving cached data"""
    
    def __init__(self):
        self.client: Optional[Redis] = None
    
    async def init(self):
        """Initialize Redis client"""
        self.client = await get_redis_client()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if not self.client:
                await self.init()
            if not self.client:
                raise RuntimeError("Redis client not initialized")
            
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL"""
        try:
            if not self.client:
                await self.init()
            if not self.client:
                raise RuntimeError("Redis client not initialized")
            
            await self.client.setex(key, ttl, json.dumps(value, default=str))
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            if not self.client:
                await self.init()
            if not self.client:
                raise RuntimeError("Redis client not initialized")
            
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            if not self.client:
                await self.init()
            if not self.client:
                raise RuntimeError("Redis client not initialized")
            
            result = await self.client.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False

class QueueService:
    """Redis queue service for background task processing"""
    
    def __init__(self):
        self.client: Optional[Redis] = None
    
    async def init(self):
        """Initialize Redis client"""
        self.client = await get_redis_client()
    
    async def enqueue(self, queue_name: str, data: dict) -> bool:
        """Add item to queue"""
        try:
            if not self.client:
                await self.init()
            if not self.client:
                raise RuntimeError("Redis client not initialized")
            
            await self.client.rpush(queue_name, json.dumps(data, default=str))
            return True
        except Exception as e:
            logger.error(f"Queue enqueue error for {queue_name}: {e}")
            return False
    
    async def dequeue(self, queue_name: str, timeout: int = 1) -> Optional[dict]:
        """Remove and return item from queue"""
        try:
            if not self.client:
                await self.init()
            if not self.client:
                raise RuntimeError("Redis client not initialized")
            
            result = await self.client.blpop(queue_name, timeout=timeout)
            if result:
                _, data = result
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Queue dequeue error for {queue_name}: {e}")
            return None
    
    async def get_queue_length(self, queue_name: str) -> int:
        """Get queue length"""
        try:
            if not self.client:
                await self.init()
            if not self.client:
                raise RuntimeError("Redis client not initialized")
            
            result = await self.client.llen(queue_name)
            return result
        except Exception as e:
            logger.error(f"Queue length error for {queue_name}: {e}")
            return 0

# Global instances
cache_service = CacheService()
queue_service = QueueService()
