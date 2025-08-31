import sys
sys.path.append('.')

try:
    from app.ai.final import generate_score_analysis
    print("✓ generate_score_analysis imported successfully")
    
    from app.services.ai_service import ai_service  
    print("✓ ai_service imported successfully")
    
    from app.models.report import ReportBase
    print("✓ ReportBase model imported successfully")
    
    print("\n=== ALL IMPORTS SUCCESSFUL ===")
    print("Individual score analysis enhancement is ready!")
    
except Exception as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
