import math
import logging
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def normalize_urgency(age_seconds: float, cap_days: float = 30.0) -> float:
    """
    Normalize urgency (how old the problem is) to [0,1].
    - age_seconds: time since report in seconds
    - cap_days: age at which urgency saturates to 1.0 (default 30 days)
    Uses linear normalization: urgency = min(1, age_days / cap_days).
    """
    age_days = max(0.0, age_seconds) / (3600.0 * 24.0)
    result = min(1.0, age_days / max(1e-9, cap_days))
    logger.debug(f"normalize_urgency: age_seconds={age_seconds}, cap_days={cap_days}, age_days={age_days:.2f}, result={result:.4f}")
    return result

def normalize_reports(count: int, report_cap: int = 10) -> float:
    """
    Normalize report_count to [0,1] using a logarithmic curve so
    repeated reports give diminishing returns.
    - report_cap: value at which normalization reaches ~1 (default 10)
    """
    if count <= 0:
        logger.debug(f"normalize_reports: count={count}, returning 0.0")
        return 0.0
    # log1p gives diminishing returns; divide by log1p(report_cap) to scale to ~[0,1]
    result = min(1.0, math.log1p(count) / max(1e-9, math.log1p(report_cap)))
    logger.debug(f"normalize_reports: count={count}, report_cap={report_cap}, result={result:.4f}")
    return result

def compute_criticality_score(
    severity: float,
    impact: float,
    age_seconds: Optional[float],
    report_count: int = 1,
    weights: Optional[Dict[str, float]] = None,
    caps: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    import math
    logger.info("=== CRITICALITY_SCORE COMPUTE STARTED ===")

    # Default weights
    if weights is None:
        weights = {"impact": 0.6, "urgency": 0.25, "reports": 0.15}
    w_sum = sum(weights.values())
    weights = {k: v / w_sum for k, v in weights.items()}

    sev = max(0.0, min(1.0, float(severity)))
    # nonlinear severity adjustment
    sev_adj = sev ** 1.5

    impact_norm = max(0.0, min(1.0, float(impact) / 100.0))
    urgency_norm = normalize_urgency(age_seconds, cap_days=30.0) if age_seconds else 0.0
    reports_norm = normalize_reports(report_count, report_cap=10)

    # dynamic weighting: urgency weighs more if severity is high
    if sev > 0.7:
        weights = {"impact": 0.4, "urgency": 0.4, "reports": 0.2}

    raw_score = sev_adj * (
        weights["impact"] * impact_norm +
        weights["urgency"] * urgency_norm +
        weights["reports"] * reports_norm
    )

    # floor boost for critical cases
    if impact_norm >= 0.8 or urgency_norm >= 0.8:
        raw_score = min(1.0, raw_score + 0.1)

    # logistic scaling for spread
    criticality_float = 100 * (1 / (1 + math.exp(-5 * (raw_score - 0.5))))
    criticality = max(1, int(round(criticality_float)))

    result = {
        "criticality": criticality,
        "raw_score": round(float(raw_score), 4),
        "components": {
            "severity": round(sev, 3),
            "severity_adj": round(sev_adj, 3),
            "impact_norm": round(impact_norm, 3),
            "urgency": round(urgency_norm, 3),
            "reports_norm": round(reports_norm, 3),
            "weights": {k: round(v, 3) for k, v in weights.items()}
        }
    }
    return result
