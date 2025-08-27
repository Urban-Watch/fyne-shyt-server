from supabase.client import create_client, Client
from app.core.config import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Global Supabase client instance
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Optional[Client]:
    """Get or create Supabase client instance"""
    global _supabase_client
    
    if _supabase_client is None:
        try:
            # Check if we have valid Supabase configuration
            if (settings.SUPABASE_URL.startswith("https://") and 
                "supabase.co" in settings.SUPABASE_URL and
                len(settings.SUPABASE_KEY) > 50):
                
                _supabase_client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_KEY
                )
                logger.info("Supabase client initialized successfully")
            else:
                logger.warning("Supabase configuration incomplete - using mock client")
                return None
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            return None
    
    return _supabase_client


def get_supabase_service_client() -> Optional[Client]:
    """Get Supabase client with service key for admin operations"""
    try:
        # Check if we have valid Supabase configuration
        if (settings.SUPABASE_URL.startswith("https://") and 
            "supabase.co" in settings.SUPABASE_URL and
            len(settings.SUPABASE_SERVICE_KEY) > 50):
            
            return create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
        else:
            logger.warning("Supabase service configuration incomplete")
            return None
    except Exception as e:
        logger.error(f"Failed to initialize Supabase service client: {e}")
        return None


# Convenience instance (may be None if not configured)
supabase_client = get_supabase_client()
