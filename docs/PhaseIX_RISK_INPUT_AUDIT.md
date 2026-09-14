# ThermoGuard Phase IX — Risk Engine Input Audit

**Document Status**: INSPECTION ONLY — No datasets modified, no models trained, no scores computed.

**Inspection Date**: 2026-09-14

**Dataset inspected**:
- `data/satellite/processed/firms_satellite_enriched_pilot.parquet` — N=100 events, 55 columns
- `data/satellite/processed/thermoguard_ml_features_pilot.parquet` — N=100 events, 43 columns
- `data/satellite/processed/firms_ground_truth_pilot.parquet` — N=100 events, 12 columns
- `models/logistic_regression_baseline.joblib` and `models/random_forest_baseline.joblib`

---

## 1. Full Field Audit Table

**Column legend for `usable_for_risk`**:
- **A** — Safe risk input (direct evidence signal, no leakage)
- **B** — Context only (metadata, spatial reference, not a scored signal)
- **C** — Ground-truth / evaluation only (MUST NOT be used for operational risk scoring)
- **D** — Potential leakage (derived from or correlated with ground-truth strata)
- **E** — Missing / not currently available in this pipeline

### 1.1 FIRMS Temporal and Persistence Features

| field | source | meaning | usable_for_risk | reason | leakage_risk |
|---|---|---|---|---|---|
| `duration_days` | firms_satellite_enriched | Days from first to last FIRMS detection | **A** | Direct physical persistence signal — longer duration = higher concern for industrial permanence | None |
| `detection_count` | firms_satellite_enriched | Total raw FIRMS detections across the event lifetime | **A** | Volume of thermal detections; higher values suggest established heat source | None |
| `distinct_detection_days` | firms_satellite_enriched | Number of unique calendar days with at least one FIRMS detection | **A** | Strongest persistence signal; near-perfectly correlated with `duration_days` (r=1.00) — see duplication note | None |
| `distinct_satellites` | firms_satellite_enriched | Number of distinct satellite platforms that detected the event | **A** | Multi-satellite corroboration increases detection reliability | None |
| `distinct_instruments` | firms_satellite_enriched | Number of distinct sensor instruments | **B** | Redundant with `distinct_satellites` in this dataset (only MODIS/VIIRS); retain as context | Low |
| `first_detection` | firms_satellite_enriched | Timestamp of earliest detection | **B** | Context/metadata for event timeline; not a scored signal in itself | None |
| `last_detection` | firms_satellite_enriched | Timestamp of most recent detection | **B** | Context/metadata; use with `first_detection` to derive `duration_days` | None |
| `frp_confidence` | firms_satellite_enriched | FIRMS per-detection confidence level | **E** | **Field not present** in any current pipeline output. Original FIRMS raw confidence was not aggregated into the event-level dataset during Phase III clustering. | N/A |
| `frp_std` | firms_satellite_enriched | Standard deviation of FRP across detections | **E** | **Not computed**. A high FRP variance would indicate pulsed vs. continuous thermal activity. | N/A |

### 1.2 FIRMS Thermal Intensity Features

| field | source | meaning | usable_for_risk | reason | leakage_risk |
|---|---|---|---|---|---|
| `frp_mean` | firms_satellite_enriched | Mean Fire Radiative Power (MW) across all detections | **A** | Core thermal intensity signal; negatively correlated with persistence (r=-0.67) — see note | None |
| `frp_max` | firms_satellite_enriched | Maximum FRP (MW) across all detections | **A** | Peak thermal event magnitude; captures episodic vs. steady thermal behaviour | None |
| `brightness_mean` | firms_satellite_enriched | Mean FIRMS brightness temperature (K) | **A** | Thermal emission intensity; range 307-367 K in this dataset | None |

### 1.3 FIRMS Spatial Features

| field | source | meaning | usable_for_risk | reason | leakage_risk |
|---|---|---|---|---|---|
| `spatial_extent_km2` | firms_satellite_enriched | Bounding-box area of all detections for the event (km2) | **A** | Larger extents may indicate wildfire spread; smaller concentrated extents suggest point industrial sources | None |
| `centroid_lat` | firms_satellite_enriched | Centroid latitude of event | **B** | Geographic reference -- not a risk signal in isolation but enables proximity and regional context | None |
| `centroid_lon` | firms_satellite_enriched | Centroid longitude of event | **B** | As above | None |
| `bbox_lat_min/max` | firms_satellite_enriched | Bounding box bounds | **B** | Metadata / spatial reference only | None |
| `bbox_lon_min/max` | firms_satellite_enriched | Bounding box bounds | **B** | Metadata / spatial reference only | None |

