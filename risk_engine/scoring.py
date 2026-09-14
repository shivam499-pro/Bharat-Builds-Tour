"""
ThermoGuard Phase IX - Deterministic Risk Engine Scoring Pipeline.

Computes deterministic risk score (0-100), risk tier, dimension contributions,
and evidence confidence according to the locked methodology.

Reference: docs/PhaseIX_RISK_METHODOLOGY.md Sections 2, 7, 8, 9, 10.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

from .normalization import METHODOLOGY_VERSION
from .dimensions import (
    compute_dimension_a_thermal,
    compute_dimension_b_persistence,
    compute_dimension_c_industrial,
    compute_dimension_d_spatial,
    compute_dimension_e_spectral,
    WEIGHT_A_THERMAL,
    WEIGHT_B_PERSISTENCE,
    WEIGHT_C_INDUSTRIAL,
    WEIGHT_D_SPATIAL,
    WEIGHT_E_SPECTRAL,
)
from .confidence import compute_evidence_confidence


def get_risk_tier(risk_score: float) -> str:
    """
    Map numerical risk score (0-100) to Risk Tier:
    - LOW: 0.0 to 24.9
    - MODERATE: 25.0 to 49.9
    - HIGH: 50.0 to 74.9
    - CRITICAL: 75.0 to 100.0
    Reference: Section 10.2.
    """
    if risk_score >= 75.0:
        return "CRITICAL"
    elif risk_score >= 50.0:
        return "HIGH"
    elif risk_score >= 25.0:
        return "MODERATE"
    else:
        return "LOW"


def score_event(
    event: Dict[str, Any],
    osm_query_complete: bool = True,
) -> Dict[str, Any]:
    """
    Score a single thermal event deterministically.

    Non-negotiable invariants:
    1. Fixed weights: 30%, 25%, 20%, 10%, 15%.
    2. No weight redistribution for missing data.
    3. WorldCover is context only (0% risk weight).
    4. OSM tier / category is context only (0% risk weight).
    5. Evidence Confidence is strictly separate from Risk Score.
    6. Returns reproducible, unrounded intermediate values and cleanly rounded outputs.
    """
    event_id = str(event.get("event_id", "UNKNOWN"))

    # Step 1: Compute 5 dimensions
    dim_A = compute_dimension_a_thermal(event)
    dim_B = compute_dimension_b_persistence(event)
    dim_C = compute_dimension_c_industrial(event)
    dim_D = compute_dimension_d_spatial(event)
    dim_E = compute_dimension_e_spectral(event)

    # Step 2: Linear weighted aggregation (Fixed scale 0-100; no redistribution)
    risk_raw = (
        dim_A["weighted_contribution"]
        + dim_B["weighted_contribution"]
        + dim_C["weighted_contribution"]
        + dim_D["weighted_contribution"]
        + dim_E["weighted_contribution"]
    )
    # Numerical score rounded at boundary per methodology
    risk_score = round(risk_raw * 100.0, 1)
    risk_tier = get_risk_tier(risk_score)

    # Step 3: Evidence Confidence computation (separate output)
    spectral_reliability = dim_E["spectral_reliability"]
    has_spectral_features = dim_E["raw_inputs"]["has_spectral_features"]
    conf = compute_evidence_confidence(
        event=event,
        spectral_reliability=spectral_reliability,
        has_spectral_features=has_spectral_features,
        osm_query_complete=osm_query_complete,
    )

    # Step 4: Audit missing evidence
    missing_evidence: List[str] = []
    if dim_A["is_completely_missing"]:
        missing_evidence.append("dimension_A_thermal_missing")
    elif len(dim_A["missing_fields"]) > 0:
        missing_evidence.append(f"partial_thermal:{','.join(dim_A['missing_fields'])}")

    if dim_B["is_completely_missing"]:
        missing_evidence.append("dimension_B_persistence_missing")
    elif len(dim_B["missing_fields"]) > 0:
        missing_evidence.append(f"partial_persistence:{','.join(dim_B['missing_fields'])}")

    if dim_C["is_completely_missing"]:
        missing_evidence.append("dimension_C_industrial_missing")
    elif not dim_C["has_mapped_association"]:
        missing_evidence.append("osm_context:no_mapped_association")

    if dim_D["is_completely_missing"]:
        missing_evidence.append("dimension_D_spatial_missing")

    if dim_E["is_completely_missing"]:
        missing_evidence.append("dimension_E_spectral_missing")
        if dim_E["raw_inputs"].get("has_satellite_scene") == 0:
            missing_evidence.append("spectral_coverage:no_scene")
        elif dim_E["raw_inputs"].get("has_spectral_features") == 0:
            missing_evidence.append("spectral_coverage:extraction_failed")
    else:
        if dim_E["cloud_reliability"] < 0.5:
            missing_evidence.append("spectral_quality:degraded_cloud")
        if dim_E["temporal_reliability"] < 0.5:
            missing_evidence.append("temporal_relevance:stale")
        if len(dim_E["missing_fields"]) > 0:
            missing_evidence.append(f"partial_spectral:{','.join(dim_E['missing_fields'])}")

    # Step 5: Contextual data (0% risk weight)
    contextual_data = {
        "worldcover_class": event.get("worldcover_class"),
        "worldcover_class_name": event.get("worldcover_class_name"),
        "osm_primary_category": event.get("osm_primary_category"),
        "osm_sub_category": event.get("osm_sub_category"),
        "osm_tier": event.get("osm_tier"),
        "distinct_satellites": event.get("distinct_satellites"),
    }

    return {
        "event_id": event_id,
        "methodology_version": METHODOLOGY_VERSION,
        "risk_score": risk_score,
        "risk_score_raw": float(risk_raw),
        "risk_tier": risk_tier,
        "thermal_dimension_score": float(dim_A["score"]),
        "persistence_dimension_score": float(dim_B["score"]),
        "industrial_dimension_score": float(dim_C["score"]),
        "spatial_dimension_score": float(dim_D["score"]),
        "spectral_dimension_score": float(dim_E["score"]),
        "dimensions": {
            "thermal": dim_A,
            "persistence": dim_B,
            "industrial": dim_C,
            "spatial": dim_D,
            "spectral": dim_E,
        },
        "evidence_confidence": conf["score"],
        "confidence_tier": conf["tier"],
        "confidence_details": conf,
        "missing_evidence": missing_evidence,
        "contextual_data": contextual_data,
    }


def score_dataframe(
    df: pd.DataFrame,
    osm_query_complete: bool = True,
) -> pd.DataFrame:
    """
    Score an entire dataframe of events deterministically.
    Returns a dataframe containing all required score and audit fields.
    """
    results = []
    for _, row in df.iterrows():
        res = score_event(row.to_dict(), osm_query_complete=osm_query_complete)
        # Flatten to top-level structured record for tabular analysis
        flat = {
            "event_id": res["event_id"],
            "risk_score": res["risk_score"],
            "risk_tier": res["risk_tier"],
            "thermal_dimension_score": res["thermal_dimension_score"],
            "persistence_dimension_score": res["persistence_dimension_score"],
            "industrial_dimension_score": res["industrial_dimension_score"],
            "spatial_dimension_score": res["spatial_dimension_score"],
            "spectral_dimension_score": res["spectral_dimension_score"],
            "evidence_confidence": res["evidence_confidence"],
            "confidence_tier": res["confidence_tier"],
            "missing_evidence": ",".join(res["missing_evidence"]) if res["missing_evidence"] else "none",
            "methodology_version": res["methodology_version"],
            # Component scores
            "risk_score_raw": res["risk_score_raw"],
            "weighted_thermal": res["dimensions"]["thermal"]["weighted_contribution"],
            "weighted_persistence": res["dimensions"]["persistence"]["weighted_contribution"],
            "weighted_industrial": res["dimensions"]["industrial"]["weighted_contribution"],
            "weighted_spatial": res["dimensions"]["spatial"]["weighted_contribution"],
            "weighted_spectral": res["dimensions"]["spectral"]["weighted_contribution"],
            # Contextual attributes
            "worldcover_class_name": str(res["contextual_data"]["worldcover_class_name"]),
            "osm_primary_category": str(res["contextual_data"]["osm_primary_category"]),
            "osm_tier": res["contextual_data"]["osm_tier"],
            "distinct_satellites": res["contextual_data"]["distinct_satellites"],
        }
        results.append(flat)

    return pd.DataFrame(results)
