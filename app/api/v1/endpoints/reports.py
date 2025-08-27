from fastapi import APIRouter, Depends, HTTPException, status as http_status, File, UploadFile, Form
from typing import Dict, Any, Optional, List
import logging

from app.models.report import ReportCreate, ReportResponse, ReportDetailResponse, Location, PaginationResponse
from app.models.user import User
from app.services.report_service import report_service
from app.services.image_service import image_service
from app.api.auth.dependencies import get_current_active_user
from app.db.redis_client import cache_service
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Reports"])

@router.post("/report-issue", response_model=Dict[str, Any])
async def report_issue(
    image: UploadFile = File(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    address: Optional[str] = Form(default="RK D130 IIT KGP"),
    current_user: User = Depends(get_current_active_user)
):
    """Report a new issue with image and location"""
    try:
        # Validate latitude and longitude ranges
        if not (-90 <= latitude <= 90):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Latitude must be between -90 and 90"
            )
        if not (-180 <= longitude <= 180):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Longitude must be between -180 and 180"
            )
        
        # Create location object
        location_obj = Location(lat=latitude, lon=longitude, address=address)
        
        # Read image data once at the beginning for both upload and AI processing
        image_data = await image.read()
        logger.info(f"Read image data: {len(image_data)} bytes")
        
        # Upload image to Supabase storage and get URL
        image_url = await image_service.save_image_from_data(image, image_data)

        # Process image through AI pipeline
        try:
            from app.services.ai_service import ai_service
            from app.services.report_service import report_service
            from app.core.security import generate_random_string

            # Validate image data is not empty
            if not image_data or len(image_data) == 0:
                # Clean up uploaded image if validation fails
                logger.error("Image data is empty, cleaning up")
                await image_service.delete_from_supabase(image_url)
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail="Uploaded image is empty or invalid"
                )

            # Validate image size (max 10MB)
            max_size = 10 * 1024 * 1024  # 10MB
            if len(image_data) > max_size:
                # Clean up uploaded image if validation fails
                logger.error(f"Image too large: {len(image_data)} bytes, cleaning up")
                await image_service.delete_from_supabase(image_url)
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail="Image size exceeds maximum limit of 10MB"
                )

            logger.info("Image validation passed, proceeding to AI processing")

            # Run AI analysis
            ai_result = await ai_service.process_report_image(
                image_data=image_data,
                latitude=latitude,
                longitude=longitude,
                address=address or "Unknown location",
                age_seconds=0,  # New report, so age is 0
                report_count=1  # First report of this issue
            )

            # Create report with AI analysis results
            report_data = {
                "report_id": generate_random_string(32),
                "user_ids": [current_user.user_id],
                "people_reported": 1,
                "category": ai_result["category"],
                "title": ai_result["title"],
                "ai_analysis": ai_result["description"],
                "images": [image_url],
                "location": location_obj.dict(),
                "criticality_score": ai_result["criticality_score"],
                "status": "waiting_for_attention"
            }

            # Create report in database
            logger.info("Creating report in database")
            report = await report_service.create_report(current_user.user_id, report_data)

            if not report:
                # Clean up uploaded image if report creation fails
                logger.error("Report creation failed, cleaning up uploaded image")
                await image_service.delete_from_supabase(image_url)
                raise HTTPException(
                    status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create report"
                )

            logger.info(f"Report created successfully: {report.report_id}")

            return {
                "status": "success",
                "message": "Issue reported and analyzed successfully",
                "data": {
                    "report_id": report.report_id,
                    "ai_analysis": {
                        "category": ai_result["category"],
                        "severity_score": ai_result["severity_score"],
                        "criticality_score": ai_result["criticality_score"],
                        "title": ai_result["title"]
                    }
                }
            }

        except Exception as e:
            # Clean up uploaded image if any error occurs
            logger.error(f"Processing failed, attempting to clean up image: {image_url}")
            logger.error(f"Error details: {str(e)}")
            await image_service.delete_from_supabase(image_url)
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process report: {str(e)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to report issue"
        )

@router.get("/get-reports", response_model=Dict[str, Any])
async def get_reports(
    category: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user)
):
    """Get user's reports with filtering and pagination"""
    try:
        # Check cache first
        cache_key = f"user:{current_user.user_id}:reports:{category}:{status}:{limit}:{offset}"
        cached_result = await cache_service.get(cache_key)
        
        if cached_result:
            return cached_result
        
        # Get reports from database
        reports, total_count = await report_service.get_user_reports(
            user_id=current_user.user_id,
            category=category,
            status=status,
            limit=limit,
            offset=offset
        )
        
        # Format response
        response_data = {
            "status": "success",
            "message": "Reports retrieved successfully",
            "data": {
                "reports": [
                    {
                        "report_id": report.report_id,
                        "category": report.category,
                        "title": report.title,
                        "status": report.status,
                        "criticality_score": report.criticality_score,
                        "location": report.location.dict(),
                        "people_reported": report.people_reported,
                        "created_at": report.created_at
                    }
                    for report in reports
                ],
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset
                }
            }
        }
        
        # Cache the result
        await cache_service.set(cache_key, response_data, settings.CACHE_TTL_USER_REPORTS)
        
        return response_data
        
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve reports"
        )
