from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from app.db.supabase_client import get_supabase_client, get_supabase_service_client
from app.models.user import User, UserCreate, UserUpdate
from app.core.security import generate_random_string
import logging

logger = logging.getLogger(__name__)

class UserService:
    """Service for user database operations"""
    
    def __init__(self):
        self.client = get_supabase_client()
        self.service_client = get_supabase_service_client()
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        try:
            # Use service client for user creation to bypass RLS policies
            if not self.service_client:
                raise Exception("Supabase service client not available")
                
            user_id = generate_random_string(32)
            now = datetime.utcnow().isoformat()
            
            user_dict = {
                "user_id": user_id,
                "mobile_no": user_data.mobile_no,
                "name": user_data.name,
                "address": user_data.address,
                "created_at": now,
                "updated_at": now
            }
            
            result = self.service_client.table("users").insert(user_dict).execute()
            
            if result.data:
                return User(**result.data[0])
            else:
                raise Exception("Failed to create user")
                
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            # Use service client for authentication operations to bypass RLS
            if not self.service_client:
                raise Exception("Supabase service client not available")
                
            result = self.service_client.table("users").select("*").eq("user_id", user_id).execute()
            
            if result.data:
                return User(**result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            return None
    
    async def get_user_by_mobile(self, mobile_no: str) -> Optional[User]:
        """Get user by mobile number"""
        try:
            # Use service client for login operations to bypass RLS
            if not self.service_client:
                raise Exception("Supabase service client not available")
                
            result = self.service_client.table("users").select("*").eq("mobile_no", mobile_no).execute()
            
            if result.data:
                return User(**result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by mobile {mobile_no}: {e}")
            return None
    
    async def update_user(self, user_id: str, user_data: UserUpdate) -> Optional[User]:
        """Update user information"""
        try:
            if not self.client:
                raise Exception("Supabase client not available")
                
            update_dict = user_data.dict(exclude_unset=True)
            update_dict["updated_at"] = datetime.utcnow().isoformat()
            
            result = self.client.table("users").update(update_dict).eq("user_id", user_id).execute()
            
            if result.data:
                return User(**result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            return None
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user (admin only)"""
        try:
            if not self.service_client:
                raise Exception("Supabase service client not available")
                
            result = self.service_client.table("users").delete().eq("user_id", user_id).execute()
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False
    
    async def user_exists(self, mobile_no: str) -> bool:
        """Check if user exists by mobile number"""
        user = await self.get_user_by_mobile(mobile_no)
        return user is not None

# Global user service instance
user_service = UserService()