### 1.4 OSM Infrastructure Features

| field | source | meaning | usable_for_risk | reason | leakage_risk |
|---|---|---|---|---|---|
| `has_osm_industrial_match` | firms_satellite_enriched (derived) | Binary: 1 if any OSM industrial feature matches the event footprint | **A** | Strong industrial context indicator; 40% of pilot events match. `min_distance_m=0` for 39 events. | None |
| `osm_matched_fraction` | firms_satellite_enriched | Fraction of event detections overlapping any OSM industrial polygon | **A** | Graduated spatial overlap -- more nuanced than binary flag | None |
| `osm_containment_fraction` | firms_satellite_enriched | Fraction of event footprint contained within an OSM industrial polygon | **A** | Measures how fully the thermal event is enclosed by an industrial feature | None |
| `osm_proximity_fraction` | firms_satellite_enriched | Fraction of detections within proximity threshold of an OSM feature | **A** | Near-field context even when not fully contained | None |
| `min_distance_m` | firms_satellite_enriched | Distance in metres from event centroid to nearest OSM industrial feature | **A** | Proximity metric; 60 events have null (no OSM match found -- requires imputation at score time) | None |
| `osm_tier` | firms_satellite_enriched | Tier classification of matched OSM facility (1=primary, 2=secondary) | **A** | Tier 1 = directly mapped industrial polygon; available for 40 events, null for 60 | Low |
| `osm_primary_category` | firms_satellite_enriched | High-level OSM facility category: mine_quarry, industrial_area, factory_works, substation, power_plant | **A** | Categorical risk context -- should remain categorical (not one-hot collapsed). Null 60% of events. | None |
| `osm_sub_category` | firms_satellite_enriched | Fine-grained OSM category: coal, industrial_area, works, quarry, steel_mill, etc. | **A** | More specific industrial type signal -- should remain categorical | None |
| `osm_facility_density` | external | Count of industrial facilities within N-km buffer | **E** | **Not computed**. Only the nearest OSM feature is captured. Density would strengthen context for clustered industrial zones. | N/A |

### 1.5 ESA WorldCover Features

| field | source | meaning | usable_for_risk | reason | leakage_risk |
|---|---|---|---|---|---|
| `worldcover_class` | firms_satellite_enriched | ESA WorldCover land-cover class integer code (e.g., 10=Tree cover, 40=Cropland, 50=Built-up, 60=Bare/sparse) | **A** | Direct land-cover evidence. 100% coverage. Encode as categorical -- raw integer class codes have no ordinal meaning. | None |
| `worldcover_class_name` | firms_satellite_enriched | Human-readable WorldCover class name | **A** | Categorical -- retain as primary form. Numeric code and name are redundant; use one. | None |
| `worldcover_status` | firms_satellite_enriched | Validity flag for WorldCover extraction | **B** | Always "valid" in this dataset (100%). Drop as uninformative constant. | None |

### 1.6 Sentinel-2 Spectral Features

