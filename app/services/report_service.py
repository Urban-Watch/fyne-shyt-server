from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import uuid
from geopy.distance import geodesic
from app.db.supabase_client import get_supabase_client, get_supabase_service_client
from app.models.report import Report, ReportCreate, ReportUpdate, ReportCategory, ReportStatus, ReportSummary, Location
from app.core.security import generate_random_string
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class ReportService:
    """Service for report database operations"""
    
    def __init__(self):
        self.client = get_supabase_client()
        self.service_client = get_supabase_service_client()
    
    async def create_report(self, user_id: str, report_data: dict) -> Report:
        """Create a new report"""
        try:
            if not self.service_client:
                raise Exception("Supabase service client not available")
                
            report_id = generate_random_string(32)
            now = datetime.utcnow().isoformat()
            
            report_dict = {
                "report_id": report_id,
                "user_ids": [user_id],
                "people_reported": 1,
                "category": report_data["category"],
                "title": report_data["title"],
                "ai_analysis": report_data.get("ai_analysis", ""),
                "images": report_data.get("images", []),
                "location": report_data["location"],
                "criticality_score": report_data["criticality_score"],
                "status": ReportStatus.WAITING_FOR_ATTENTION.value,
                "created_at": now,
                "updated_at": now
            }
            
            result = self.service_client.table("reports").insert(report_dict).execute()
            
            if result.data:
                return Report(**result.data[0])
            else:
                raise Exception("Failed to create report")
                
        except Exception as e:
            logger.error(f"Error creating report: {e}")
            raise
    
    async def get_report_by_id(self, report_id: str) -> Optional[Report]:
        """Get report by ID"""
        try:
            if not self.service_client:
                raise Exception("Supabase service client not available")
            result = self.service_client.table("reports").select("*").eq("report_id", report_id).execute()
            
            if result.data:
                return Report(**result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error getting report by ID {report_id}: {e}")
            return None
    
    async def get_user_reports(
        self, 
        user_id: str, 
        category: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Report], int]:
        """Get reports for a specific user with pagination"""
        try:
            # Use service_client to bypass RLS for user reports
            # For now, let's get all reports and filter in Python
            # This is less efficient but will work while we debug the query
            if not self.service_client:
                raise Exception("Supabase service client not available")
            query = self.service_client.table("reports").select("*")
            
            # Apply filters
            if category:
                query = query.eq("category", category)
            if status:
                query = query.eq("status", status)
            
            # Apply ordering
            query = query.order("created_at", desc=True)
            
            result = query.execute()
            
            if not result.data:
                return [], 0
            
            # Filter reports where user_id is in user_ids array
            user_reports = []
            for report_data in result.data:
                if user_id in report_data.get("user_ids", []):
                    user_reports.append(Report(**report_data))
            
            # Apply pagination manually
            total_count = len(user_reports)
            paginated_reports = user_reports[offset:offset + limit]
            
            return paginated_reports, total_count
            
        except Exception as e:
            logger.error(f"Error getting user reports for {user_id}: {e}")
            return [], 0
    
    async def get_all_reports(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Report], int]:
        """Get all reports with pagination (admin only)"""
        try:
            if not self.service_client:
                raise Exception("Supabase service client not available")
            query = self.service_client.table("reports").select("*", count="exact")
            
            # Apply filters
            if category:
                query = query.eq("category", category)
            if status:
                query = query.eq("status", status)
            
            # Apply pagination and ordering
            query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
            
            result = query.execute()
            
            reports = [Report(**report) for report in result.data] if result.data else []
            total_count = result.count if result.count else 0
            
            return reports, total_count
            
        except Exception as e:
            logger.error(f"Error getting all reports: {e}")
            return [], 0
    
    async def get_priority_reports(self, limit: int = 4) -> List[Report]:
        """Get priority reports sorted by criticality score"""
        try:
            if not self.service_client:
                raise Exception("Supabase service client not available")
            
            # Get all reports with status "waiting_for_attention" sorted by criticality score
            result = self.service_client.table("reports").select("*").eq(
                "status", ReportStatus.WAITING_FOR_ATTENTION.value
            ).order("criticality_score", desc=True).limit(limit).execute()
            
            return [Report(**report) for report in result.data] if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting priority reports: {e}")
            return []
    
    async def update_report_status(
        self, 
        report_id: str, 
        status: ReportStatus,
        admin_notes: Optional[str] = None
    ) -> Optional[Report]:
        """Update report status (admin only)"""
        try:
            update_dict = {
                "status": status.value,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if admin_notes:
                update_dict["admin_notes"] = admin_notes
            if not self.service_client:
                raise Exception("Supabase service client not available")
            result = self.service_client.table("reports").update(update_dict).eq("report_id", report_id).execute()
            
            if result.data:
                return Report(**result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error updating report status {report_id}: {e}")
            return None
    
    async def find_nearby_reports(
        self, 
        location: Location, 
        radius_meters: float = 50.0,
        category: Optional[str] = None
    ) -> List[Report]:
        """Find reports within specified radius"""
        try:
            # Get all reports in the general area (we'll filter by exact distance in Python)
            # This is a simplified approach - in production, you'd want to use PostGIS for better performance
            if not self.service_client:
                raise Exception("Supabase service client not available")
            query = self.service_client.table("reports").select("*")
            
            if category:
                query = query.eq("category", category)
            
            # Only get reports that are not resolved
            query = query.neq("status", ReportStatus.RESOLVED.value)
            
            result = query.execute()
            
            if not result.data:
                return []
            
            nearby_reports = []
            target_point = (location.lat, location.lon)
            
            for report_data in result.data:
                report = Report(**report_data)
                report_point = (report.location.lat, report.location.lon)
                
                # Calculate distance using geopy
                distance = geodesic(target_point, report_point).meters
                
                if distance <= radius_meters:
                    nearby_reports.append(report)
            
            return nearby_reports
            
        except Exception as e:
            logger.error(f"Error finding nearby reports: {e}")
            return []
    
    async def merge_reports(self, existing_report: Report, new_report_data: dict, new_user_id: str) -> Report:
        """Merge a new report into an existing one"""
        try:
            # Update existing report
            updated_user_ids = list(set(existing_report.user_ids + [new_user_id]))
            updated_images = existing_report.images + new_report_data.get("images", [])
            people_reported = len(updated_user_ids)
            
            # Recalculate criticality score based on number of people and max of individual scores
            base_criticality = max(existing_report.criticality_score, new_report_data.get("criticality_score", 0))
            crowd_factor = min(people_reported * 5, 30)  # Up to 30 points for crowd reporting
            new_criticality = min(100, base_criticality + crowd_factor)
            
            update_dict = {
                "user_ids": updated_user_ids,
                "people_reported": people_reported,
                "images": updated_images,
                "criticality_score": new_criticality,
                "updated_at": datetime.utcnow().isoformat()
            }
            if not self.service_client:
                raise Exception("Supabase service client not available")
            result = self.service_client.table("reports").update(update_dict).eq("report_id", existing_report.report_id).execute()
            
            if result.data:
                return Report(**result.data[0])
            else:
                raise Exception("Failed to merge reports")
                
        except Exception as e:
            logger.error(f"Error merging reports: {e}")
            raise
    
    async def delete_report(self, report_id: str) -> bool:
        """Delete a report by ID"""
        try:
            if not self.service_client:
                raise Exception("Supabase service client not available")
                
            result = self.service_client.table("reports").delete().eq("report_id", report_id).execute()
            return True
            
        except Exception as e:
            logger.error(f"Error deleting report {report_id}: {e}")
            return False

    async def delete_user_reports(self, user_id: str) -> bool:
        """Delete all reports created by a specific user"""
        try:
            if not self.service_client:
                raise Exception("Supabase service client not available")
                
            # Get all reports where user_id is in user_ids array
            result = self.service_client.table("reports").select("*").execute()
            
            if not result.data:
                return True
            
            # Filter and delete reports where user_id is in user_ids array
            reports_to_delete = []
            for report_data in result.data:
                if user_id in report_data.get("user_ids", []):
                    reports_to_delete.append(report_data["report_id"])
            
            # Delete each report
            for report_id in reports_to_delete:
                await self.delete_report(report_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user reports for user {user_id}: {e}")
            return False

    async def get_reports_summary(self) -> ReportSummary:
        """Get reports summary statistics"""
        try:
            if not self.service_client:
                raise Exception("Supabase service client not available")
                
            # Get all reports for processing
            result = self.service_client.table("reports").select("*").execute()
            
            if not result.data:
                return ReportSummary(
                    total_active=0,
                    by_criticality={"low": 0, "medium": 0, "high": 0},
                    by_status={"waiting_for_attention": 0, "got_the_attention": 0},
                    by_category={"potholes": 0, "trash_overflow": 0}
                )
            
            reports = result.data
            total_active = len(reports)
            
            # Count by criticality
            by_criticality = {"low": 0, "medium": 0, "high": 0}
            for report in reports:
                score = report.get("criticality_score", 0)
                if score < 40:
                    by_criticality["low"] += 1
                elif score < 70:
                    by_criticality["medium"] += 1
                else:
                    by_criticality["high"] += 1
            
            # Count by status
            by_status = {"waiting_for_attention": 0, "got_the_attention": 0}
            for report in reports:
                status = report.get("status", "")
                if status in by_status:
                    by_status[status] += 1
            
            # Count by category
            by_category = {"potholes": 0, "trash_overflow": 0}
            for report in reports:
                category = report.get("category", "")
                if category in by_category:
                    by_category[category] += 1
            
            return ReportSummary(
                total_active=total_active,
                by_criticality=by_criticality,
                by_status=by_status,
                by_category=by_category
            )
            
        except Exception as e:
            logger.error(f"Error getting reports summary: {e}")
            # Return empty summary if error
            return ReportSummary(
                total_active=0,
                by_criticality={"low": 0, "medium": 0, "high": 0},
                by_status={"waiting_for_attention": 0, "got_the_attention": 0},
                by_category={"potholes": 0, "trash_overflow": 0}
            )

# Global report service instance
report_service = ReportService()
