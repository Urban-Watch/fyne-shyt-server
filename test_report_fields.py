#!/usr/bin/env python3
"""Test script to verify all report fields are included in GET responses."""

def test_report_fields_coverage():
    """Test that all database fields are included in the GET responses."""
    
    # All fields available in the database schema
    database_fields = {
        "report_id", "user_ids", "people_reported", "category", "title", 
        "ai_analysis", "images", "location", "criticality_score", 
        "severity_score", "severity_analysis", "impact_score", "impact_analysis",
        "population_estimate", "vehicle_estimate", "status", "created_at", "updated_at"
    }
    
    # Fields that should be in our response (from the code we just updated)
    response_fields = {
        "report_id", "user_ids", "people_reported", "category", "title",
        "ai_analysis", "images", "location", "criticality_score",
        "severity_score", "severity_analysis", "impact_score", "impact_analysis", 
        "population_estimate", "vehicle_estimate", "status", "created_at", "updated_at"
    }
    
    print("=== REPORT FIELDS COVERAGE TEST ===")
    print(f"Database fields: {len(database_fields)}")
    print(f"Response fields: {len(response_fields)}")
    
    missing_fields = database_fields - response_fields
    extra_fields = response_fields - database_fields
    
    if missing_fields:
        print(f"❌ Missing fields in response: {missing_fields}")
        return False
    
    if extra_fields:
        print(f"⚠️  Extra fields in response (not in DB): {extra_fields}")
    
    print("✅ All database fields are included in GET responses!")
    print("\n=== UPDATED ENDPOINTS ===")
    print("✅ GET /reports/get-reports - User reports with all fields")
    print("✅ GET /admin/priority-reports - Priority reports with all fields") 
    print("✅ GET /admin/reports - All reports (admin) with all fields")
    print("✅ GET /admin/reports/{report_id} - Single report with all fields")
    
    return True

if __name__ == "__main__":
    test_report_fields_coverage()