| field | source | meaning | usable_for_risk | reason | leakage_risk |
|---|---|---|---|---|---|
| `b02_blue_mean` | firms_satellite_enriched | Mean reflectance B02 (Blue, 490 nm) over event footprint | **B** | Raw band reflectance -- high correlation with other bands; derived indices (NDVI, NBR, BSI) already capture its information | Low |
| `b03_green_mean` | firms_satellite_enriched | Mean reflectance B03 (Green, 560 nm) | **B** | As above | Low |
| `b04_red_mean` | firms_satellite_enriched | Mean reflectance B04 (Red, 665 nm) | **B** | As above | Low |
| `b08_nir_mean` | firms_satellite_enriched | Mean reflectance B08 (NIR, 842 nm) | **B** | Needed for NDVI; already captured. Use index directly. | Low |
| `b11_swir1_mean` | firms_satellite_enriched | Mean reflectance B11 (SWIR1, 1610 nm) | **B** | Input to swir2_swir1_ratio; already captured | Low |
| `b12_swir2_mean` | firms_satellite_enriched | Mean reflectance B12 (SWIR2, 2190 nm) over event footprint window | **A** | Direct high-temperature emission indicator; useful alongside anomaly ratio | None |
| `b12_swir2_center` | firms_satellite_enriched | B12 reflectance at the hotspot centre pixel | **A** | Peak SWIR2 at exact thermal centre -- complements the mean | None |
| `b12_swir2_bg_mean` | firms_satellite_enriched | Background B12 mean (spatial reference) | **B** | Used to compute `swir2_anomaly_ratio`; not needed directly once ratio is computed | Low |
| `swir2_anomaly_ratio` | firms_satellite_enriched | Ratio of centre B12 to background B12 (hotspot contrast) | **A** | Best single Sentinel-2 thermal anomaly signal. Range 0-6.3 in pilot dataset. Threshold >=1.0 suggests active thermal anomaly. | None |
| `swir2_swir1_ratio` | firms_satellite_enriched | B12/B11 ratio across event footprint | **A** | Fire/combustion spectral signature ratio; highly correlated with nbr2 (r=0.98) -- see duplication note | None |
| `ndvi` | firms_satellite_enriched | Normalized Difference Vegetation Index | **A** | Vegetation density context -- important for wildfire vs. industrial discrimination. 11% null rate. | None |
| `nbr` | firms_satellite_enriched | Normalized Burn Ratio (NIR-SWIR2)/(NIR+SWIR2) | **A** | Post-fire severity indicator; highly correlated with ndvi (r=0.89) and nbr2 (r=0.93) -- see duplication note | None |
| `nbr2` | firms_satellite_enriched | NBR2 (SWIR1-SWIR2)/(SWIR1+SWIR2) | **A** | Burn scar / soil moisture indicator; near-perfectly correlated with swir2_swir1_ratio (r=-0.98) -- see duplication note | None |
| `bsi` | firms_satellite_enriched | Bare Soil Index | **A** | Identifies bare / disturbed soil contexts (mining, construction). Useful contextual signal. | None |

### 1.7 Sentinel-2 Quality and Temporal Features

| field | source | meaning | usable_for_risk | reason | leakage_risk |
|---|---|---|---|---|---|
| `has_spectral_features` | firms_satellite_enriched (derived) | Binary flag: 1 if spectral features successfully extracted | **A** | Inverse confidence weight: when 0, all spectral contributions to risk score must be nulled | None |
| `has_satellite_scene` | firms_satellite_enriched (derived) | Binary flag: 1 if any Sentinel-2 scene was found in STAC | **A** | Scene availability indicator; 96% coverage in this dataset | None |
| `satellite_cloud_cover_scene` | firms_satellite_enriched | Cloud cover fraction at scene level (0-1) | **A** | Scene-level quality; events with `satellite_cloud_cover_scene > 0.5` have degraded spectral reliability | None |
| `scl_clear_fraction` | firms_satellite_enriched | Fraction of clear (unobstructed) pixels in the event footprint (SCL-derived) | **A** | Pixel-level quality mask; higher fraction = more reliable spectral measurements | None |
| `scl_cloud_fraction` | firms_satellite_enriched | Fraction of cloudy pixels in the event footprint | **A** | Complement of `scl_clear_fraction`; highly correlated -- use one | None |
| `temporal_delta_days` | firms_satellite_enriched | Days between FIRMS event active period and Sentinel-2 acquisition date | **A** | Temporal relevance qualifier -- large delta (e.g., >90 days) reduces spectral signal reliability for active event assessment | None |
| `satellite_scene_id` | firms_satellite_enriched | Sentinel-2 scene identifier | **B** | Metadata / provenance -- not a risk signal | None |
| `satellite_acq_datetime` | firms_satellite_enriched | Sentinel-2 scene acquisition datetime | **B** | Metadata; useful for temporal delta computation | None |
| `satellite_source` | firms_satellite_enriched | Data source label (Sentinel-2 L2A via AWS) | **B** | Metadata; constant in this dataset | None |
| `observation_status` | firms_satellite_enriched | Enrichment status: successfully_enriched, band_window_read_error, stac_no_scene_found | **B** | Pipeline diagnostics -- determines whether spectral features are reliable. 10 events have errors. | None |
| `stac_search_start` / `stac_search_end` | firms_satellite_enriched | STAC search window timestamps | **B** | Metadata only | None |

