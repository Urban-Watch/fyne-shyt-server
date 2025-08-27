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
    severity: float,                # between 0 and 1 (0=no severity, 1=max)
    impact: float,                  # between 0 and 100 (your impact_score)
    age_seconds: Optional[float],   # how old the problem is in seconds
    report_count: int = 1,          # number of duplicate reports in same cluster
    weights: Optional[Dict[str, float]] = None,
    caps: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Returns dict:
      {
        "criticality": float (0-100),
        "components": {"severity":..., "impact_norm":..., "urgency":..., "reports_norm":...},
        "raw_score": float (0-1)
      }
    Default combination (recommended):
      criticality_raw = severity * (w_i*impact_norm + w_u*urgency + w_r*reports_norm)
      criticality = criticality_raw * 100
    """

    logger.info("=== CRITICALITY_SCORE.PY COMPUTE_CRITICALITY_SCORE STARTED ===")
    logger.info(f"Input: severity={severity}, impact={impact}, age_seconds={age_seconds}, report_count={report_count}")

    # --- defaults (tweakable) ---
    if weights is None:
        weights = {"impact": 0.6, "urgency": 0.25, "reports": 0.15}
    # ensure weights sum to 1 (normalize if not)
    w_sum = sum(weights.values())
    if w_sum <= 0:
        raise ValueError("Weights must sum to > 0")
    weights = {k: v / w_sum for k, v in weights.items()}
    logger.info(f"Normalized weights: {weights}")

    if caps is None:
        caps = {"pop_scale": 100.0}  # unused here, kept for future extension

    # --- clamp severity ---
    sev = max(0.0, min(1.0, float(severity)))
    logger.info(f"Clamped severity: {sev}")

    # --- normalize impact (0-100 -> 0-1) ---
    impact_norm = max(0.0, min(1.0, float(impact) / 100.0))
    logger.info(f"Normalized impact: {impact_norm}")

    # --- urgency normalization ---
    if age_seconds is None:
        # If age unknown, treat as low urgency by default (0)
        urgency_norm = 0.0
        logger.info("Age seconds is None, setting urgency_norm to 0.0")
    else:
        urgency_norm = normalize_urgency(age_seconds, cap_days=30.0)
        logger.info(f"Calculated urgency_norm: {urgency_norm} from age_seconds={age_seconds}")

    # --- reports normalization ---
    reports_norm = normalize_reports(report_count, report_cap=10)
    logger.info(f"Calculated reports_norm: {reports_norm} from report_count={report_count}")

    # --- combine and convert to integer 1-100 scale ---
    raw_score = sev * (
        weights["impact"] * impact_norm +
        weights["urgency"] * urgency_norm +
        weights["reports"] * reports_norm
    )
    
    # Convert to integer with ceiling to ensure minimum value of 1
    import math
    criticality_float = raw_score * 100.0
    criticality = max(1, math.ceil(criticality_float))

    logger.info(f"Raw score calculation: {raw_score}")
    logger.info(f"Final criticality score: {criticality_float:.2f} -> {criticality} (1-100 scale)")

    result = {
        "criticality": criticality,
        "raw_score": round(float(raw_score), 4),
        "components": {
            "severity": round(sev, 3),
            "impact_norm": round(impact_norm, 4),
            "urgency": round(urgency_norm, 4),
            "reports_norm": round(reports_norm, 4),
            "weights": {k: round(v, 3) for k, v in weights.items()}
        }
    }

    logger.info(f"=== CRITICALITY_SCORE.PY COMPUTE_CRITICALITY_SCORE COMPLETED ===")
    logger.info(f"Final result: {result}")
    return result