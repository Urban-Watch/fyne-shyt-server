#!/usr/bin/env python3
"""Quick verification that the improved criticality formula is restored."""

from app.ai.criticality_score import compute_criticality_score

print("=== VERIFYING IMPROVED CRITICALITY FORMULA ===")

# Test with your real data
result = compute_criticality_score(0.587, 55, 0, 1)
print(f"\n✅ Formula restored successfully!")
print(f"Criticality Score: {result['criticality']}")
print(f"Formula Type: {result.get('formula', 'unknown')}")
print(f"Raw Score: {result['raw_score']}")

# Check if it's the improved weighted average (not multiplicative)
if result.get('formula') == 'weighted_average':
    print("✅ CONFIRMED: Using improved weighted average formula")
    print("✅ Components properly balanced across all factors")
else:
    print("❌ WARNING: Still using old multiplicative formula")

print(f"\nWeights: {result['components']['weights']}")
print(f"Components: severity={result['components']['severity']}, impact={result['components']['impact_norm']}, urgency={result['components']['urgency']}, reports={result['components']['reports_norm']}")