### 1.8 ML Model Outputs

| field | source | meaning | usable_for_risk | reason | leakage_risk |
|---|---|---|---|---|---|
| `predicted_class` (LR/RF) | classify_event.py | Predicted domain category: agricultural_ephemeral, forest_wildfire, industrial_persistent | **A** | Useful as a composite risk input -- model encodes pattern across many features. Must treat as **one signal**, not definitive truth. | Low-Moderate: model trained on surrogate labels (sampling_stratum), not human ground truth |
| `class_probability_industrial` | classify_event.py | Predicted probability of industrial_persistent class | **A** | Continuous risk-relevant probability; more informative than predicted class alone | Same as above |
| `class_probability_agricultural` | classify_event.py | Predicted probability of agricultural_ephemeral class | **A** | Inverse industrial signal | Same as above |
| `class_probability_wildfire` | classify_event.py | Predicted probability of forest_wildfire class | **A** | Wildfire flag -- useful for risk tier differentiation | Same as above |
| `model_version` | classify_event.py | Model version string (v0.1-baseline-pilot) | **B** | Provenance / audit metadata | None |
| `top_contributing_features` | classify_event.py | Feature importance list (global Gini) | **B** | Explanation artifact -- not a scored risk input | None |

### 1.9 Ground Truth Fields (Evaluation Only -- MUST NOT be used as risk inputs)

| field | source | meaning | usable_for_risk | reason | leakage_risk |
|---|---|---|---|---|---|
| `label` | firms_ground_truth_pilot | Human expert classification | **C** | EVALUATION ONLY. Ground-truth label must never feed into the operational risk score; it is the validation target, not an input. | **CRITICAL** |
| `label_confidence` | firms_ground_truth_pilot | Human-assigned label confidence (high/medium/low) | **C** | EVALUATION ONLY. Same leakage concern as `label`. | **CRITICAL** |
| `label_source` | firms_ground_truth_pilot | How the label was assigned | **C** | EVALUATION ONLY | **CRITICAL** |
| `label_reason` | firms_ground_truth_pilot | Free-text rationale from human reviewer | **C** | EVALUATION ONLY | **CRITICAL** |
| `review_status` | firms_ground_truth_pilot | Review workflow status (pending/reviewed/final) | **C** | EVALUATION ONLY | **CRITICAL** |
| `reviewed_at` | firms_ground_truth_pilot | Timestamp of human review | **C** | EVALUATION ONLY | **CRITICAL** |
| `sampling_stratum` | firms_satellite_enriched / firms_ground_truth_pilot | Domain category used for pilot sampling strategy | **D** | **Potential leakage**: this field was used as the ML model's surrogate training target. Including it in a risk score would be direct leakage of a label-proxy. | **HIGH** |

---

## 2. Missing Evidence Fields

The following evidence signals are scientifically valuable for a ThermoGuard risk engine but are **not currently available** in any pipeline output:

| missing_field | evidence_value | pipeline_gap |
|---|---|---|
| FIRMS per-detection confidence | Distinguishes nominal vs. low confidence FIRMS detections; important for weighting | Not aggregated during Phase III event clustering |
| FRP standard deviation | Would distinguish pulsed (episodic burning) from stable (industrial) thermal sources | Not computed during clustering |
| FRP time-series / trend | Temporal pattern of FRP changes (growing, steady, declining) would directly discriminate industrial vs. fire | Not stored -- only aggregate statistics retained |
| OSM facility density (buffer) | Count of industrial facilities within 1 km, 5 km, 10 km buffers | Only nearest facility captured; no density metric |
| OSM facility area | Polygon area of the matched industrial feature | Not extracted from OSM |
| Nighttime light (NTL) | VIIRS-DNB nighttime light intensity at event location | Not integrated |
| Terrain / elevation | DEM-derived slope and aspect (steeper terrain disfavours fixed industrial operations) | Not integrated |
| Population density | High population density near thermal events increases risk severity | Not integrated |
| Wind / atmospheric | Smoke plume direction affects downwind exposure | Not integrated |
| FIRMS raw confidence level | Raw FIRMS detection quality flag (low/nominal/high) per detection | Dropped during aggregation |

---

## 3. Duplicate and Highly Correlated Signals

