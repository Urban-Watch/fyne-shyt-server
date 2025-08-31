"""
Test script to verify the new individual score analysis functionality
"""
import os
import sys
import asyncio
from PIL import Image
import io
import tempfile

# Add the app directory to path
sys.path.append('.')

from app.ai.final import generate_score_analysis
from app.services.ai_service import ai_service

async def test_individual_score_analysis():
    """Test the new individual score analysis functions"""
    
    print("=== TESTING INDIVIDUAL SCORE ANALYSIS ===")
    
    # Create a simple test image
    test_image = Image.new('RGB', (100, 100), color='red')
    
    # Test severity analysis
    print("\n1. Testing Severity Analysis:")
    severity_analysis = generate_score_analysis(
        score_type="severity",
        score_value=587,
        image=test_image,
        address="IIT Main Rd, Kharagpur, West Bengal"
    )
    print(f"Severity Analysis: {severity_analysis}")
    
    # Test impact analysis
    print("\n2. Testing Impact Analysis:")
    impact_analysis = generate_score_analysis(
        score_type="impact", 
        score_value=55,
        image=test_image,
        address="IIT Main Rd, Kharagpur, West Bengal",
        additional_context={
            'population_estimate': 1200,
            'vehicle_estimate': 4180
        }
    )
    print(f"Impact Analysis: {impact_analysis}")
    
    # Test criticality analysis
    print("\n3. Testing Criticality Analysis:")
    criticality_analysis = generate_score_analysis(
        score_type="criticality",
        score_value=38,
        image=test_image,
        address="IIT Main Rd, Kharagpur, West Bengal",
        additional_context={
            'severity_score': 587,
            'impact_score': 55
        }
    )
    print(f"Criticality Analysis: {criticality_analysis}")
    
    print("\n=== TEST COMPLETED ===")

if __name__ == "__main__":
    asyncio.run(test_individual_score_analysis())
