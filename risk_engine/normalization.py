"""
ThermoGuard Phase IX - Risk Engine Normalization Specifications.

Provisional pilot/expert normalization anchors requiring sensitivity analysis
and later empirical calibration once human-reviewed ground truth becomes available.
Reference: docs/PhaseIX_RISK_METHODOLOGY.md Section 6.
"""

from typing import Optional, Union, Tuple
import numpy as np
import pandas as pd


METHODOLOGY_VERSION = "PhaseIX-2026-09-14"

# --- Provisional Normalization Anchors ---
FRP_MEAN_CEILING = 100.0  # MW
FRP_MAX_CEILING = 500.0   # MW
BRIGHTNESS_FLOOR = 300.0  # K
BRIGHTNESS_RANGE = 70.0   # K (370 K ceiling)

PERSISTENCE_DAYS_ANCHOR = 365.0  # Days
DETECTION_COUNT_ANCHOR = 50000.0 # Detections

OSM_DISTANCE_THRESHOLD = 5000.0  # meters

SPATIAL_EXTENT_ANCHOR = 500.0    # km2

SWIR_ANOMALY_THRESHOLD = 1.0     # Baseline contrast
SWIR_ANOMALY_RANGE = 5.0         # Upper contrast clip (1.0 + 5.0 = 6.0)
SWIR_RATIO_CEILING = 2.0         # B12/B11 ratio


def is_missing(val: Optional[Union[float, int]]) -> bool:
    """Check if a numeric value is missing or NaN."""
    if val is None:
        return True
    try:
        return bool(pd.isna(val))
    except Exception:
        return False


def normalize_frp_mean(val: Optional[float]) -> Tuple[float, bool]:
    """
    FRP mean normalization: clip(frp_mean, 0, 100) / 100.
    Returns: (normalized_value, is_missing_flag)
    """
    if is_missing(val):
        return 0.0, True
    clipped = float(np.clip(float(val), 0.0, FRP_MEAN_CEILING))
    return clipped / FRP_MEAN_CEILING, False


def normalize_frp_max(val: Optional[float]) -> Tuple[float, bool]:
    """
    FRP max normalization: clip(frp_max, 0, 500) / 500.
    Returns: (normalized_value, is_missing_flag)
    """
    if is_missing(val):
        return 0.0, True
    clipped = float(np.clip(float(val), 0.0, FRP_MAX_CEILING))
    return clipped / FRP_MAX_CEILING, False


def normalize_brightness(val: Optional[float]) -> Tuple[float, bool]:
    """
    Brightness temperature: clip((brightness_mean - 300), 0, 70) / 70.
    Returns: (normalized_value, is_missing_flag)
    """
    if is_missing(val):
        return 0.0, True
    offset = float(val) - BRIGHTNESS_FLOOR
    clipped = float(np.clip(offset, 0.0, BRIGHTNESS_RANGE))
    return clipped / BRIGHTNESS_RANGE, False


def normalize_persistence_days(val: Optional[Union[float, int]]) -> Tuple[float, bool]:
    """
    Distinct detection days: log1p(distinct_detection_days) / log1p(365).
    Returns: (normalized_value, is_missing_flag)
    """
    if is_missing(val):
        return 0.0, True
    v = max(0.0, float(val))
    norm = float(np.log1p(v) / np.log1p(PERSISTENCE_DAYS_ANCHOR))
    return float(np.clip(norm, 0.0, 1.0)), False


def normalize_detection_count(val: Optional[Union[float, int]]) -> Tuple[float, bool]:
    """
    Detection count: log1p(detection_count) / log1p(50000).
    Returns: (normalized_value, is_missing_flag)
    """
    if is_missing(val):
        return 0.0, True
    v = max(0.0, float(val))
    norm = float(np.log1p(v) / np.log1p(DETECTION_COUNT_ANCHOR))
    return float(np.clip(norm, 0.0, 1.0)), False


def normalize_osm_proximity(min_distance_m: Optional[float]) -> Tuple[float, bool]:
    """
    Convert min distance to proximity score:
    - NULL: 0.0 (no evidence of proximity)
    - <= 0: 1.0 (inside industrial polygon)
    - >= 5000: 0.0 (beyond threshold)
    - else: 1.0 - (min_distance_m / 5000)
    Returns: (normalized_value, is_missing_flag)
    """
    if is_missing(min_distance_m):
        return 0.0, True
    d = float(min_distance_m)
    if d <= 0.0:
        return 1.0, False
    elif d >= OSM_DISTANCE_THRESHOLD:
        return 0.0, False
    else:
        score = 1.0 - (d / OSM_DISTANCE_THRESHOLD)
        return float(np.clip(score, 0.0, 1.0)), False


def normalize_fraction(val: Optional[float]) -> Tuple[float, bool]:
    """Ensure fraction in [0, 1]."""
    if is_missing(val):
        return 0.0, True
    return float(np.clip(float(val), 0.0, 1.0)), False


def normalize_spatial_extent(spatial_extent_km2: Optional[float]) -> Tuple[float, bool]:
    """
    Spatial extent: log1p(spatial_extent_km2) / log1p(500).
    Returns: (normalized_value, is_missing_flag)
    """
    if is_missing(spatial_extent_km2):
        return 0.0, True
    v = max(0.0, float(spatial_extent_km2))
    norm = float(np.log1p(v) / np.log1p(SPATIAL_EXTENT_ANCHOR))
    return float(np.clip(norm, 0.0, 1.0)), False


def normalize_swir_anomaly(swir2_anomaly_ratio: Optional[float]) -> Tuple[float, bool]:
    """
    SWIR2 anomaly ratio (surface reflectance contrast):
    - < 1.0: 0.0 (no contrast above background)
    - >= 1.0: clip(swir2_anomaly_ratio - 1.0, 0, 5) / 5
    Returns: (normalized_value, is_missing_flag)
    """
    if is_missing(swir2_anomaly_ratio):
        return 0.0, True
    ratio = float(swir2_anomaly_ratio)
    if ratio < SWIR_ANOMALY_THRESHOLD:
        return 0.0, False
    excess = ratio - SWIR_ANOMALY_THRESHOLD
    norm = float(np.clip(excess, 0.0, SWIR_ANOMALY_RANGE) / SWIR_ANOMALY_RANGE)
    return norm, False


def normalize_ndvi(ndvi: Optional[float]) -> Tuple[float, bool]:
    """
    NDVI surface disturbance: clip(1.0 - ndvi, 0, 1).
    Lower vegetation density -> higher disturbance score.
    Returns: (normalized_value, is_missing_flag)
    """
    if is_missing(ndvi):
        return 0.0, True
    disturb = 1.0 - float(ndvi)
    return float(np.clip(disturb, 0.0, 1.0)), False


def normalize_bsi(bsi: Optional[float]) -> Tuple[float, bool]:
    """
    BSI bare soil: clip(bsi + 0.5, 0, 1).
    Returns: (normalized_value, is_missing_flag)
    """
    if is_missing(bsi):
        return 0.0, True
    shifted = float(bsi) + 0.5
    return float(np.clip(shifted, 0.0, 1.0)), False


def normalize_swir_ratio(swir2_swir1_ratio: Optional[float]) -> Tuple[float, bool]:
    """
    SWIR2 / SWIR1 ratio: clip(swir2_swir1_ratio, 0, 2) / 2.
    Returns: (normalized_value, is_missing_flag)
    """
    if is_missing(swir2_swir1_ratio):
        return 0.0, True
    clipped = float(np.clip(float(swir2_swir1_ratio), 0.0, SWIR_RATIO_CEILING))
    return clipped / SWIR_RATIO_CEILING, False
