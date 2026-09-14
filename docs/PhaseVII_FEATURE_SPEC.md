# ThermoGuard Phase VII — Machine Learning Feature Specification & Inventory

This document defines the complete feature engineering inventory for the ThermoGuard fire event classification model. It audits the enriched satellite/OSM/WorldCover dataset (`firms_satellite_enriched_pilot.parquet`) and ground-truth dataset (`firms_ground_truth_pilot.parquet`), specifying candidate ML features, data types, ranges, imputation strategies, and strict leakage constraints.

---

## 1. Feature Classification Taxonomy

All available fields in the pipeline are systematically categorized into 9 distinct functional groups:

1. **FIRMS Temporal & Spatial Features**: Cluster duration, detection frequencies, spatial bounding extents, and sensor counts.
2. **FIRMS Thermal Features**: Radiant power and thermal brightness measurements.
3. **OSM Infrastructure Features**: Spatial distance, containment, and category tags relative to industrial infrastructure.
4. **ESA WorldCover Features**: Baseline 10-meter land-cover classifications and environmental context.
5. **Sentinel-2 Spectral Features**: Multi-spectral band reflectances (visible, NIR, SWIR) and normalized spectral indices.
6. **Sentinel-2 Quality & Cloud Features**: Scene-level and pixel-level cloud/clear mask fractions and status flags.
7. **Temporal Alignment Features**: Time offsets between satellite image capture and active thermal detections.
8. **Metadata & Identifier Fields**: Technical tracking keys, scene identifiers, and data source manifests.
9. **Label & Human Review Fields**: Ground-truth target annotations and human review audit trail.

---

## 2. Comprehensive Candidate ML Feature Inventory

### 2.1 FIRMS Temporal & Spatial Features

| Feature Name | Source Column | Description | Data Type | Expected Range | Missing-Value Behavior | Safe for ML? | Potential Leakage? | Derived from Label? |
|---|---|---|---|---|---|---|---|---|
| `duration_days` | `duration_days` | Total timespan between first and last FIRMS detection in event cluster | `float64` | $[0.0, 388.1]$ days | None ($0$ nulls) | Yes | No | No |
| `detection_count` | `detection_count` | Total number of individual satellite thermal hotspot detections in cluster | `int64` | $[1, 21883]$ | None ($0$ nulls) | Yes (log-transform recommended) | No | No |
| `distinct_detection_days` | `distinct_detection_days` | Number of unique calendar days on which the event was detected | `int64` | $[1, 343]$ days | None ($0$ nulls) | Yes | No | No |
| `spatial_extent_km2` | `spatial_extent_km2` | Approximate convex hull / bounding polygon area of cluster | `float64` | $[0.0, 88.6]$ km² | None ($0$ nulls; $0.0$ for single-point events) | Yes | No | No |
| `distinct_satellites` | `distinct_satellites` | Count of distinct satellite platforms registering detections | `int32` | $[1, 5]$ | None ($0$ nulls) | Yes | No | No |
| `distinct_instruments` | `distinct_instruments` | Count of distinct sensor types (MODIS vs VIIRS) | `int32` | $[1, 2]$ | None ($0$ nulls) | Yes | No | No |
| `centroid_lat` | `centroid_lat` | Cluster geographic centroid latitude | `float64` | $[12.39, 32.83]$ °N | None ($0$ nulls) | Conditional (spatial CV required to prevent regional overfitting) | No | No |
| `centroid_lon` | `centroid_lon` | Cluster geographic centroid longitude | `float64` | $[69.70, 96.77]$ °E | None ($0$ nulls) | Conditional (spatial CV required to prevent regional overfitting) | No | No |

---

### 2.2 FIRMS Thermal Features

| Feature Name | Source Column | Description | Data Type | Expected Range | Missing-Value Behavior | Safe for ML? | Potential Leakage? | Derived from Label? |
|---|---|---|---|---|---|---|---|---|
| `frp_mean` | `frp_mean` | Average Fire Radiative Power across detections | `float64` | $[1.26, 57.40]$ MW | None ($0$ nulls) | Yes | No | No |
| `frp_max` | `frp_max` | Peak Fire Radiative Power registered in cluster | `float64` | $[8.43, 381.56]$ MW | None ($0$ nulls) | Yes | No | No |
| `brightness_mean` | `brightness_mean` | Average channel brightness temperature (Kelvin) | `float64` | $[306.98, 367.00]$ K | None ($0$ nulls) | Yes | No | No |

---

### 2.3 OSM Infrastructure Features

