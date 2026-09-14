# ThermoGuard Phase VII — Feature Dataset Report

This report documents the generation, validation, and audit of the machine-learning-ready feature dataset (`thermoguard_ml_features_pilot.parquet`) synthesized in Phase VII from existing enriched satellite, OSM, and WorldCover evidence joined with human ground-truth records.

---

## 1. Dataset Dimensions & Accounting

| Metric | Count | Details |
|---|---|---|
| **Input Rows (Enriched Evidence)** | 100 | Source: `firms_satellite_enriched_pilot.parquet` |
| **Input Rows (Ground-Truth Table)** | 100 | Source: `firms_ground_truth_pilot.parquet` |
| **Output Dataset Rows** | **100** | Preserved 100% of pilot candidate events |
| **Excluded Rows** | **0** | No events were dropped or filtered |
| **Feature Count** | **41** | 41 predictive ML input features |
| **Identifier Fields** | 1 | `event_id` (primary key; excluded from model training) |
| **Target Variable Count** | 1 | `target_label` (human ground-truth label) |

---

## 2. Feature Types & Distribution

The 41 model features span numerical, discrete, and categorical data types:

| Feature Group | Features | Data Types | Imputation / Preprocessing Strategy |
|---|---|---|---|
| **FIRMS Temporal & Spatial (8)** | `duration_days`, `detection_count`, `distinct_detection_days`, `spatial_extent_km2`, `distinct_satellites`, `distinct_instruments`, `centroid_lat`, `centroid_lon` | `float64`, `int64`, `int32` | No missing values; continuous and discrete counts. |
| **FIRMS Thermal (3)** | `frp_mean`, `frp_max`, `brightness_mean` | `float64` | No missing values; radiant fire power and channel brightness. |
| **OSM Infrastructure (8)** | `has_osm_industrial_match`, `min_distance_m`, `osm_matched_fraction`, `osm_containment_fraction`, `osm_proximity_fraction`, `osm_tier`, `osm_primary_category`, `osm_sub_category` | `int32`, `float64`, `string` | 60 events lack industrial features within search radius: `has_osm_industrial_match` flag set to 0, `min_distance_m` imputed to 10,000m, `osm_tier` imputed to 0, categories set to `'none'`. |
| **ESA WorldCover (2)** | `worldcover_class`, `worldcover_class_name` | `int64`, `string` | 0 missing values; discrete 10m land cover classification. |
| **Sentinel-2 Spectral (15)** | `has_spectral_features`, `b02_blue_mean`, `b03_green_mean`, `b04_red_mean`, `b08_nir_mean`, `b11_swir1_mean`, `b12_swir2_mean`, `b12_swir2_center`, `b12_swir2_bg_mean`, `swir2_anomaly_ratio`, `swir2_swir1_ratio`, `ndvi`, `nbr`, `nbr2`, `bsi` | `int32`, `float64` | 10 events lack clear S2 scene; 1 additional event has edge/null spectral index. `has_spectral_features` binary flag set to 0 for missing rows. Raw reflectances retained for model imputers. |
| **Sentinel-2 Quality & Cloud (4)** | `has_satellite_scene`, `satellite_cloud_cover_scene`, `scl_clear_fraction`, `scl_cloud_fraction` | `int32`, `float64` | Missing S2 tiles imputed with conservative values (clear=0.0, cloud=1.0). |
| **Temporal Alignment (1)** | `temporal_delta_days` | `float64` | Days between S2 pass and active cluster (imputed to 999.0 when scene missing). |

---

## 3. Missing Value Audit

Of the 41 features, 27 features have **0** missing values. The remaining 14 features have expected missingness due to physical observation limitations (cloud cover or absence of clear Sentinel-2 scenes):

| Feature Name | Missing Count | % Missing | Root Cause & Handled Strategy |
|---|---|---|---|
| `b02_blue_mean` ... `b12_swir2_mean` (10 bands/ratios) | 10 | 10.0% | No cloud-free Sentinel-2 L2A tile available within 7-day window. Flagged by `has_spectral_features = 0`. |
| `ndvi`, `nbr`, `nbr2`, `bsi` | 11 | 11.0% | 10 cloudy scenes + 1 edge-of-swath tile calculation boundary. Flagged by `has_spectral_features = 0`. |

*Note: All OSM missing values were explicitly handled via indicator `has_osm_industrial_match` and distance default ($10,000\text{ m}$), eliminating silent data loss.*

---

## 4. Leakage Prevention Verification

A comprehensive automated assertion check confirmed zero feature leakage:

- [x] **`sampling_stratum` EXCLUDED**: Confirmed absent from feature columns (preventing sampling design bias).
- [x] **Review metadata EXCLUDED**: `review_status`, `reviewed_at`, `label_confidence`, `label_source`, and `label_reason` are strictly excluded.
- [x] **Evidence annotations EXCLUDED**: `evidence_type`, `evidence_url`, `evidence_notes`, `independent_evidence`, and `conflicting_evidence` are strictly excluded.
- [x] **Temporal leakage EXCLUDED**: STAC query timestamps and pipeline artifacts are excluded.
- [x] **Target Isolation**: Target variable `target_label` is isolated from the feature matrix.

---

## 5. Label Distribution

- **Total Target Rows**: 100
- **Populated Labels**: 0 (0.0%)
- **Null / Unassigned Labels**: 100 (100.0%)

*Supervised classifier training remains strictly deferred pending human review finalization according to the Phase VI-B labeling protocol.*
