from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, Optional

from app.models.report import ReportUpdate, ReportStatus
from app.services.report_service import report_service
from app.services.user_service import user_service
from app.db.redis_client import cache_service
from app.core.config import settings

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/priority-reports", response_model=Dict[str, Any])
async def get_priority_reports():
    """Get top 4 priority reports sorted by criticality score"""
    try:
        # Check cache first
        cache_key = "admin:priority_reports"
        cached_result = await cache_service.get(cache_key)
        
        if cached_result:
            return cached_result
        
        # Get priority reports (top 4 by criticality score)
        priority_reports = await report_service.get_priority_reports()
        
        response_data = {
            "status": "success",
            "message": "Priority reports retrieved successfully",
            "data": {
                "priority_reports": [
                    {
                        "report_id": report.report_id,
                        "title": report.title,
                        "criticality_score": report.criticality_score,
                        "people_reported": report.people_reported,
                        "location": report.location.dict(),
                        "category": report.category,
                        "created_at": report.created_at
                    }
                    for report in priority_reports
                ]
            }
        }
        
        # Cache the result
        await cache_service.set(cache_key, response_data, settings.CACHE_TTL_PRIORITY_REPORTS)
        
        return response_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve priority reports"
        )

@router.get("/reports", response_model=Dict[str, Any])
async def get_all_reports(
    status_filter: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get all reports with filtering and pagination (admin only)"""
    try:
        # Check cache first
        cache_key = f"admin:reports:{status_filter}:{category}:{limit}:{offset}"
        cached_result = await cache_service.get(cache_key)
        
        if cached_result:
            return cached_result
        
        # Get reports from database
        reports, total_count = await report_service.get_all_reports(
            category=category,
            status=status_filter,
            limit=limit,
            offset=offset
        )
        
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
                        "people_reported": report.people_reported,
                        "location": report.location.dict(),
                        "created_at": report.created_at,
                        "updated_at": report.updated_at
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
        await cache_service.set(cache_key, response_data, 300)  # 5 minutes cache
        
        return response_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve reports"
        )

@router.get("/reports/summary", response_model=Dict[str, Any])
async def get_reports_summary():
    """Get reports summary statistics (admin only)"""
    try:
        # Check cache first
        cache_key = "admin:reports_summary"
        cached_result = await cache_service.get(cache_key)
        
        if cached_result:
            return cached_result
        
        # Get summary from database
        summary = await report_service.get_reports_summary()
        
        response_data = {
            "status": "success",
            "message": "Summary retrieved successfully",
            "data": {
                "total_active": summary.total_active,
                "by_criticality": {
                    "low": summary.by_criticality.get("low", 0),
                    "medium": summary.by_criticality.get("medium", 0),
                    "high": summary.by_criticality.get("high", 0)
                },
                "by_status": {
                    "waiting_for_attention": summary.by_status.get("waiting_for_attention", 0),
                    "got_the_attention": summary.by_status.get("got_the_attention", 0)
                },
                "by_category": {
                    "potholes": summary.by_category.get("potholes", 0),
                    "trash_overflow": summary.by_category.get("trash_overflow", 0)
                }
            }
        }
        
        # Cache the result
        await cache_service.set(cache_key, response_data, settings.CACHE_TTL_REPORTS_SUMMARY)
        
        return response_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve summary"
        )

@router.get("/reports/{report_id}", response_model=Dict[str, Any])
async def get_report_by_id(
    report_id: str
):
    """Get detailed report by ID (admin only)"""
    try:
        report = await report_service.get_report_by_id(report_id)
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        return {
            "status": "success",
            "message": "Report retrieved successfully",
            "data": {
                "report": {
                    "report_id": report.report_id,
                    "user_ids": report.user_ids,
                    "people_reported": report.people_reported,
                    "category": report.category,
                    "title": report.title,
                    "ai_analysis": report.ai_analysis,
                    "images": report.images,
                    "location": report.location.dict(),
                    "criticality_score": report.criticality_score,
                    "status": report.status,
                    "created_at": report.created_at,
                    "updated_at": report.updated_at
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve report"
        )

@router.put("/reports/{report_id}/status", response_model=Dict[str, Any])
async def update_report_status(
    report_id: str,
    update_data: ReportUpdate
):
    """Update report status (admin only)"""
    try:
        # Check if report exists
        existing_report = await report_service.get_report_by_id(report_id)
        if not existing_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Update report status
        updated_report = None
        if update_data.status:
            updated_report = await report_service.update_report_status(
                report_id=report_id,
                status=update_data.status,
                admin_notes=update_data.admin_notes
            )
        
        if not updated_report:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update report status"
            )
        
        # Invalidate relevant caches
        cache_keys = [
            "admin:priority_reports",
            "admin:reports_summary",
            f"admin:reports:*"  # All admin report caches
        ]
        
        for key in cache_keys:
            if "*" not in key:
                await cache_service.delete(key)
        
        return {
            "status": "success",
            "message": "Report status updated successfully",
            "data": {
                "report": {
                    "report_id": updated_report.report_id,
                    "status": updated_report.status,
                    "updated_at": updated_report.updated_at
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update report status"
        )

@router.delete("/reports/{report_id}", response_model=Dict[str, Any])
async def delete_report(report_id: str):
    """Delete a specific report (admin only)"""
    try:
        # Check if report exists
        existing_report = await report_service.get_report_by_id(report_id)
        if not existing_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Delete the report
        success = await report_service.delete_report(report_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete report"
            )
        
        # Invalidate relevant caches
        cache_keys = [
            "admin:priority_reports",
            "admin:reports_summary",
        ]
        
        for key in cache_keys:
            await cache_service.delete(key)
        
        return {
            "status": "success",
            "message": "Report deleted successfully",
            "data": {
                "report_id": report_id
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete report"
        )

@router.delete("/users/{user_id}", response_model=Dict[str, Any])
async def delete_user(user_id: str):
    """Delete a user and all their reports (admin only)"""
    try:
        # Check if user exists
        existing_user = await user_service.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Delete all user's reports first
        reports_deleted = await report_service.delete_user_reports(user_id)
        
        # Delete the user
        user_deleted = await user_service.delete_user(user_id)
        
        if not user_deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user"
            )
        
        # Invalidate relevant caches
        cache_keys = [
            "admin:priority_reports",
            "admin:reports_summary",
        ]
        
        for key in cache_keys:
            await cache_service.delete(key)
        
        return {
            "status": "success",
            "message": "User and associated reports deleted successfully",
            "data": {
                "user_id": user_id,
                "reports_deleted": reports_deleted
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )

@router.delete("/users/mobile/{mobile_no}", response_model=Dict[str, Any])
async def delete_user_by_mobile(mobile_no: str):
    """Delete a user by mobile number and all their reports (admin only)"""
    try:
        # Get user by mobile number
        existing_user = await user_service.get_user_by_mobile(mobile_no)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Delete all user's reports first
        reports_deleted = await report_service.delete_user_reports(existing_user.user_id)
        
        # Delete the user
        user_deleted = await user_service.delete_user(existing_user.user_id)
        
        if not user_deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user"
            )
        
        # Invalidate relevant caches
        cache_keys = [
            "admin:priority_reports",
            "admin:reports_summary",
        ]
        
        for key in cache_keys:
            await cache_service.delete(key)
        
        return {
            "status": "success",
            "message": "User and associated reports deleted successfully",
            "data": {
                "user_id": existing_user.user_id,
                "mobile_no": mobile_no,
                "reports_deleted": reports_deleted
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )
