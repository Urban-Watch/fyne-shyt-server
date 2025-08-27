from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import re


class UserBase(BaseModel):
    mobile_no: str = Field(..., description="10-digit mobile number")
    name: str = Field(..., min_length=1, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    
    @validator('mobile_no')
    def validate_mobile_no(cls, v):
        if not re.match(r'^\d{10}$', v):
            raise ValueError('Mobile number must be exactly 10 digits')
        return v


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    address: Optional[str] = Field(None, max_length=500)


class User(UserBase):
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    user_id: str
    name: str
    mobile_no: str
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    mobile_no: str = Field(..., description="10-digit mobile number")
    
    @validator('mobile_no')
    def validate_mobile_no(cls, v):
        if not re.match(r'^\d{10}$', v):
            raise ValueError('Mobile number must be exactly 10 digits')
        return v