| Feature Name | Source Column | Description | Data Type | Expected Range | Missing-Value Behavior | Safe for ML? | Potential Leakage? | Derived from Label? |
|---|---|---|---|---|---|---|---|---|
| `min_distance_m` | `min_distance_m` | Distance in meters to nearest industrial OSM feature | `float64` | $[0.0, \infty)$ m (Observed $[0.0, 89.6]$) | $60$ nulls (events without industrial feature within radius). Impute with default upper bound (e.g. $10000$ m) or add missing indicator. | Yes | No | No |
| `osm_matched_fraction` | `osm_matched_fraction` | Fraction of cluster detections matching industrial criteria | `float64` | $[0.0, 1.0]$ | None ($0$ nulls) | Yes | No | No |
| `osm_containment_fraction` | `osm_containment_fraction` | Fraction of detections directly inside an industrial polygon | `float64` | $[0.0, 1.0]$ | None ($0$ nulls) | Yes | No | No |
| `osm_proximity_fraction` | `osm_proximity_fraction` | Fraction of detections within designated proximity buffer | `float64` | $[0.0, 1.0]$ | None ($0$ nulls) | Yes | No | No |
| `osm_tier` | `osm_tier` | Priority tier of matched industrial feature (Tier 1 vs 2) | `float64` | $\{1.0, 2.0\}$ | $60$ nulls; impute as $0$ (no industrial match) | Yes | No | No |
| `osm_primary_category` | `osm_primary_category` | Primary category of matched OSM object (e.g., `mine_quarry`, `industrial_zone`) | `string` | Categorical | $60$ nulls; encode as categorical with `'none'` category | Yes | No | No |
| `osm_sub_category` | `osm_sub_category` | Specific subtype (e.g., `coal`, `factory`) | `string` | Categorical | $60$ nulls; encode with `'none'` category | Yes | No | No |

---

### 2.4 ESA WorldCover Features

| Feature Name | Source Column | Description | Data Type | Expected Range | Missing-Value Behavior | Safe for ML? | Potential Leakage? | Derived from Label? |
|---|---|---|---|---|---|---|---|---|
| `worldcover_class` | `worldcover_class` | Discrete ESA WorldCover class code (10: Tree, 20: Shrub, 30: Grass, 40: Crop, 50: Built-up, 60: Bare, 80: Water) | `uint8` | $\{10, 20, 30, 40, 50, 60, 80\}$ | None ($0$ nulls) | Yes (one-hot or categorical encoding) | No | No |
| `worldcover_class_name` | `worldcover_class_name` | Human-readable land-cover class name | `string` | Categorical | None ($0$ nulls) | Redundant with `worldcover_class` (use one) | No | No |
| `worldcover_status` | `worldcover_status` | Spatial join status flag (`valid`) | `string` | Single-valued | Constant; drop | No (constant) | No | No |

---

### 2.5 Sentinel-2 Spectral Features

