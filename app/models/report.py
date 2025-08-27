from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class ReportCategory(str, Enum):
    POTHOLES = "potholes"
    TRASH_OVERFLOW = "trash_overflow"


class ReportStatus(str, Enum):
    WAITING_FOR_ATTENTION = "waiting_for_attention"
    GOT_THE_ATTENTION = "got_the_attention"
    RESOLVED = "resolved"


class Location(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")
    address: Optional[str] = Field(None, max_length=500)


class ReportBase(BaseModel):
    category: ReportCategory
    title: str = Field(..., min_length=1, max_length=200)
    ai_analysis: Optional[str] = Field(None, max_length=1000)
    images: List[str] = Field(default_factory=list, description="URLs to stored images")
    location: Location
    criticality_score: int = Field(..., ge=1, le=100, description="Criticality score from 1-100")
    status: ReportStatus = ReportStatus.WAITING_FOR_ATTENTION


class ReportCreate(BaseModel):
    location: Location
    # Images will be handled separately in the endpoint


class ReportUpdate(BaseModel):
    status: Optional[ReportStatus] = None
    admin_notes: Optional[str] = Field(None, max_length=1000)


class Report(ReportBase):
    report_id: str
    user_ids: List[str] = Field(default_factory=list, description="List of user IDs who reported this")
    people_reported: int = Field(default=1, ge=1, description="Number of people who reported this")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ReportResponse(BaseModel):
    report_id: str
    category: ReportCategory
    title: str
    status: ReportStatus
    criticality_score: int
    location: Location
    people_reported: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ReportDetailResponse(Report):
    """Detailed report response with all fields"""
    pass


class ReportSummary(BaseModel):
    total_active: int
    by_criticality: dict = Field(default_factory=dict)
    by_status: dict = Field(default_factory=dict)
    by_category: dict = Field(default_factory=dict)


class PaginationResponse(BaseModel):
    total: int
    limit: int
    offset: int
