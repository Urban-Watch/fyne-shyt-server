from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from datetime import timedelta
from typing import Dict, Any

from app.models.user import User, UserCreate, UserLogin, UserResponse
from app.services.user_service import user_service
from app.core.security import create_access_token
from app.core.config import settings
from app.api.auth.dependencies import get_current_active_user

router = APIRouter(prefix="/user", tags=["User Authentication"])

@router.post("/signup", response_model=Dict[str, Any])
async def signup(user_data: UserCreate):
    """User signup endpoint"""
    try:
        # Check if user already exists
        if await user_service.user_exists(user_data.mobile_no):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this mobile number already exists"
            )
        
        # Create user
        user = await user_service.create_user(user_data)
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.user_id}, 
            expires_delta=access_token_expires
        )
        
        return {
            "status": "success",
            "message": "User created successfully",
            "token": access_token,
            "data": {
                "user_id": user.user_id,
                "name": user.name,
                "phone": user.mobile_no
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

@router.post("/login", response_model=Dict[str, Any])
async def login(user_credentials: UserLogin):
    """User login endpoint"""
    try:
        # Get user by mobile number
        user = await user_service.get_user_by_mobile(user_credentials.mobile_no)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found. Please signup first."
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.user_id}, 
            expires_delta=access_token_expires
        )
        
        return {
            "status": "success",
            "message": "Login successful",
            "token": access_token,
            "data": {
                "user_id": user.user_id,
                "name": user.name,
                "phone": user.mobile_no
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.get("/profile", response_model=Dict[str, Any])
async def get_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user profile"""
    return {
        "status": "success",
        "message": "Profile retrieved successfully",
        "data": {
            "user_id": current_user.user_id,
            "name": current_user.name,
            "phone": current_user.mobile_no,
            "address": current_user.address,
            "created_at": current_user.created_at
        }
    }