Based on the empirical Pearson correlation matrix computed from the pilot dataset, the following field groups contain redundant information. A risk engine should select **one representative** from each group to avoid over-weighting correlated signals:

| group | fields | max_correlation | recommendation |
|---|---|---|---|
| Persistence cluster | `duration_days`, `distinct_detection_days` | r = 1.00 | Near-perfect duplicates. **Use `distinct_detection_days`** (more interpretable; directly counts calendar days with observations) |
| Burn index cluster | `nbr2`, `swir2_swir1_ratio` | r = -0.98 | Near-perfect anti-correlation (same phenomenon, opposite sign convention). **Use `swir2_swir1_ratio`** or `nbr2`, not both |
| Vegetation/burn cluster | `ndvi`, `nbr`, `nbr2` | r = 0.89-0.93 | High mutual correlation. `nbr` captures fire severity; `ndvi` captures vegetation context. **Retain `ndvi` + `swir2_swir1_ratio`; drop `nbr2` and `nbr`** |
| Detection volume cluster | `detection_count`, `spatial_extent_km2` | r = 0.85 | Strong correlation. Both reflect event scale. **Retain both** but apply log-normalisation; they measure different dimensions (time-volume vs. space) |
| Raw band cluster | `b02`, `b03`, `b04`, `b08`, `b11` | >0.70 mutual | Raw visible/NIR bands are already captured by their derived indices. **Drop raw bands from risk score; use derived indices only** |
| Quality complement | `scl_clear_fraction`, `scl_cloud_fraction` | r ~= -1.00 | Perfect complements. **Use `scl_clear_fraction` only** |

---

## 4. Normalisation Requirements

Fields requiring normalisation before use in a weighted risk scoring formula:

| field | current_range | normalisation_needed | method |
|---|---|---|---|
| `duration_days` | 0 - 388 | Yes -- extreme right skew | Log transform then min-max to [0,1] |
| `detection_count` | 1 - 21,883 | Yes -- extreme right skew | Log transform then min-max to [0,1] |
| `distinct_detection_days` | 1 - 343 | Yes -- same distribution as duration_days | Log transform then min-max to [0,1] |
| `spatial_extent_km2` | 0 - 88.6 | Yes -- right skew | Log transform then min-max |
| `frp_mean` | 1.26 - 57.4 MW | Yes | Min-max or z-score |
| `frp_max` | 8.4 - 381.6 MW | Yes -- extreme outliers | Winsorised min-max (cap at 99th percentile) |
| `brightness_mean` | 307 - 367 K | Minor -- relatively narrow | Min-max to [0,1] |
| `min_distance_m` | 0 - 89,590 m | Yes -- right skew, 60% null | Invert (proximity = 1 - normalised distance); null -> 0 (no proximity evidence) |
| `swir2_anomaly_ratio` | 0 - 6.3 | Yes -- threshold at 1.0, clip outliers | Subtract 1.0, clip to [0, 5], then normalise to [0,1] |
| `temporal_delta_days` | -5 - 238 | Yes -- used as reliability weight | Clip to [0, 90], invert to form reliability score |

---

## 5. Thresholding Requirements

Fields where a threshold separates signal from noise:

| field | threshold | interpretation |
|---|---|---|
| `swir2_anomaly_ratio` | >= 1.0 | Below 1.0 = no thermal anomaly above background. Score contribution = 0 below threshold. |
| `satellite_cloud_cover_scene` | > 0.5 | High cloud cover degrades spectral reliability. Spectral contributions should be down-weighted. |
| `scl_clear_fraction` | < 0.5 | Less than half of pixels clear -- spectral features are unreliable. |
| `temporal_delta_days` | > 90 days | Scene acquired >90 days from event active period -- spectral relevance declines sharply. |
| `min_distance_m` | > 5,000 m | Beyond 5 km from nearest industrial feature, proximity contribution to industrial risk -> 0. |
| `duration_days` | >= 7 days | Minimum threshold for persistent thermal classification. Events <7 days should receive reduced persistence weight. |
| `has_spectral_features` | == 0 | All Sentinel-2 spectral contributions to risk score must be set to 0 for this event. |

---

## 6. Fields That Should Remain Categorical

The following fields must NOT be converted to ordinal numeric values in the risk engine:

