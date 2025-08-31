import math
import logging
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def normalize_urgency(age_seconds: float, cap_days: float = 30.0) -> float:
    """
    Normalize urgency (how old the problem is) to [1,100].
    - age_seconds: time since report in seconds
    - cap_days: age at which urgency saturates to 100 (default 30 days)
    Uses linear normalization with minimum value of 1: urgency = max(1, min(100, (age_days / cap_days) * 99 + 1)).
    """
    age_days = max(0.0, age_seconds) / (3600.0 * 24.0)
    # Scale to 1-100 range instead of 0-100
    result = max(1.0, min(100.0, (age_days / max(1e-9, cap_days)) * 99.0 + 1.0))
    # logger.debug(f"normalize_urgency: age_seconds={age_seconds}, cap_days={cap_days}, age_days={age_days:.2f}, result={result:.4f}")
    return result

def normalize_reports(count: int, report_cap: int = 10) -> float:
    """
    Simple normalization of report_count to [1,100] with linear scaling.
    - count=1 returns 1.0
    - count=report_cap returns 100.0
    """
    if count <= 1:
        logger.debug(f"normalize_reports: count={count}, returning 1.0")
        return 1.0
    
    # Linear scaling from 1 to 100
    result = min(100.0, 1.0 + (count - 1) * (99.0 / (report_cap - 1)))
    # logger.debug(f"normalize_reports: count={count}, report_cap={report_cap}, result={result:.4f}")
    return result

def compute_criticality_score(
    severity: float,
    impact: float,
    age_seconds: Optional[float],
    report_count: int = 1,
    weights: Optional[Dict[str, float]] = None,
    caps: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Compute criticality score using base formula with logarithmic report multiplier.
    
    Returns dict:
      {
        "criticality": float (1-100),
        "components": {"severity":..., "impact":..., "urgency":..., "base_score":..., "log_multiplier":...},
        "raw_score": float,
        "formula": str
      }
    FORMULA:
      base_score = (severity + impact) * urgency / 2
      criticality = base_score * (1 + max(0, log(report_count)))
    """

    logger.info("=== CRITICALITY_SCORE.PY COMPUTE_CRITICALITY_SCORE STARTED (MULTIPLICATIVE) ===")
    logger.info(f"Input: severity={severity}, impact={impact}, age_seconds={age_seconds}, report_count={report_count}")

    # --- normalize severity (0-100 -> 0-100, just clamp) ---
    severity_norm = max(0.0, min(100.0, float(severity)))
    logger.info(f"Severity normalized: {severity_norm}")

    # --- normalize impact (0-100 -> 0-100, just clamp) ---
    impact_norm = max(0.0, min(100.0, float(impact)))
    logger.info(f"Impact normalized: {impact_norm}")

    # --- urgency normalization (1-100, minimum value 1) ---
    if age_seconds is None:
        # If age unknown, treat as low urgency but minimum 1
        urgency_norm = 1.0
        logger.info("Age seconds is None, setting urgency_norm to 1.0")
    else:
        urgency_norm = normalize_urgency(age_seconds, cap_days=30.0)
        logger.info(f"Urgency normalized: {urgency_norm} from age_seconds={age_seconds}")

    # --- reports normalization (1-100, minimum value 1) ---
    reports_norm = normalize_reports(report_count, report_cap=10)
    logger.info(f"Reports normalized: {reports_norm} from report_count={report_count}")

    # --- MULTIPLICATIVE FORMULA with logarithmic report multiplier ---
    # Base score: (severity + impact) * urgency / 2
    base_score = (severity_norm + impact_norm) * urgency_norm / 2.0
    
    # Apply logarithmic report multiplier: 1 + min(0, log(report_count))
    # Note: log of values < 1 gives negative numbers, so min(0, log(x)) = 0 for x >= 1
    if report_count <= 1:
        log_multiplier = 1.0  # 1 + 0 = 1 for single reports
    else:
        log_multiplier = 1.0 + max(0.0, math.log(report_count))  # 1 + log(count) for multiple reports
    
    raw_score = base_score * log_multiplier
    
    # Clamp to 1-100 range and convert to integer with ceiling to ensure minimum value of 1
    import math
    clamped_score = max(1.0, min(100.0, raw_score))  # Cap at 100 maximum
    criticality = max(1, math.ceil(clamped_score))

    logger.info(f"Base score calculation: ({severity_norm} + {impact_norm}) * {urgency_norm} / 2 = {base_score:.2f}")
    logger.info(f"Log multiplier: 1 + max(0, log({report_count})) = {log_multiplier:.2f}")
    logger.info(f"Raw score: {base_score:.2f} * {log_multiplier:.2f} = {raw_score:.2f}")
    logger.info(f"Clamped score: {clamped_score:.2f}")
    logger.info(f"Final criticality score: {criticality} (1-100 scale)")
    logger.info(f"Formula used: (severity + impact) * urgency / 2 * (1 + max(0, log(reports)))")

    result = {
        "criticality": criticality,
        "raw_score": round(float(raw_score), 2),
        "formula": "multiplicative_with_log_reports",
        "components": {
            "severity": round(severity_norm, 2),
            "impact": round(impact_norm, 2),
            "urgency": round(urgency_norm, 2),
            "base_score": round(base_score, 2),
            "log_multiplier": round(log_multiplier, 2),
            "report_count": report_count
        }
    }
    return result
