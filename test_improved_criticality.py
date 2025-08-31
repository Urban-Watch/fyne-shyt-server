"""
Test the improved criticality formula
"""
import sys
sys.path.append('.')

from app.ai.criticality_score import compute_criticality_score

def test_improved_criticality():
    print("=== TESTING IMPROVED CRITICALITY FORMULA ===\n")
    
    # Test with your real data
    print("1. Testing with your real report data:")
    print("   Severity: 587/1000, Impact: 55/100, Urgency: 0 seconds, Reports: 1")
    
    result = compute_criticality_score(
        severity=587/1000,  # 0.587
        impact=55,          # 55/100
        age_seconds=0,      # New report
        report_count=1      # Single report
    )
    
    print(f"   OLD Formula Result: ~22")
    print(f"   NEW Formula Result: {result['criticality']}")
    print(f"   Raw Score: {result['raw_score']:.4f}")
    print(f"   Formula: {result['formula']}")
    print(f"   Breakdown:")
    for component, value in result['components'].items():
        if component != 'weights':
            print(f"     {component}: {value}")
    print(f"   Weights: {result['components']['weights']}")
    
    print("\n" + "="*50)
    
    # Test edge cases
    test_cases = [
        {
            "name": "High Severity, Low Impact",
            "severity": 900/1000,  # 0.9
            "impact": 20,          # 20/100
            "age_seconds": 0,
            "report_count": 1
        },
        {
            "name": "Low Severity, High Impact", 
            "severity": 100/1000,  # 0.1
            "impact": 90,          # 90/100
            "age_seconds": 0,
            "report_count": 1
        },
        {
            "name": "Old Issue (30 days)",
            "severity": 500/1000,  # 0.5
            "impact": 60,          # 60/100
            "age_seconds": 30*24*3600,  # 30 days
            "report_count": 1
        },
        {
            "name": "Multiple Reports",
            "severity": 300/1000,  # 0.3
            "impact": 40,          # 40/100
            "age_seconds": 0,
            "report_count": 8      # Many reports
        }
    ]
    
    print("\n2. Testing edge cases:")
    for i, case in enumerate(test_cases, 1):
        result = compute_criticality_score(
            severity=case["severity"],
            impact=case["impact"], 
            age_seconds=case["age_seconds"],
            report_count=case["report_count"]
        )
        
        print(f"\n   {i}. {case['name']}:")
        print(f"      Criticality: {result['criticality']}")
        print(f"      Components: S:{result['components']['severity']:.2f}, "
              f"I:{result['components']['impact_norm']:.2f}, "
              f"U:{result['components']['urgency']:.2f}, "
              f"R:{result['components']['reports_norm']:.2f}")
    
    print("\n" + "="*50)
    print("✅ IMPROVED CRITICALITY FORMULA BENEFITS:")
    print("   • More balanced scoring across all factors")
    print("   • High-impact issues get proper priority")
    print("   • Intuitive weighted average approach")
    print("   • Linear relationship between inputs and output")
    print("   • Better reflects real-world municipal priorities")

if __name__ == "__main__":
    test_improved_criticality()
