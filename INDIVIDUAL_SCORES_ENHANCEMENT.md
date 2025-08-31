# Individual Score Storage and AI Analysis Enhancement

## Overview
This enhancement adds individual score storage with AI-generated analysis for each score component (severity, impact, criticality) to the Urban Watch system.

## Changes Made

### 1. Database Schema Updates
- **File**: `database_schema.sql`
- **Added columns to reports table**:
  - `severity_score` (INTEGER, 1-1000)
  - `severity_analysis` (TEXT) - AI analysis of severity score
  - `impact_score` (INTEGER, 1-100) 
  - `impact_analysis` (TEXT) - AI analysis of impact score
  - `population_estimate` (INTEGER) - Estimated population in area
  - `vehicle_estimate` (INTEGER) - Estimated vehicle count

### 2. Data Models
- **File**: `app/models/report.py`
- **Updated ReportBase class** to include new optional fields for individual scores and analyses

### 3. AI Processing Enhancement  
- **File**: `app/ai/final.py`
- **Added**: `generate_score_analysis()` function that generates one-line AI analysis for each score type
- Uses Gemini API to analyze images and provide contextual explanations for:
  - Severity scores (1-1000 scale)
  - Impact scores (1-100 scale) 
  - Criticality scores (1-100 scale)

### 4. AI Service Pipeline
- **File**: `app/services/ai_service.py`
- **Enhanced**: `process_report_image()` method to:
  - Generate individual score analyses using the new `generate_score_analysis()` function
  - Include all individual scores and analyses in the final result
  - Provide context-aware analysis for each score component

### 5. Report Service
- **File**: `app/services/report_service.py`
- **Updated**: `create_report()` method to store the new individual score fields in the database

### 6. API Endpoint
- **File**: `app/api/v1/endpoints/reports.py`
- **Enhanced**: `/report-issue` endpoint to:
  - Pass individual scores from AI analysis to report creation
  - Return comprehensive AI analysis including all score breakdowns

### 7. Database Migration
- **File**: `database_migration_add_individual_scores.sql`
- **Created**: Migration script to add new columns to existing reports table

## Features Added

### Individual Score Analysis
Each report now includes:

1. **Severity Analysis**: AI explanation of what the severity score (1-1000) means based on visual damage/impact in the image

2. **Impact Analysis**: AI explanation of what the impact score (1-100) means for community and traffic, considering population and vehicle estimates

3. **Criticality Analysis**: AI explanation of what the criticality score (1-100) means for municipal priority and response urgency

### Enhanced Response Format
The API now returns:
```json
{
  "status": "success",
  "data": {
    "report_id": "...",
    "ai_analysis": {
      "category": "trash_overflow",
      "severity_score": 587,
      "severity_analysis": "AI explanation of severity...",
      "impact_score": 55,
      "impact_analysis": "AI explanation of impact...", 
      "criticality_score": 38,
      "criticality_analysis": "AI explanation of criticality...",
      "population_estimate": 1200,
      "vehicle_estimate": 4180
    }
  }
}
```

## Implementation Details

### Score Analysis Generation
- Uses Gemini API with image + context for each score type
- Generates single-line explanations (max 500 characters)
- Provides fallback error messages if AI generation fails
- Includes relevant context (population, vehicles, location) for each analysis

### Database Storage
- All individual scores and analyses are stored as separate fields
- Maintains backward compatibility with existing reports
- New fields are optional to support existing data

### Error Handling
- Graceful fallback if individual analysis generation fails
- Main processing continues even if individual analyses fail
- Comprehensive logging for debugging

## Testing
- **File**: `test_score_analysis.py` - Test script to verify the new functionality
- Run migration script on database before testing
- Test endpoint with image upload to see individual score analyses

## Migration Steps
1. Run `database_migration_add_individual_scores.sql` in Supabase
2. Deploy updated code
3. Test with new image uploads
4. Verify individual scores and analyses are stored and returned correctly