| Feature Name | Source Column | Description | Data Type | Expected Range | Missing-Value Behavior | Safe for ML? | Potential Leakage? | Derived from Label? |
|---|---|---|---|---|---|---|---|---|
| `b02_blue_mean` | `b02_blue_mean` | Mean surface reflectance Band 2 (Blue, 490 nm) | `float64` | $[0, 10000]$ (Observed $[0, 1366]$) | $10$ nulls (cloudy/missing S2 scene); impute or use missing indicator | Yes | No | No |
| `b03_green_mean` | `b03_green_mean` | Mean surface reflectance Band 3 (Green, 560 nm) | `float64` | $[0, 10000]$ (Observed $[0, 1735]$) | $10$ nulls | Yes | No | No |
| `b04_red_mean` | `b04_red_mean` | Mean surface reflectance Band 4 (Red, 665 nm) | `float64` | $[0, 10000]$ (Observed $[0, 2405]$) | $10$ nulls | Yes | No | No |
| `b08_nir_mean` | `b08_nir_mean` | Mean surface reflectance Band 8 (NIR, 842 nm) | `float64` | $[0, 10000]$ (Observed $[0, 3464]$) | $10$ nulls | Yes | No | No |
| `b11_swir1_mean` | `b11_swir1_mean` | Mean surface reflectance Band 11 (SWIR1, 1610 nm) | `float64` | $[0, 10000]$ (Observed $[0, 3795]$) | $10$ nulls | Yes | No | No |
| `b12_swir2_mean` | `b12_swir2_mean` | Mean surface reflectance Band 12 (SWIR2, 2190 nm) | `float64` | $[0, 10000]$ (Observed $[0, 3276]$) | $10$ nulls | Yes | No | No |
| `b12_swir2_center` | `b12_swir2_center` | Center pixel reflectance Band 12 at event centroid | `float64` | $[0, 10000+]$ (Observed $[0, 11474]$) | $10$ nulls | Yes | No | No |
| `b12_swir2_bg_mean` | `b12_swir2_bg_mean` | Background ring reflectance Band 12 | `float64` | $[0, 10000]$ (Observed $[0, 3138]$) | $10$ nulls | Yes | No | No |
| `swir2_anomaly_ratio` | `swir2_anomaly_ratio` | Ratio of center SWIR2 to background SWIR2 | `float64` | $[0.0, 10.0+]$ (Observed $[0.0, 6.28]$) | $10$ nulls | Yes | No | No |
| `swir2_swir1_ratio` | `swir2_swir1_ratio` | Ratio of SWIR2 mean to SWIR1 mean | `float64` | $[0.0, 5.0]$ (Observed $[0.0, 2.02]$) | $10$ nulls | Yes | No | No |
| `ndvi` | `ndvi` | Normalized Difference Vegetation Index: $(B08-B04)/(B08+B04)$ | `float64` | $[-1.0, +1.0]$ (Observed $[-0.11, 0.84]$) | $11$ nulls | Yes | No | No |
| `nbr` | `nbr` | Normalized Burn Ratio: $(B08-B12)/(B08+B12)$ | `float64` | $[-1.0, +1.0]$ (Observed $[-0.63, 0.59]$) | $11$ nulls | Yes | No | No |
| `nbr2` | `nbr2` | Normalized Burn Ratio 2: $(B11-B12)/(B11+B12)$ | `float64` | $[-1.0, +1.0]$ (Observed $[-0.34, 0.37]$) | $11$ nulls | Yes | No | No |
| `bsi` | `bsi` | Bare Soil Index: $((B11+B04)-(B08+B02))/((B11+B04)+(B08+B02))$ | `float64` | $[-1.0, +1.0]$ (Observed $[-0.24, 0.26]$) | $11$ nulls | Yes | No | No |

---

### 2.6 Sentinel-2 Quality & Cloud Features

| Feature Name | Source Column | Description | Data Type | Expected Range | Missing-Value Behavior | Safe for ML? | Potential Leakage? | Derived from Label? |
|---|---|---|---|---|---|---|---|---|
| `scl_clear_fraction` | `scl_clear_fraction` | Scene Classification Layer (SCL) clear pixel fraction | `float64` | $[0.0, 1.0]$ | $10$ nulls; impute as $0.0$ | Yes | No | No |
| `scl_cloud_fraction` | `scl_cloud_fraction` | SCL cloud and shadow pixel fraction | `float64` | $[0.0, 1.0]$ | $10$ nulls; impute as $1.0$ | Yes | No | No |
| `satellite_cloud_cover_scene` | `satellite_cloud_cover_scene` | Full Sentinel-2 tile cloud cover percentage | `float64` | $[0.0, 100.0]$ | $4$ nulls | Yes | No | No |
| `observation_status` | `observation_status` | Status string (`successfully_enriched` vs missing scene) | `string` | Categorical | None ($0$ nulls); binary flag for missingness | Yes (as binary flag) | No | No |

---

### 2.7 Temporal Alignment Features

| Feature Name | Source Column | Description | Data Type | Expected Range | Missing-Value Behavior | Safe for ML? | Potential Leakage? | Derived from Label? |
|---|---|---|---|---|---|---|---|---|
| `temporal_delta_days` | `temporal_delta_days` | Difference in days between satellite acquisition and event start | `float64` | $[-14.0, +30.0]$ (Observed $[-5.1, 238.4]$) | $4$ nulls | Yes | No | No |
| `stac_search_start` | `stac_search_start` | Start timestamp of STAC imagery search query | `string` | ISO 8601 | None | No (pipeline artifact) | No | No |
| `stac_search_end` | `stac_search_end` | End timestamp of STAC imagery search query | `string` | ISO 8601 | None | No (pipeline artifact) | No | No |

---

### 2.8 Metadata & Identifier Fields (DO NOT USE AS ML FEATURES)

