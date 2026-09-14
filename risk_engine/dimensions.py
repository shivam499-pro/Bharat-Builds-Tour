"""
ThermoGuard Phase IX - Risk Engine Dimensions Implementation.

Computes the 5 core physical and contextual evidence dimensions:
- Dimension A: Thermal Intensity (30%)
- Dimension B: Persistence (25%)
- Dimension C: Industrial / Contextual Association (20%)
- Dimension D: Spatial Scale (10%)
- Dimension E: Spectral / Surface Evidence (15%)

Reference: docs/PhaseIX_RISK_METHODOLOGY.md Sections 3, 4, 7, 8, 9.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

from .normalization import (
    is_missing,
    normalize_frp_mean,
    normalize_frp_max,
    normalize_brightness,
    normalize_persistence_days,
    normalize_detection_count,
    normalize_osm_proximity,
    normalize_fraction,
    normalize_spatial_extent,
    normalize_swir_anomaly,
    normalize_ndvi,
    normalize_bsi,
    normalize_swir_ratio,
)

# --- Locked Dimension Weights ---
WEIGHT_A_THERMAL = 0.30
WEIGHT_B_PERSISTENCE = 0.25
WEIGHT_C_INDUSTRIAL = 0.20
WEIGHT_D_SPATIAL = 0.10
WEIGHT_E_SPECTRAL = 0.15

TOTAL_WEIGHT = WEIGHT_A_THERMAL + WEIGHT_B_PERSISTENCE + WEIGHT_C_INDUSTRIAL + WEIGHT_D_SPATIAL + WEIGHT_E_SPECTRAL


def compute_dimension_a_thermal(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dimension A - Thermal Intensity.
    Sub-features:
      - frp_mean: 0.50
      - frp_max: 0.35
      - brightness_mean: 0.15
    """
    frp_mean_raw = event.get("frp_mean")
    frp_max_raw = event.get("frp_max")
    brightness_raw = event.get("brightness_mean")

    frp_mean_norm, miss_mean = normalize_frp_mean(frp_mean_raw)
    frp_max_norm, miss_max = normalize_frp_max(frp_max_raw)
    brightness_norm, miss_b = normalize_brightness(brightness_raw)

    missing_fields = []
    if miss_mean:
        missing_fields.append("frp_mean")
    if miss_max:
        missing_fields.append("frp_max")
    if miss_b:
        missing_fields.append("brightness_mean")

    score_A = 0.50 * frp_mean_norm + 0.35 * frp_max_norm + 0.15 * brightness_norm
    all_missing = len(missing_fields) == 3

    return {
        "dimension_name": "Thermal Intensity",
        "dimension_code": "A",
        "weight": WEIGHT_A_THERMAL,
        "score": float(score_A),
        "weighted_contribution": float(WEIGHT_A_THERMAL * score_A),
        "raw_inputs": {
            "frp_mean": frp_mean_raw,
            "frp_max": frp_max_raw,
            "brightness_mean": brightness_raw,
        },
        "normalized_components": {
            "frp_mean_norm": frp_mean_norm,
            "frp_max_norm": frp_max_norm,
            "brightness_norm": brightness_norm,
        },
        "internal_weights": {
            "frp_mean": 0.50,
            "frp_max": 0.35,
            "brightness_mean": 0.15,
        },
        "missing_fields": missing_fields,
        "is_completely_missing": all_missing,
    }