| field | reason |
|---|---|
| `osm_primary_category` | Categories (mine_quarry, industrial_area, factory_works, power_plant, substation) have no linear ordering. Risk weights per category should be explicitly assigned by domain experts. |
| `osm_sub_category` | Fine-grained industrial type -- same reasoning. coal mine does not equal solar facility in any linear sense. |
| `worldcover_class_name` | Land-cover class codes (10=Tree, 40=Cropland, 50=Built-up, 60=Bare) are nominal, not ordinal. |
| `predicted_class` | Model output class is categorical; use `class_probability_industrial` as the continuous form. |

---

## 7. Summary: Field Classification by Risk Role

| category | count | fields (abbreviated) |
|---|---|---|
| **A -- Safe risk inputs** | 28+ | `duration_days`, `detection_count`, `distinct_detection_days`, `spatial_extent_km2`, `distinct_satellites`, `frp_mean`, `frp_max`, `brightness_mean`, `has_osm_industrial_match`, `osm_matched_fraction`, `osm_containment_fraction`, `osm_proximity_fraction`, `min_distance_m`, `osm_tier`, `osm_primary_category`, `osm_sub_category`, `worldcover_class`, `worldcover_class_name`, `b12_swir2_mean`, `b12_swir2_center`, `swir2_anomaly_ratio`, `swir2_swir1_ratio`, `ndvi`, `nbr`, `nbr2`, `bsi`, `has_spectral_features`, `has_satellite_scene`, `satellite_cloud_cover_scene`, `scl_clear_fraction`, `temporal_delta_days`, ML class probabilities |
| **B -- Context only** | 14 | `centroid_lat`, `centroid_lon`, `bbox_*`, `first_detection`, `last_detection`, `distinct_instruments`, raw bands b02/b03/b04/b08/b11, `b12_swir2_bg_mean`, `scl_cloud_fraction`, `satellite_scene_id`, `satellite_acq_datetime`, `satellite_source`, `observation_status`, `worldcover_status`, `stac_*`, `model_version`, `top_contributing_features` |
| **C -- Ground-truth / evaluation only** | 6 | `label`, `label_confidence`, `label_source`, `label_reason`, `review_status`, `reviewed_at` |
| **D -- Potential leakage** | 1 | `sampling_stratum` |
| **E -- Missing / not available** | 10 | `frp_confidence`, `frp_std`, `frp_timeseries`, `osm_facility_density`, `osm_facility_area`, nighttime lights, terrain/elevation, population density, wind/atmospheric, FIRMS raw confidence level |

---

## 8. Phase IX Input Status

```
PHASE IX INPUT STATUS: READY WITH LIMITATIONS
```

### Evidence for READY:
- 28+ safe risk input fields are available with 0-11% null rates across 100 pilot events.
- FIRMS persistence, thermal intensity, spatial extent, and temporal behaviour are fully populated (0% null).
- WorldCover land-cover is 100% available.
- OSM infrastructure context is available for 40% of events (the 60% null rate reflects genuine absence of mapped industrial infrastructure, not a pipeline error).
- Sentinel-2 spectral features are available for 90% of events (10% failures due to cloud/STAC availability).
- ML classification probabilities are computable on demand for all 100 events via `classify_event.py`.

### Evidence for LIMITATIONS:
1. **No human ground-truth labels** (100% null in `firms_ground_truth_pilot.parquet`) -- risk score validation against human-reviewed labels is not yet possible.
2. **OSM coverage gap**: 60% of events have null OSM fields. Risk engine must handle absent OSM context gracefully (default = no industrial proximity evidence, not zero risk).
3. **Temporal gap in Sentinel-2**: `temporal_delta_days` ranges 0-238 days; approximately 30 events exceed a 90-day relevance threshold. Spectral signals for those events have reduced reliability.
4. **ML model uses surrogate labels** (`sampling_stratum`, not human ground truth). Model class probabilities reflect geographic clustering patterns, not expert-validated classification.
5. **Highly correlated signals** identified (see Section 3) -- final weight design must avoid double-counting persistence and burn-index signals.
6. **Missing key signals**: FIRMS per-detection confidence, FRP temporal trends, and facility density are absent and would materially strengthen risk discrimination.

### NOT BLOCKED:
Risk engine design can proceed using Category A fields. Final validation will require completion of Phase VI human labeling.

---

*This document was generated from direct inspection of repository datasets. No values are invented. No model was trained. No dataset was modified.*
