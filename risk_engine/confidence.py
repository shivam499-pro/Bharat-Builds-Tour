"""
ThermoGuard Phase IX - Evidence Confidence Calculation.

Evidence Confidence is strictly separate from the Risk Score.
It quantifies the completeness, corroboration, and quality/reliability
of the available multi-source evidence base (0-100).
Confidence is NOT class probability.

Reference: docs/PhaseIX_RISK_METHODOLOGY.md Section 9.2.
"""

from typing import Dict, Any, Optional
import numpy as np
import pandas as pd

from .normalization import is_missing


CONFIDENCE_WEIGHT_SATELLITE = 0.30
CONFIDENCE_WEIGHT_FIRMS_COMPLETE = 0.20
CONFIDENCE_WEIGHT_OSM_COMPLETE = 0.20
CONFIDENCE_WEIGHT_SPECTRAL_QUALITY = 0.30


def get_confidence_tier(confidence_score: float) -> str:
    """
    Map numerical confidence (0-100) to Evidence Confidence Tier:
    - HIGH: >= 75.0
    - MEDIUM: 50.0 to 74.9
    - LOW: < 50.0
    """
    if confidence_score >= 75.0:
        return "HIGH"
    elif confidence_score >= 50.0:
        return "MEDIUM"
    else:
        return "LOW"


def compute_evidence_confidence(
    event: Dict[str, Any],
    spectral_reliability: float,
    has_spectral_features: int,
    osm_query_complete: bool = True,
) -> Dict[str, Any]:
    """
    Compute Evidence Confidence (0-100) and confidence tier.

    Inputs:
    - distinct_satellites: Multi-sensor platform count [1 to 5]
    - firms_complete: Active detection presence (1.0)
    - osm_query_complete: Whether OSM spatial layer was queried and available (1.0)
    - has_spectral_features: 1 if spectral features extracted, 0 if missing
    - spectral_reliability: temporal_reliability * cloud_reliability [0.0 to 1.0]
    """
    distinct_sat_raw = event.get("distinct_satellites")
    if is_missing(distinct_sat_raw):
        # Default to minimum single-platform observation for detected FIRMS event
        distinct_sat = 1
    else:
        distinct_sat = max(1, int(distinct_sat_raw))

    satellite_corroboration = float(np.clip(distinct_sat, 1, 5)) / 5.0
    firms_completeness = 1.0
    osm_completeness = 1.0 if osm_query_complete else 0.0
    spectral_quality_term = float(has_spectral_features) * float(spectral_reliability)

    confidence_raw = (
        CONFIDENCE_WEIGHT_SATELLITE * satellite_corroboration
        + CONFIDENCE_WEIGHT_FIRMS_COMPLETE * firms_completeness
        + CONFIDENCE_WEIGHT_OSM_COMPLETE * osm_completeness
        + CONFIDENCE_WEIGHT_SPECTRAL_QUALITY * spectral_quality_term
    )

    confidence_score = round(confidence_raw * 100.0, 1)
    confidence_tier = get_confidence_tier(confidence_score)

    return {
        "score": confidence_score,
        "score_raw": float(confidence_raw),
        "tier": confidence_tier,
        "components": {
            "satellite_corroboration": {
                "distinct_satellites": distinct_sat,
                "score": satellite_corroboration,
                "weight": CONFIDENCE_WEIGHT_SATELLITE,
                "contribution": float(CONFIDENCE_WEIGHT_SATELLITE * satellite_corroboration),
            },
            "firms_completeness": {
                "score": firms_completeness,
                "weight": CONFIDENCE_WEIGHT_FIRMS_COMPLETE,
                "contribution": float(CONFIDENCE_WEIGHT_FIRMS_COMPLETE * firms_completeness),
            },
            "osm_completeness": {
                "osm_query_complete": osm_query_complete,
                "score": osm_completeness,
                "weight": CONFIDENCE_WEIGHT_OSM_COMPLETE,
                "contribution": float(CONFIDENCE_WEIGHT_OSM_COMPLETE * osm_completeness),
            },
            "spectral_quality": {
                "has_spectral_features": has_spectral_features,
                "spectral_reliability": spectral_reliability,
                "score": spectral_quality_term,
                "weight": CONFIDENCE_WEIGHT_SPECTRAL_QUALITY,
                "contribution": float(CONFIDENCE_WEIGHT_SPECTRAL_QUALITY * spectral_quality_term),
            },
        },
    }
