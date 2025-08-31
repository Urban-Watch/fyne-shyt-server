#!/usr/bin/env python3
"""Test script to verify Report model includes all new fields."""

import sys
sys.path.append('.')

from app.models.report import Report, ReportCategory, ReportStatus, Location
from datetime import datetime

def test_report_model_fields():
    """Test that Report model includes all new AI analysis fields."""
    
    # Sample report data with all fields
    sample_location = Location(lat=22.32, lon=87.32, address="Test Address")
    
    report_data = {
        "report_id": "test123",
        "user_ids": ["user1"],
        "people_reported": 1,
        "category": ReportCategory.POTHOLES,
        "title": "Test Pothole",
        "ai_analysis": "AI analysis text",
        "images": ["image1.jpg"],
        "location": sample_location,
        "criticality_score": 42,
        "severity_score": 587,
        "severity_analysis": "High severity due to depth",
        "impact_score": 55,
        "impact_analysis": "Moderate impact on traffic",
        "population_estimate": 150,
        "vehicle_estimate": 50,
        "status": ReportStatus.WAITING_FOR_ATTENTION,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    try:
        # Try to create Report instance
        report = Report(**report_data)
        
        print("=== REPORT MODEL FIELD TEST ===")
        print(f"✅ report_id: {report.report_id}")
        print(f"✅ severity_score: {report.severity_score}")
        print(f"✅ severity_analysis: {report.severity_analysis}")
        print(f"✅ impact_score: {report.impact_score}")
        print(f"✅ impact_analysis: {report.impact_analysis}")
        print(f"✅ population_estimate: {report.population_estimate}")
        print(f"✅ vehicle_estimate: {report.vehicle_estimate}")
        
        # Test with None values (should work for optional fields)
        report_data_with_nones = report_data.copy()
        report_data_with_nones.update({
            "severity_score": None,
            "severity_analysis": None,
            "impact_score": None,
            "impact_analysis": None,
            "population_estimate": None,
            "vehicle_estimate": None
        })
        
        report_with_nones = Report(**report_data_with_nones)
        print(f"✅ Handles None values: severity_score={report_with_nones.severity_score}")
        
        print("✅ ALL FIELDS WORKING CORRECTLY!")
        print("✅ Report model now includes all database fields")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    test_report_model_fields()