def compute_dimension_b_persistence(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dimension B - Persistence.
    Sub-features:
      - distinct_detection_days: 0.70
      - detection_count: 0.30
    """
    detection_days_raw = event.get("distinct_detection_days")
    detection_count_raw = event.get("detection_count")

    days_norm, miss_days = normalize_persistence_days(detection_days_raw)
    count_norm, miss_count = normalize_detection_count(detection_count_raw)

    missing_fields = []
    if miss_days:
        missing_fields.append("distinct_detection_days")
    if miss_count:
        missing_fields.append("detection_count")

    score_B = 0.70 * days_norm + 0.30 * count_norm
    all_missing = len(missing_fields) == 2

    return {
        "dimension_name": "Persistence",
        "dimension_code": "B",
        "weight": WEIGHT_B_PERSISTENCE,
        "score": float(score_B),
        "weighted_contribution": float(WEIGHT_B_PERSISTENCE * score_B),
        "raw_inputs": {
            "distinct_detection_days": detection_days_raw,
            "detection_count": detection_count_raw,
        },
        "normalized_components": {
            "persistence_norm": days_norm,
            "detection_count_norm": count_norm,
        },
        "internal_weights": {
            "distinct_detection_days": 0.70,
            "detection_count": 0.30,
        },
        "missing_fields": missing_fields,
        "is_completely_missing": all_missing,
    }


def compute_dimension_c_industrial(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dimension C - Industrial / Contextual Association.
    Strictly objective spatial metrics only:
      - osm_matched_fraction: 0.35
      - osm_containment_fraction: 0.30
      - osm_proximity_fraction: 0.20
      - osm_proximity_score: 0.15
    osm_tier, osm_primary_category, osm_sub_category are retained as metadata only.
    """
    matched_raw = event.get("osm_matched_fraction")
    containment_raw = event.get("osm_containment_fraction")
    proximity_raw = event.get("osm_proximity_fraction")
    min_dist_raw = event.get("min_distance_m")

    # Has OSM industrial match flag
    has_match_raw = event.get("has_osm_industrial_match")
    has_match = bool(has_match_raw) if has_match_raw is not None and not is_missing(has_match_raw) else False

    # Proximity score from distance
    prox_score, miss_dist = normalize_osm_proximity(min_dist_raw)
    matched_norm, miss_matched = normalize_fraction(matched_raw)
    containment_norm, miss_containment = normalize_fraction(containment_raw)
    proximity_norm, miss_proximity = normalize_fraction(proximity_raw)

    missing_fields = []
    if miss_matched:
        missing_fields.append("osm_matched_fraction")
    if miss_containment:
        missing_fields.append("osm_containment_fraction")
    if miss_proximity:
        missing_fields.append("osm_proximity_fraction")
    if miss_dist:
        missing_fields.append("min_distance_m")

    # If all fields missing or no match indicated
    is_no_match = (len(missing_fields) == 4) or (not has_match and matched_norm == 0.0 and prox_score == 0.0)

    score_C = (
        0.35 * matched_norm
        + 0.30 * containment_norm
        + 0.20 * proximity_norm
        + 0.15 * prox_score
    )

    return {
        "dimension_name": "Industrial / Contextual Association",
        "dimension_code": "C",
        "weight": WEIGHT_C_INDUSTRIAL,
        "score": float(score_C),
        "weighted_contribution": float(WEIGHT_C_INDUSTRIAL * score_C),
        "raw_inputs": {
            "osm_matched_fraction": matched_raw,
            "osm_containment_fraction": containment_raw,
            "osm_proximity_fraction": proximity_raw,
            "min_distance_m": min_dist_raw,
            "has_osm_industrial_match": has_match_raw,
            "osm_tier": event.get("osm_tier"),
            "osm_primary_category": event.get("osm_primary_category"),
            "osm_sub_category": event.get("osm_sub_category"),
        },
        "normalized_components": {
            "osm_matched_fraction": matched_norm,
            "osm_containment_fraction": containment_norm,
            "osm_proximity_fraction": proximity_norm,
            "osm_proximity_score": prox_score,
        },
        "internal_weights": {
            "osm_matched_fraction": 0.35,
            "osm_containment_fraction": 0.30,
            "osm_proximity_fraction": 0.20,
            "osm_proximity_score": 0.15,
        },
        "missing_fields": missing_fields,
        "has_mapped_association": not is_no_match and score_C > 0.0,
        "is_completely_missing": len(missing_fields) == 4,
    }


def compute_dimension_d_spatial(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dimension D - Spatial Scale.
    Quantifies physical event footprint extent:
      - spatial_norm (spatial_extent_km2): 1.00
    distinct_satellites is excluded from risk scoring (allocated to Evidence Confidence).
    """
    extent_raw = event.get("spatial_extent_km2")
    spatial_norm, miss_extent = normalize_spatial_extent(extent_raw)

    missing_fields = []
    if miss_extent:
        missing_fields.append("spatial_extent_km2")

    score_D = spatial_norm

    return {
        "dimension_name": "Spatial Scale",
        "dimension_code": "D",
        "weight": WEIGHT_D_SPATIAL,
        "score": float(score_D),
        "weighted_contribution": float(WEIGHT_D_SPATIAL * score_D),
        "raw_inputs": {
            "spatial_extent_km2": extent_raw,
        },
        "normalized_components": {
            "spatial_norm": spatial_norm,
        },
        "internal_weights": {
            "spatial_norm": 1.00,
        },
        "missing_fields": missing_fields,
        "is_completely_missing": miss_extent,
    }


def compute_dimension_e_spectral(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dimension E - Spectral / Surface Evidence.
    Sentinel-2 optical/SWIR surface reflectance contrast and ground disturbance.
    Sub-features:
      - swir_anomaly_norm: 0.45
      - ndvi_disturb_norm: 0.25
      - swir_ratio_norm: 0.20
      - bsi_norm: 0.10
    Adjusted by spectral reliability:
      spectral_reliability = temporal_reliability * cloud_reliability
    """
    has_spectral_raw = event.get("has_spectral_features")
    has_scene_raw = event.get("has_satellite_scene")

    # If has_spectral_features is not explicitly given, infer from b02 or swir2 presence
    if has_spectral_raw is None:
        has_spectral = 1 if not is_missing(event.get("b02_blue_mean")) or not is_missing(event.get("swir2_anomaly_ratio")) else 0
    else:
        has_spectral = int(has_spectral_raw) if not is_missing(has_spectral_raw) else 0

    if has_scene_raw is None:
        has_scene = 1 if event.get("satellite_scene_id") is not None or has_spectral == 1 else 0
    else:
        has_scene = int(has_scene_raw) if not is_missing(has_scene_raw) else 0

    swir_anomaly_raw = event.get("swir2_anomaly_ratio")
    ndvi_raw = event.get("ndvi")
    bsi_raw = event.get("bsi")
    swir_ratio_raw = event.get("swir2_swir1_ratio")

    temporal_delta_raw = event.get("temporal_delta_days")
    scl_clear_raw = event.get("scl_clear_fraction")

    # Normalization of sub-features
    swir_anomaly_norm, miss_swir_a = normalize_swir_anomaly(swir_anomaly_raw)
    ndvi_disturb_norm, miss_ndvi = normalize_ndvi(ndvi_raw)
    bsi_norm, miss_bsi = normalize_bsi(bsi_raw)
    swir_ratio_norm, miss_swir_r = normalize_swir_ratio(swir_ratio_raw)

    missing_fields = []
    if miss_swir_a:
        missing_fields.append("swir2_anomaly_ratio")
    if miss_ndvi:
        missing_fields.append("ndvi")
    if miss_bsi:
        missing_fields.append("bsi")
    if miss_swir_r:
        missing_fields.append("swir2_swir1_ratio")

    # Temporal reliability
    if is_missing(temporal_delta_raw):
        temporal_reliability = 0.5
    else:
        delta = float(temporal_delta_raw)
        if delta <= 0.0:
            temporal_reliability = 1.0
        elif delta >= 90.0:
            temporal_reliability = 0.0
        else:
            temporal_reliability = 1.0 - (delta / 90.0)

    # Cloud reliability
    if has_spectral == 0 or is_missing(scl_clear_raw):
        cloud_reliability = 0.0
    else:
        clear_frac = float(scl_clear_raw)
        if clear_frac >= 0.9:
            cloud_reliability = 1.0
        elif clear_frac >= 0.5:
            cloud_reliability = clear_frac
        else:
            cloud_reliability = 0.0

    spectral_reliability = float(temporal_reliability * cloud_reliability)

    # Unadjusted raw spectral score
    E_raw = (
        0.45 * swir_anomaly_norm
        + 0.25 * ndvi_disturb_norm
        + 0.20 * swir_ratio_norm
        + 0.10 * bsi_norm
    )

    # If has_spectral_features == 0 or no scene, contribution is 0.0
    if has_spectral == 0 or has_scene == 0:
        score_E = 0.0
        spectral_reliability = 0.0
        all_missing = True
    else:
        score_E = E_raw * spectral_reliability
        all_missing = len(missing_fields) == 4

    return {
        "dimension_name": "Spectral / Surface Evidence",
        "dimension_code": "E",
        "weight": WEIGHT_E_SPECTRAL,
        "score": float(score_E),
        "raw_score_before_reliability": float(E_raw),
        "spectral_reliability": float(spectral_reliability),
        "temporal_reliability": float(temporal_reliability),
        "cloud_reliability": float(cloud_reliability),
        "weighted_contribution": float(WEIGHT_E_SPECTRAL * score_E),
        "raw_inputs": {
            "swir2_anomaly_ratio": swir_anomaly_raw,
            "ndvi": ndvi_raw,
            "bsi": bsi_raw,
            "swir2_swir1_ratio": swir_ratio_raw,
            "temporal_delta_days": temporal_delta_raw,
            "scl_clear_fraction": scl_clear_raw,
            "has_spectral_features": has_spectral,
            "has_satellite_scene": has_scene,
        },
        "normalized_components": {
            "swir_anomaly_norm": swir_anomaly_norm,
            "ndvi_disturb_norm": ndvi_disturb_norm,
            "bsi_norm": bsi_norm,
            "swir_ratio_norm": swir_ratio_norm,
        },
        "internal_weights": {
            "swir_anomaly_norm": 0.45,
            "ndvi_disturb_norm": 0.25,
            "swir_ratio_norm": 0.20,
            "bsi_norm": 0.10,
        },
        "missing_fields": missing_fields,
        "is_completely_missing": all_missing,
    }