| Field Name | Source Column | Purpose | Reason for Exclusion from ML Features |
|---|---|---|---|
| `event_id` | `event_id` | Primary cluster key | High-cardinality unique identifier; non-generalizable. |
| `satellite_scene_id` | `satellite_scene_id` | Sentinel-2 scene tile product ID | Metadata string; tile-specific artifact. |
| `satellite_source` | `satellite_source` | STAC provider description | Constant string (`Sentinel-2 L2A AWS Open Data COG`). |
| `satellite_acq_datetime` | `satellite_acq_datetime` | Sentinel-2 acquisition timestamp | Timestamp string; use derived `temporal_delta_days` instead. |
| `first_detection` | `first_detection` | FIRMS first detection timestamp | Raw timestamp; extract seasonal day-of-year if needed, but exclude raw string. |
| `last_detection` | `last_detection` | FIRMS last detection timestamp | Raw timestamp; redundant with `first_detection` and `duration_days`. |
| `bbox_lat_min` / `bbox_lat_max` | Bounding box latitudes | Spatial extent boundaries | Redundant with `centroid_lat` and `spatial_extent_km2`. |
| `bbox_lon_min` / `bbox_lon_max` | Bounding box longitudes | Spatial extent boundaries | Redundant with `centroid_lon` and `spatial_extent_km2`. |
| `sampling_criteria_rationale` | Rationale string | Explanatory notes from pilot design | Unstructured text describing candidate filtering logic. |

---

## 3. STRICTLY PROHIBITED FIELDS (Target & Leakage Hazards)

The following fields **MUST NEVER** be introduced into the feature set:

| Prohibited Field | Reason for Strict Exclusion |
|---|---|
| `label` | **Target Variable**: Ground-truth class. Using it as a feature is trivial target leakage. |
| `label_confidence` | **Post-Label Annotation**: Reflects human certainty in the assigned label. Severe leakage. |
| `label_source` | **Post-Label Metadata**: Documents reviewer team or external citation source. Leakage. |
| `label_reason` | **Post-Label Rationale**: Textual justification explaining why the label was assigned. Severe leakage. |
| `review_status` | **Workflow Lifecycle State**: Tracks whether review is pending or finalized. Leakage. |
| `reviewed_at` | **Review Audit Timestamp**: Post-hoc timestamp of review action. Leakage. |
| `evidence_type` | **Human Review Field**: Identifies which external evidence was examined. Leakage. |
| `evidence_url` | **Human Review Field**: Citation URL for independent evidence. Leakage. |
| `evidence_notes` | **Human Review Field**: Human observations of incident context. Leakage. |
| `independent_evidence` | **Human Review Field**: Flag denoting external emergency reports. Leakage. |
| `conflicting_evidence` | **Human Review Field**: Human notes on conflicting evidence. Leakage. |
| `sampling_stratum` | **SAMPLING DESIGN BIAS HAZARD**: Stratum (`industrial_persistent`, `agricultural_ephemeral`, `forest_wildfire`) was assigned during candidate stratification. It is an artificial grouping variable, NOT physical ground truth, and must never be used as a predictor. |

---

## 4. Collinearity & Feature Redundancy Review

Before model training, the following pairs/groups of redundant features must be pruned or combined:

1. **Visible Reflectances**:
   - `b02_blue_mean`, `b03_green_mean`, and `b04_red_mean` exhibit pairwise Pearson correlations $r > 0.95$. Retain only one visible band (e.g. `b04_red_mean`) or compute a single visible brightness mean.
2. **FIRMS Persistence**:
   - `duration_days` and `distinct_detection_days` are strongly collinear ($r > 0.85$). Prefer `distinct_detection_days` as it is robust against long gaps with single isolated false alarms.
3. **FIRMS FRP Metrics**:
   - `frp_mean` and `frp_max` are highly correlated ($r > 0.88$). Retain `frp_max` (extreme combustion intensity) and optionally the ratio `frp_max / (frp_mean + 1e-3)`.
4. **Band 12 Derived Features**:
   - `b12_swir2_mean`, `b12_swir2_center`, and `b12_swir2_bg_mean` all characterize SWIR2 reflectance. `swir2_anomaly_ratio` effectively synthesizes center vs background contrast in a normalized metric, reducing the need for raw center and background levels.
5. **OSM Spatial Proximity**:
   - `min_distance_m`, `osm_proximity_fraction`, and `osm_containment_fraction` describe collinear proximity buffers. `min_distance_m` combined with `osm_containment_fraction` provides sufficient granular separation.
6. **Spectral Indices**:
   - `ndvi` and `nbr` both utilize $B08$ (NIR) and capture related vegetative density/moisture variations. Retaining `ndvi` (vegetation) and `nbr2` (SWIR1 vs SWIR2 dry matter) avoids singular matrix issues.
