# ThermoGuard Phase IX — Risk Engine Methodology

**Document Status**: DESIGN ONLY — No datasets modified, no models trained, no scores calculated, no real event classified.

**Design Date**: 2026-09-14

**Input reference**: `docs/PhaseIX_RISK_INPUT_AUDIT.md`

**Repository basis**: `firms_satellite_enriched_pilot.parquet` (N=100), `thermoguard_ml_features_pilot.parquet` (N=100)

---

## 1. Purpose

ThermoGuard is a satellite-based evidence aggregation system that identifies thermal events of potential environmental or regulatory concern — primarily persistent industrial heat sources, large-scale agricultural burning, and uncontrolled wildfires — across India.

The **ThermoGuard Risk Score** is a structured, explainable, evidence-weighted indicator (0–100) that summarises the available multi-source satellite evidence for a given thermal event. It is designed for:

- **Environmental monitoring**: Flagging persistent industrial thermal sources for regulatory follow-up.
- **Analyst triage**: Prioritising which events warrant deeper human investigation.
- **Audit trail**: Providing a traceable, field-level justification for every score.

### What the risk score is NOT

See Section 13 (Do Not Claim) for the complete list. In brief:

- It is NOT a fire detection truth label.
- It is NOT proof of illegal activity.
- It is NOT a replacement for emergency response systems.
- It is NOT produced by a validated model trained on human ground truth.

---

## 2. Risk vs. Evidence Confidence — Fundamental Distinction

The ThermoGuard system maintains **two strictly separate outputs** for every event. These represent distinct concepts and must never be merged into a single number.

### 2.1 Risk Score (0–100)

**Definition**: Strength of observed physical and contextual evidence indicating an event of potential regulatory or environmental concern (0–100).

- A **HIGH** risk score indicates strong, convergent physical observations of sustained thermal power, long-term persistence, close industrial spatial association, notable event scale, and optical/SWIR surface contrast.
- A **LOW** risk score indicates that available evidence does not show concerning thermal or spatial characteristics — it does **not** confirm that the location is benign or safe.

### 2.2 Evidence Confidence (0–100 or LOW / MEDIUM / HIGH)

**Definition**: Completeness, corroboration, and quality/reliability of available evidence across data sources (0–100).

- Evidence Confidence measures whether data is present, timely, clear-sky, and multi-sensor corroborated (including multi-platform satellite observations via `distinct_satellites`).
- **Confidence is NOT class probability.** It is not a model certainty metric, posterior probability, or fire truth likelihood.
- A **HIGH** evidence confidence means: FIRMS thermal observations, Sentinel-2 optical/SWIR spectral imagery, and OSM vector layers are all available, temporally aligned, cloud-free, and corroborated.
- A **LOW** evidence confidence means: imagery is missing, cloudy, temporally distant (>90 days), or infrastructure context is absent.

### 2.3 Why they must be separate

| Risk Score | Evidence Confidence | Operational Interpretation |
|---|---|---|
| HIGH | HIGH | Strong, well-supported concern with robust evidence base — prioritised for investigation |
| HIGH | LOW | Concerning signals observed, but evidence base is incomplete or degraded — flag for data acquisition |
| MODERATE | HIGH | Well-evidenced moderate concern — regular monitoring |
| LOW | HIGH | Well-evidenced low concern — robust observation showing minimal concern |
| LOW | LOW | Insufficient evidence to assess — do NOT treat as confirmed safe; data gap |

> [!IMPORTANT]
> A LOW risk score coupled with a LOW evidence confidence score does NOT confirm an event is benign. It indicates an **inability to adequately assess** the event due to missing or degraded observations.

---

## 3. Evidence Dimensions

The risk score is composed of **five core evidence dimensions** summing to exactly 100%. Each dimension captures a distinct physical or spatial aspect of the event and is normalized to [0, 1] (or 0–100) prior to weighted aggregation.

| Dimension | Dimension Name | Weight | Physical / Contextual Meaning | Primary Data Source |
|---|---|---|---|---|
| A | Thermal Intensity | **30%** | Sustained and peak radiated thermal energy | FIRMS (FRP, brightness temperature) |
| B | Persistence | **25%** | Recurrence and temporal longevity of thermal activity | FIRMS temporal fields (distinct detection days, counts) |
| C | Industrial / Contextual Association | **20%** | Observed spatial proximity, containment, and footprint match to mapped industrial facilities | OpenStreetMap (OSM) spatial metrics |
| D | Spatial Scale | **10%** | Physical footprint and geographic extent of the thermal anomaly cluster | FIRMS spatial cluster extent (`spatial_extent_km2`) |
| E | Spectral / Surface Evidence | **15%** | Surface reflectance contrast and surface disturbance from optical/SWIR imagery | Sentinel-2 MSI (B11/B12 SWIR contrast, NDVI, BSI) |
| — | **Total** | **100%** | **Comprehensive Evidence-Weighted Risk Score** | — |

### Contextual Information (Not Scored for Risk)

- **Land-Cover Context (ESA WorldCover)**: **CONTEXT ONLY (0% risk weight)**. Land cover describes the baseline landscape environment (e.g., Built-up, Cropland, Tree cover). It is used strictly for contextual explanations and qualitative reporting. It has **no multiplicative or additive effect** on the numerical risk score.
- **Satellite Platform Corroboration (`distinct_satellites`)**: **EVIDENCE CONFIDENCE ONLY (0% risk weight)**. The number of observing satellite platforms indicates multi-sensor corroboration and reliability. It is incorporated into the Evidence Confidence indicator, not into physical risk scoring.

---

## 4. Feature Selection and Rationale

Based on the Phase IX Input Audit, the following features are selected as inputs to each dimension. Highly correlated redundant fields identified in the audit are de-duplicated.

### Dimension A: Thermal Intensity

| feature | field | rationale |
|---|---|---|
| FRP mean | `frp_mean` | Primary continuous thermal intensity signal. Mean over all detections captures sustained power level. |
| FRP peak | `frp_max` | Captures peak thermal episodes; complementary to mean — two events with equal mean can differ greatly in peak. |
| Brightness temperature | `brightness_mean` | FIRMS mid-infrared brightness temperature; narrow range (307-367 K in pilot) but provides independent corroboration of thermal intensity. |

**Excluded**: `frp_std` (not available in current pipeline — see audit Section 2).

### Dimension B: Persistence

**Primary feature**: `distinct_detection_days`

**Rationale**: As documented in the audit (r=1.00 with `duration_days`), these two fields are near-perfect duplicates. `distinct_detection_days` is selected because it directly counts calendar days with active satellite observations, is robust to gaps in the observation window, and is more interpretable than a computed interval between first/last detection timestamps.

`detection_count` is used as a secondary signal within this dimension because it captures detection frequency/density within the active days — two events with 30 distinct days may have very different detection counts, indicating different intensity profiles.

**Excluded from persistence**: `duration_days` (duplicate of `distinct_detection_days`).

### Dimension C: Industrial / Contextual Association

| feature | field | rationale |
|---|---|---|
| Binary match | `has_osm_industrial_match` | Strongest single industrial presence indicator; 40% of pilot events match |
| Matched fraction | `osm_matched_fraction` | Graduated — fraction of detections overlapping a mapped industrial polygon |
| Containment fraction | `osm_containment_fraction` | Measures how fully the event footprint falls within an industrial polygon |
| Proximity fraction | `osm_proximity_fraction` | Captures near-field proximity even without full containment |
| Distance | `min_distance_m` | Proximity score — events within mapped industrial footprint have distance = 0 |

**Contextual and Evidence-Quality Annotation Fields (Not Scored Numerically in Dimension C)**:
- `osm_tier`: Facility mapping verification tier (Tier 1 primary-mapped vs. Tier 2 secondary-mapped). Retained exclusively for contextual reporting and evidence-quality metadata, not numerical risk scoring.
- `osm_primary_category` and `osm_sub_category`: Retained exclusively for contextual reporting and human-readable narrative explanations. Arbitrary numeric category/subcategory risk multipliers are explicitly **removed**.
- Dimension C scoring is driven strictly by objective, observed spatial metrics: matched fraction, containment fraction, proximity fraction, and distance/proximity score.

> [!IMPORTANT]
> **OSM context is evidence of mapped infrastructure — NOT proof of industrial activity.** OSM data represents human-edited map entries; it may be incomplete, outdated, or misclassified. High industrial association score means the event occurred near or within a mapped facility, not that industrial activity caused it. No OSM match is NOT evidence that no facility exists.

### Dimension D: Spatial Scale

| feature | field | rationale |
|---|---|---|
| Spatial extent | `spatial_extent_km2` | Physical footprint area of the clustered detections. |

**Clarification on Spatial Scale Interpretation**:
- Larger spatial extent represents **event scale/extent**; it does **not** automatically mean greater industrial danger.
- A large spatial extent often characterizes dispersed landscape phenomena such as agricultural burning or forest wildfires. In contrast, point-source industrial thermal events (smelters, flaring, kilns) frequently exhibit tight, localized footprints.
- Within general risk scoring, spatial extent measures the physical magnitude/footprint of the observation, while the nature of the hazard depends on convergence with thermal intensity, persistence, and industrial association.

**Excluded from Risk Dimension D**:
- `distinct_satellites`: Removed from physical risk scoring. Multi-platform satellite detection counts (`distinct_satellites`) represent sensor corroboration and observation quality, and are therefore incorporated into **Evidence Confidence**, not physical risk magnitude.

### Contextual Information: Land-Cover Context (WorldCover)

| feature | field | rationale |
|---|---|---|
| Land-cover class | `worldcover_class_name` | Categorical landscape context (e.g., Built-up, Cropland, Tree cover) |

> [!IMPORTANT]
> **WorldCover is CONTEXT ONLY.** WorldCover must not directly increase or decrease the risk score, and all multiplicative risk adjustments from land cover are removed. It appears strictly in explanations and contextual metadata to inform human analysts of baseline terrain (e.g., distinguishing industrial zones from agricultural belts or forest tracts).

### Dimension E: Spectral / Surface Evidence

> [!CAUTION]
> **Sentinel-2 is an optical/NIR/SWIR sensor, NOT a thermal sensor.**
> - Bands B11 and B12 are Short-Wave Infrared (SWIR) surface reflectance bands (centered at ~1610 nm and ~2190 nm), not thermal infrared emissions.
> - `swir2_anomaly_ratio` represents a **surface-reflectance contrast** between the event centre and its local background, **NOT** temperature or a direct thermal anomaly.
> - Spectral indices do **NOT** prove combustion, active fire, gas flaring, or surface temperature. They provide auxiliary optical/surface evidence of surface disturbance, bare ground exposure, or altered surface reflectance properties.

| feature | field | rationale |
|---|---|---|
| SWIR anomaly ratio | `swir2_anomaly_ratio` | Surface-reflectance contrast between event centre and background. Reflectance anomaly indicator (not temperature). |
| NDVI | `ndvi` | Normalized Difference Vegetation Index. Low NDVI indicates lack of dense green vegetation / bare surface. |
| BSI | `bsi` | Bare Soil Index. Elevated BSI aligns with exposed earth, excavation, or barren surface. |
| SWIR2/SWIR1 ratio | `swir2_swir1_ratio` | Spectral reflectance slope between SWIR bands. |

**Excluded from this dimension (correlation de-duplication)**:
- `nbr` (r=0.89–0.93 with ndvi/nbr2 — redundant)
- `nbr2` (r=−0.98 with `swir2_swir1_ratio` — near-perfect duplicate with opposite sign)
- Raw bands `b02`–`b11` (captured by derived indices)
- `b12_swir2_mean`, `b12_swir2_center`, `b12_swir2_bg_mean` (captured by `swir2_anomaly_ratio`)

---

## 5. Correlation Handling Summary

| correlated_group | selected_representative | excluded | basis |
|---|---|---|---|
| Persistence | `distinct_detection_days` | `duration_days` | r=1.00; `distinct_detection_days` more directly interpretable |
| SWIR ratio / NBR2 | `swir2_swir1_ratio` | `nbr2` | r=−0.98; same phenomenon, opposite sign |
| Vegetation/burn | `ndvi` | `nbr`, `nbr2` | ndvi retains independent vegetation meaning; nbr/nbr2 redundant given swir2_swir1_ratio |
| WorldCover | `worldcover_class_name` | `worldcover_class` (integer) | Identical information; string form used for human-readable categorical mapping |
| OSM quality | `scl_clear_fraction` | `scl_cloud_fraction` | Perfect complements (r≈−1.00); one is sufficient |

---

## 6. Normalization Specification

All continuous features must be normalized to [0, 1] before weighted summation. The transformations below use domain-anchored bounds rather than dataset-specific min/max to ensure score stability across deployments and prevent overfitting to the pilot cohort.

> [!NOTE]
> All normalization bounds, thresholds, and ceilings listed in this section are **provisional pilot/expert normalization anchors requiring sensitivity analysis and later empirical calibration** once human-reviewed ground truth becomes available.

### 6.1 Thermal Intensity

**FRP mean** (`frp_mean`):
```
frp_mean_norm = clip(frp_mean, 0, 100) / 100
```
- Domain anchor: 100 MW as upper bound (provisional pilot/expert normalization anchor requiring sensitivity analysis and later empirical calibration). Pilot range: 1.26–57.4 MW.
- Rationale: Domain-anchored ceiling avoids outlier sensitivity from dataset-max normalisation.

**FRP peak** (`frp_max`):
```
frp_max_norm = clip(frp_max, 0, 500) / 500
```
- Domain anchor: 500 MW as upper bound (provisional pilot/expert normalization anchor requiring sensitivity analysis and later empirical calibration). Pilot range: 8.4–381.6 MW.
- Rationale: Winsorised ceiling protects against extreme outlier detections inflating normalisation denominators.

**Brightness temperature** (`brightness_mean`):
```
brightness_norm = clip((brightness_mean - 300), 0, 70) / 70
```
- Domain anchor: 300 K floor and 370 K ceiling (provisional pilot/expert normalization anchors requiring sensitivity analysis and later empirical calibration). Pilot range: 307–367 K.
- Rationale: Kelvin range avoids dataset-specific min/max scaling.

### 6.2 Persistence

**Distinct detection days** (`distinct_detection_days`) — PRIMARY:
```
persistence_norm = log1p(distinct_detection_days) / log1p(365)
```
- Domain anchor: 365 days (provisional pilot/expert normalization anchor requiring sensitivity analysis and later empirical calibration).
- Rationale: Mitigates extreme right skew (pilot: 1–343 days). Logarithmic compression `log1p` preserves near-zero sensitivity while stabilizing long-lived sources.

**Detection count** (`detection_count`) — SECONDARY (sub-signal):
```
detection_count_norm = log1p(detection_count) / log1p(50000)
```
- Domain anchor: 50,000 detections upper bound (provisional pilot/expert normalization anchor requiring sensitivity analysis and later empirical calibration). Pilot range: 1–21,883.
- Rationale: `log1p` stabilizes heavy right tail while capturing observation density.

### 6.3 Industrial / Contextual Association

**OSM match fraction** (`osm_matched_fraction`):
Already in [0, 1] by construction.

**OSM containment fraction** (`osm_containment_fraction`):
Already in [0, 1] by construction.

**OSM proximity fraction** (`osm_proximity_fraction`):
Already in [0, 1] by construction.

**Min distance** (`min_distance_m`):
```
# Convert distance to proximity score (higher = closer, 1.0 = inside polygon)
if min_distance_m is NULL:
    osm_proximity_score = 0.0     # No evidence of proximity (not evidence of safety)
elif min_distance_m <= 0:
    osm_proximity_score = 1.0     # Within mapped industrial polygon
elif min_distance_m >= 5000:
    osm_proximity_score = 0.0     # Beyond 5 km cutoff -- zero contribution
else:
    osm_proximity_score = 1.0 - (min_distance_m / 5000)
```
- Domain anchor: 5,000 m (5 km) outer proximity threshold (provisional pilot/expert normalization anchor requiring sensitivity analysis and later empirical calibration).

*(Note: `osm_tier` is retained strictly as contextual and evidence-quality metadata; it is not scored numerically.)*

### 6.4 Spatial Scale

**Spatial extent** (`spatial_extent_km2`):
```
spatial_norm = log1p(spatial_extent_km2) / log1p(500)
```
- Domain anchor: 500 km2 as upper extent bound (provisional pilot/expert normalization anchor requiring sensitivity analysis and later empirical calibration). Pilot range: 0–88.6 km2.
- Rationale: `log1p` compresses spatial extent. Represents physical footprint scale of the event; larger extent does not automatically signify greater industrial danger.

### 6.5 Spectral / Surface Evidence

**SWIR2 anomaly ratio** (`swir2_anomaly_ratio`):
```
if swir2_anomaly_ratio < 1.0:
    swir_anomaly_norm = 0.0     # No contrast above background
else:
    swir_anomaly_norm = clip((swir2_anomaly_ratio - 1.0), 0, 5) / 5
```
- Domain anchor: Threshold at 1.0 and upper clip at 6.0 (provisional pilot/expert normalization anchors requiring sensitivity analysis and later empirical calibration). Measures optical/SWIR surface-reflectance contrast, not temperature. Pilot range: 0–6.3.

**NDVI** (`ndvi`):
```
ndvi_disturb_norm = clip(1.0 - ndvi, 0, 1)   # Inverted: bare/disturbed surface -> higher score
```
- Domain anchor: Normalized to [0, 1] (provisional pilot/expert normalization anchor requiring sensitivity analysis and later empirical calibration). Pilot range: -0.11 to 0.84.

**BSI** (`bsi`):
```
bsi_norm = clip((bsi + 0.5), 0, 1)
```
- Domain anchor: Offset +0.5 shifts typical [-0.5, 0.5] range to [0, 1] (provisional pilot/expert normalization anchor requiring sensitivity analysis and later empirical calibration). Pilot range: -0.24 to 0.26.

**SWIR2/SWIR1 ratio** (`swir2_swir1_ratio`):
```
swir_ratio_norm = clip(swir2_swir1_ratio, 0, 2) / 2
```
- Domain anchor: Upper clip at 2.0 (provisional pilot/expert normalization anchor requiring sensitivity analysis and later empirical calibration). Pilot range: 0–2.02.

---

## 7. Risk Dimension and Sub-Feature Weights

> [!WARNING]
> All weights in this section are **provisional pilot/expert anchors requiring sensitivity analysis and later empirical calibration**. They have NOT been fitted to surrogate targets or validated against human ground truth.

### 7.1 Dimension Weights

The five risk dimensions sum to exactly 1.00 (100%):

| Dimension | Label | Risk Weight | Rationale |
|---|---|---|---|
| A | Thermal Intensity | **0.30 (30%)** | Direct physical measurement of emitted thermal radiation from FIRMS sensors; fundamental measure of thermal power magnitude. |
| B | Persistence | **0.25 (25%)** | Temporal recurrence and longevity; essential discriminator between ephemeral transient burning and persistent stationary heat sources. |
| C | Industrial / Contextual Association | **0.20 (20%)** | Observed spatial metrics (match, containment, proximity, distance) to mapped industrial polygons; objective infrastructure co-location. |
| D | Spatial Scale | **0.10 (10%)** | Footprint scale/geographic extent of clustered detections. Larger extent reflects physical event scale; does not automatically indicate higher industrial danger. |
| E | Spectral / Surface Evidence | **0.15 (15%)** | Optical/SWIR surface reflectance contrast and ground disturbance signals from Sentinel-2 MSI; auxiliary surface evidence (not temperature). |
| — | **Total** | **1.00 (100%)** | **Fully additive multi-dimensional risk framework** |

**Context Only (0% Risk Weight)**:
- **WorldCover**: 0% risk weight. No multiplicative or additive scaling on the risk score. Appears solely in contextual explanations.
- **`distinct_satellites`**: 0% risk weight. Relocated to Evidence Confidence as a platform corroboration metric.

### 7.2 Within-Dimension Sub-Feature Weights

#### Dimension A — Thermal Intensity (Weight = 0.30; internal sum = 1.00)

| sub-feature | internal_weight | rationale | limitation |
|---|---|---|---|
| `frp_mean` | 0.50 | Sustained radiated thermal power level | Does not capture temporal modulation |
| `frp_max` | 0.35 | Peak observed thermal episode | Single observation; sensitive to sensor scan angle |
| `brightness_mean` | 0.15 | Mid-infrared sensor brightness temperature | Narrower dynamic range in pilot (307–367 K) |

#### Dimension B — Persistence (Weight = 0.25; internal sum = 1.00)

| sub-feature | internal_weight | rationale | limitation |
|---|---|---|---|
| `distinct_detection_days` | 0.70 | Calendar days with active satellite detections | Revisit cadence dependent |
| `detection_count` | 0.30 | Detection density/volume within active days | Correlated with detection days (r=0.70); lower weight mitigates double counting |

#### Dimension C — Industrial / Contextual Association (Weight = 0.20; internal sum = 1.00)

All arbitrary category/subcategory multipliers and `osm_tier_score` are removed from numerical scoring. Scoring relies solely on objective, observed spatial metrics:

| sub-feature | internal_weight | rationale | limitation |
|---|---|---|---|
| `osm_matched_fraction` | 0.35 | Fraction of cluster detections intersecting industrial polygon | Incomplete OSM polygon coverage |
| `osm_containment_fraction` | 0.30 | Full polygon containment of event cluster | Sensitive to polygon boundary fidelity |
| `osm_proximity_fraction` | 0.20 | Near-field proximity fraction | Overlaps with containment |
| `osm_proximity_score` | 0.15 | Continuous inverse distance score (1.0 at 0m, 0.0 at >=5000m) | Applies only when nearest facility identified |

**Dimension C Score Computation**:
```
osm_dimension_score = (0.35 * osm_matched_fraction
                     + 0.30 * osm_containment_fraction
                     + 0.20 * osm_proximity_fraction
                     + 0.15 * osm_proximity_score)
```
- If no OSM match exists (all fields NULL), `osm_dimension_score = 0.0`. This represents absence of mapped industrial evidence, not confirmed absence of industry (no OSM match is NOT evidence that no facility exists).
- `osm_tier` is retained strictly as contextual/evidence-quality metadata. `osm_primary_category` and `osm_sub_category` are retained solely for human-readable narrative explanations.

#### Dimension D — Spatial Scale (Weight = 0.10; internal sum = 1.00)

| sub-feature | internal_weight | rationale | limitation |
|---|---|---|---|
| `spatial_norm` (`spatial_extent_km2`) | 1.00 | Quantifies physical footprint/extent of the cluster | Extent reflects event scale; large scale does not automatically imply industrial danger |

#### Dimension E — Spectral / Surface Evidence (Weight = 0.15; internal sum = 1.00)

| sub-feature | internal_weight | rationale | limitation |
|---|---|---|---|
| `swir_anomaly_norm` | 0.45 | Centre-to-background surface-reflectance contrast (B12 SWIR) | Surface reflectance only; NOT a temperature measurement |
| `ndvi_disturb_norm` | 0.25 | Surface disturbance / lack of dense vegetation canopy | Influenced by seasonal phenology |
| `swir_ratio_norm` | 0.20 | Spectral shape ratio (B12/B11) | Spectral reflectance property, not fire proof |
| `bsi_norm` | 0.10 | Bare soil / bare earth index | Narrow dynamic range in pilot |

---

## 8. Missing Data — Explicit Behaviour

> [!IMPORTANT]
> **Fixed Risk Weights and Missing Data Interpretation**:
> - **Fixed Weights with No Redistribution**: Risk weights are fixed (30%, 25%, 20%, 10%, 15%) and sum to 100%. Under no circumstances are weights redistributed or renormalized when a data source or dimension is unavailable.
> - **Observed Evidence on a Fixed Scale**: Missing evidence can lower the numerical Risk Score because the score represents evidence actually observed on a fixed 0–100 scale. Unavailable dimensions contribute no observed evidence to the fixed-scale score.
> - **A lower score caused by missing evidence must NOT be interpreted as lower real-world danger.**
> - **Evidence Confidence must always be consulted alongside the Risk Score.**
> - **LOW Risk + LOW Evidence Confidence means insufficient evidence to assess, NOT verified safety or low hazard.**
> - The absence of observed evidence in an unobserved dimension does not represent a meaningful physical hazard ceiling; it reflects an observational data gap.

### 8.1 No OSM Match (OSM fields null for 60% of pilot events)

- `osm_dimension_score = 0.0` — the Industrial / Contextual Association dimension contributes no observed evidence (0.0 toward its 20% weight).
- **Weights are NOT redistributed.** Surviving dimensions operate strictly at their fixed weights.
- **Distinction between "No Mapped Association" and "Data Unavailable"**:
  * An absent OSM match represents **no mapped industrial association** in the OpenStreetMap database at that coordinate.
  * This must **not** be conflated with **OSM data unavailable/incomplete** (if the spatial query executed successfully against the vector database, query execution is complete; the query simply returned no intersecting polygon).
  * Consequently, an absent OSM match does **not** automatically indicate poor overall evidence quality for the query pipeline.
  * Crucially: **No OSM match is NOT evidence that no facility exists.** Due to documented OSM coverage gaps in India (60% null in pilot), industrial facilities may be unmapped.
- Explanation audit trail records: `osm_context: NO_MAPPED_ASSOCIATION`.

### 8.2 No Sentinel-2 Scene Found (4% of pilot events — `has_satellite_scene = 0`)

- Dimension E score = 0.0.
- **No weight redistribution occurs.** Unavailable dimensions contribute no observed evidence to the fixed-scale score (Dimension E contributes 0.0 toward the 15% allocated to spectral evidence).
- Missing optical/SWIR data directly lowers the Evidence Confidence score:
  `spectral_coverage: NO_SCENE`

### 8.3 Missing Spectral Features (extraction error — 10% of pilot events, `has_spectral_features = 0`)

- Same behaviour as 8.2: Dimension E = 0.0, no weight redistribution; contributes no observed evidence.
- Evidence confidence indicator records: `spectral_coverage: EXTRACTION_FAILED`

### 8.4 High Cloud Cover (`satellite_cloud_cover_scene > 0.5` or `scl_clear_fraction < 0.5`)

- Dimension E raw score is multiplied by `spectral_reliability` (see Section 9.1).
- Unreliable spectral evidence reduces observed contribution without inflating other dimensions.
- Evidence confidence indicator records: `spectral_quality: DEGRADED_CLOUD`

### 8.5 Large Temporal Delta (`temporal_delta_days > 90`)

- Dimension E raw score is multiplied by `temporal_reliability` (see Section 9.1).
- Stale surface imagery cannot corroborate current thermal activity.
- Evidence confidence indicator records: `temporal_relevance: STALE (delta=N days)`

### 8.6 Missing Individual Spectral Indices (11% null NDVI, BSI)

- Any uncomputed index contributes 0 to the Dimension E sub-score.
- Internal weights are not arbitrarily inflated; missing indices lower the dimension sub-score and record: `spectral_completeness: PARTIAL`.

### 8.7 General Principle: Zero Redistribution and Fixed Scale

For any missing feature or dimension:
1. Unavailable dimensions contribute no observed evidence to the fixed-scale score (contributing 0.0).
2. Under no circumstance is the missing weight reallocated or renormalized across other dimensions.
3. Missing observations reduce the **Evidence Confidence** score and are explicitly itemized in the explanation audit trail.
4. Analysts must always evaluate Risk Score alongside Evidence Confidence: LOW Risk + LOW Evidence Confidence indicates an evidence gap, never confirmed safety.

---

## 9. Reliability Adjustment and Evidence Confidence

### 9.1 Spectral Reliability Score

Because Sentinel-2 provides optical/SWIR surface reflectance observations rather than concurrent thermal radiometry, its contribution to Dimension E is adjusted by image quality and acquisition timeliness:

```
# Temporal reliability: decays linearly from 1.0 (0 days) to 0.0 (90+ days)
if temporal_delta_days is NULL:
    temporal_reliability = 0.5    # Unknown delta -- moderate penalty
elif temporal_delta_days <= 0:
    temporal_reliability = 1.0
elif temporal_delta_days >= 90:
    temporal_reliability = 0.0
else:
    temporal_reliability = 1.0 - (temporal_delta_days / 90)

# Cloud/quality reliability: based on scene classification clear pixel fraction
if has_spectral_features == 0:
    cloud_reliability = 0.0
elif scl_clear_fraction >= 0.9:
    cloud_reliability = 1.0
elif scl_clear_fraction >= 0.5:
    cloud_reliability = scl_clear_fraction    # Proportional degradation
else:
    cloud_reliability = 0.0    # Overcast / cloud-obscured -- zero reliable surface signal

# Combined spectral reliability
spectral_reliability = temporal_reliability * cloud_reliability

# Adjusted Dimension E score
dimension_E_score = dimension_E_raw * spectral_reliability
```

### 9.2 Evidence Confidence Indicator

Evidence Confidence is strictly separated from the Risk Score. It quantifies the completeness, corroboration, and reliability of the data sources across the observation pipeline (0–100).

> [!IMPORTANT]
> **Confidence is NOT class probability.** It does not express the likelihood of fire, industrial operation, or any classification category. It measures observational data completeness and quality.

Key Evidence Quality & Corroboration Principles:
- **Satellite Corroboration**: Multi-platform satellite observation count (`distinct_satellites`) measures sensor corroboration:
  ```
  satellite_corroboration = clip(distinct_satellites, 1, 5) / 5.0
  ```
- **OSM Evidence Quality vs. Association**: An absent OSM match represents no mapped industrial association; it does **not** mean OSM data was unavailable or that overall evidence quality is poor. If the OSM spatial query executed successfully against the database, the query pipeline is complete. OSM tier (`osm_tier`) is retained as evidence-quality metadata (Tier 1 primary vs. Tier 2 secondary) when a match exists.
- **Spectral Completeness & Quality**: Measures clear-sky coverage and temporal proximity (`has_spectral_features * spectral_reliability`).

The overall Evidence Confidence (0–100) is aggregated across data components:

| Component | Measurement / Metric | Weight |
|---|---|---|
| FIRMS Multi-Sensor Corroboration | `satellite_corroboration` (platform diversity 1–5) | 0.30 |
| FIRMS Observation Completeness | Active detection presence (1.0 for detected events) | 0.20 |
| Spatial Query / Layer Completeness | OSM spatial query executed and layer available (1.0 if query completed; 0.0 if database unavailable) | 0.20 |
| Spectral Completeness & Quality | `has_spectral_features` * `spectral_reliability` | 0.30 |

```
evidence_confidence_raw = (0.30 * satellite_corroboration
                         + 0.20 * 1.0                             # FIRMS detections verified
                         + 0.20 * (1.0 if osm_query_complete else 0.0)
                         + 0.30 * (has_spectral_features * spectral_reliability))

evidence_confidence = round(evidence_confidence_raw * 100, 1)
```

Evidence confidence categories:
- **HIGH**: >= 75
- **MEDIUM**: 50–74
- **LOW**: < 50

---

## 10. Risk Score Aggregation

### 10.1 Additive Score Computation

The risk score is a direct, linear weighted combination of the five evidence dimensions. There are no multiplicative modifiers from land-cover or categorical tables.

```
# Step 1: Compute normalized dimension scores [0, 1]
score_A = 0.50 * frp_mean_norm + 0.35 * frp_max_norm + 0.15 * brightness_norm
score_B = 0.70 * persistence_norm + 0.30 * detection_count_norm
score_C = osm_dimension_score   # (from Section 7.2; observed spatial metrics only)
score_D = spatial_norm          # (from Section 6.4; spatial_extent_km2)
score_E = (0.45 * swir_anomaly_norm
         + 0.25 * ndvi_disturb_norm
         + 0.20 * swir_ratio_norm
         + 0.10 * bsi_norm) * spectral_reliability  # (adjusted by reliability)

# Step 2: Weighted linear aggregation (weights sum to 1.00)
risk_raw = (0.30 * score_A
          + 0.25 * score_B
          + 0.20 * score_C
          + 0.10 * score_D
          + 0.15 * score_E)

# Step 3: Scale to 0-100
risk_score = round(risk_raw * 100, 1)
```

### 10.2 Risk Tiers (Provisional Pilot Thresholds)

> [!WARNING]
> The following risk tier thresholds are **provisional pilot/expert anchors requiring sensitivity analysis and later empirical calibration**. They have NOT been calibrated on human ground-truth labels.

| Tier | Score Range | Label | Meaning |
|---|---|---|---|
| 1 | 0 – 24 | **LOW** | Available evidence does not indicate significant thermal or contextual concern. Does not confirm the event is benign. |
| 2 | 25 – 49 | **MODERATE** | Moderate physical evidence of thermal activity or partial industrial proximity. Warrants automated tracking. |
| 3 | 50 – 74 | **HIGH** | Significant convergent physical evidence across intensity, persistence, spatial scale, and/or industrial association. Prioritised for analyst review. |
| 4 | 75 – 100 | **CRITICAL** | Highly persistent, intense thermal emissions with close industrial association and surface disturbance signals. Urgent inspection priority. |

---

## 11. Explanation Structure

Every scored event should produce a structured explanation record (deterministic, not LLM-generated). The structure is:

```
event_id            : <event_id>
risk_score          : <0-100> (weighted physical & contextual evidence strength)
risk_tier           : LOW | MODERATE | HIGH | CRITICAL
evidence_confidence : <0-100> (HIGH | MEDIUM | LOW; completeness & corroboration)

--- RISK DIMENSION SCORES (Sum of weights = 100%) ---
A. Thermal Intensity (30%)                : <score> / 100  [frp_mean=X MW, frp_max=Y MW, brightness=Z K]
B. Persistence (25%)                      : <score> / 100  [N distinct days, M total detections]
C. Industrial / Contextual Assoc. (20%)   : <score> / 100  [match=X%, containment=Y%, prox_dist=Z m]
D. Spatial Scale (10%)                    : <score> / 100  [extent=X km2 (footprint scale, not danger level)]
E. Spectral / Surface Evidence (15%)      : <score> / 100  [swir_anomaly=X, ndvi=Y, bsi=Z (surface contrast only)]
   Spectral reliability factor            : <factor>       [temporal_delta=N days, clear_fraction=X]

--- CONTEXTUAL ANNOTATIONS (Context Only — 0% Risk Weight) ---
- Land-Cover Context (WorldCover)         : <worldcover_class_name> (baseline landscape; no risk multiplier)
- OSM Category & Tier Details            : <osm_primary_category> / <osm_sub_category> / tier=<osm_tier> (context & evidence quality only)

--- EVIDENCE CONFIDENCE & CORROBORATION ---
- Satellite Platform Corroboration        : <distinct_satellites> platforms observing event
- Vector & Scene Data Completeness        : [OSM present/absent, S2 scene present/absent]
- Overall Evidence Confidence             : <score> / 100 (<category>)

--- MAIN SUPPORTING EVIDENCE ---
1. [Top scoring dimension and its observed physical metric values]
2. [Second strongest dimension]
3. [Third strongest dimension, if score > 0.5]

--- COUNTER-EVIDENCE & DATA DEGRADATIONS ---
- [Any dimension scoring < 0.3 that indicates lack of physical signal]
- [Any data quality issue reducing evidence reliability (clouds, stale acquisition)]

--- EVIDENCE GAPS ---
- [List of missing data: no OSM match / no Sentinel-2 scene / high temporal delta / etc.]

--- SCIENTIFIC CAVEATS ---
- Risk score reflects observed physical/contextual evidence strength; NOT ground-truth validated.
- Evidence Confidence is observational quality/corroboration; NOT class probability.
- Sentinel-2 SWIR bands (B11/B12) measure surface reflectance contrast; NOT temperature or active combustion.
- OSM proximity indicates mapped infrastructure co-location; NOT proof of industrial causation.
- Larger spatial scale indicates geographic extent; does NOT automatically mean higher industrial hazard.
```

---

## 12. Example Calculation — Hypothetical Event ONLY

> [!CAUTION]
> The following example uses **entirely hypothetical values**. It does NOT correspond to any real event in the pilot dataset. It does NOT use any real event_id. It is provided solely to illustrate the corrected methodology.

**Hypothetical Event**: `EVT_HYPOTHETICAL_EXAMPLE` (NOT REAL)

```
Hypothetical input values:
  frp_mean = 18.0 MW        frp_max = 45.0 MW     brightness_mean = 340 K
  distinct_detection_days = 210     detection_count = 5,000
  spatial_extent_km2 = 12.0        distinct_satellites = 3
  has_osm_industrial_match = 1     osm_matched_fraction = 0.85
  osm_containment_fraction = 0.70  osm_proximity_fraction = 0.90
  min_distance_m = 0               osm_tier = 2 (Context / Evidence Quality Only)
  osm_primary_category = mine_quarry (Context Only)
  worldcover_class_name = Bare / sparse vegetation (Context Only)
  swir2_anomaly_ratio = 2.8        ndvi = 0.12
  bsi = 0.15                       swir2_swir1_ratio = 1.3
  has_spectral_features = 1        scl_clear_fraction = 0.88
  temporal_delta_days = 25
```

**Step 1: Normalize features** (provisional pilot/expert normalization anchors requiring sensitivity analysis and later empirical calibration)
```
frp_mean_norm       = clip(18.0, 0, 100) / 100 = 0.180
frp_max_norm        = clip(45.0, 0, 500) / 500 = 0.090
brightness_norm     = clip((340 - 300), 0, 70) / 70 = 40 / 70 = 0.571
persistence_norm    = log1p(210) / log1p(365) = 5.352 / 5.900 = 0.907
detection_norm      = log1p(5000) / log1p(50000) = 8.517 / 10.820 = 0.787
osm_proximity_score = 1.000 (distance = 0)
spatial_norm        = log1p(12.0) / log1p(500) = 2.565 / 6.216 = 0.413
swir_anomaly_norm   = clip((2.8 - 1.0), 0, 5) / 5 = 1.8 / 5 = 0.360 (surface contrast)
ndvi_disturb_norm   = clip(1.0 - 0.12, 0, 1) = 0.880
bsi_norm            = clip((0.15 + 0.5), 0, 1) = 0.650
swir_ratio_norm     = clip(1.3, 0, 2) / 2 = 0.650
```

**Step 2: Dimension scores**
```
# A. Thermal Intensity (internal weights: 0.50, 0.35, 0.15)
score_A = 0.50 * 0.180 + 0.35 * 0.090 + 0.15 * 0.571 = 0.0900 + 0.0315 + 0.0857 = 0.207

# B. Persistence (internal weights: 0.70, 0.30)
score_B = 0.70 * 0.907 + 0.30 * 0.787 = 0.6349 + 0.2361 = 0.871

# C. Industrial / Contextual Association (objective spatial metrics only; NO tier or category multipliers)
score_C = (0.35 * 0.85 + 0.30 * 0.70 + 0.20 * 0.90 + 0.15 * 1.00)
        = 0.2975 + 0.2100 + 0.1800 + 0.1500 = 0.8375

# D. Spatial Scale (spatial_extent_km2 footprint scale; NO distinct_satellites)
score_D = spatial_norm = 0.413

# E. Spectral / Surface Evidence (Sentinel-2 optical/SWIR surface reflectance contrast)
spectral_reliability = (1.0 - 25/90) * 0.88 = 0.722 * 0.88 = 0.635
E_raw = 0.45 * 0.360 + 0.25 * 0.880 + 0.20 * 0.650 + 0.10 * 0.650
      = 0.162 + 0.220 + 0.130 + 0.065 = 0.577
score_E = 0.577 * 0.635 = 0.366
```

**Step 3: Weighted linear risk score aggregation** (weights: 30%, 25%, 20%, 10%, 15%; NO landcover multiplier)
```
risk_raw = (0.30 * score_A
          + 0.25 * score_B
          + 0.20 * score_C
          + 0.10 * score_D
          + 0.15 * score_E)
         = (0.30 * 0.207 + 0.25 * 0.871 + 0.20 * 0.8375 + 0.10 * 0.413 + 0.15 * 0.366)
         = 0.0621 + 0.21775 + 0.1675 + 0.0413 + 0.0549
         = 0.54355

risk_score = round(0.54355 * 100, 1) = 54.4 --> Risk Tier: HIGH (Provisional Pilot Threshold)
```

**Step 4: Evidence Confidence computation** (includes multi-platform satellite corroboration; NOT class probability)
```
satellite_corroboration = clip(3, 1, 5) / 5.0 = 0.60
evidence_confidence_raw = (0.30 * 0.60                          # distinct_satellites corroboration
                         + 0.20 * 1.00                          # FIRMS active detection
                         + 0.20 * 1.00                          # OSM query complete
                         + 0.30 * (1.00 * 0.635))               # Spectral features * reliability
                        = 0.180 + 0.200 + 0.200 + 0.1905 = 0.7705

evidence_confidence = round(0.7705 * 100, 1) = 77.1 --> HIGH (>= 75)
```

**Result Summary**:
```
Risk Score           : 54.4 / 100
Risk Tier            : HIGH (PROVISIONAL PILOT THRESHOLD)
Evidence Confidence  : 77.1 / 100 (HIGH)

Main evidence:
1. High Persistence: 210 distinct detection days over annual baseline
2. Strong Industrial Spatial Association: 85% match, 70% containment within mapped polygon
3. Moderate Spatial Footprint: 12 km2 cluster extent

Counter-evidence / Limitations:
- Thermal intensity moderate (FRP mean 18 MW, well below 100 MW anchor)
- Temporal delta of 25 days attenuates spectral evidence reliability to 63.5%

Contextual Observations:
- WorldCover class 'Bare / sparse vegetation' provides land context (0% score weighting)
- OSM facility category 'mine_quarry' and mapping tier '2' provide descriptive and evidence-quality context (no score multiplier)
```

---

## 13. Scientific Limitations and Machine Learning Guardrails

1. **ML / Surrogate Target Guardrails**:
   - `sampling_stratum` is **NOT** ground truth. It is an automated geographic/temporal clustering heuristic used purely for candidate sampling.
   - Current baseline ML models (Phase VIII) used `sampling_stratum` strictly as a **surrogate target**, not as human expert verification.
   - Current ML predictions and class probabilities are **NOT** validated classification evidence.
   - Current ML outputs must **NOT** be primary risk inputs.
   - Human-reviewed ground truth is strictly required before any validated supervised classification or model-driven scoring can occur.
   - Ground-truth fields (`label`, `label_confidence`, `label_reason`, `review_status`, `reviewed_at`, `sampling_stratum`) must **never enter operational risk scoring** to prevent target leakage.
2. **Provisional Anchors and Pilot Dataset**: All normalization bounds and dimension weights are **provisional pilot/expert normalization anchors requiring sensitivity analysis and later empirical calibration**. They were formulated from domain reasoning on a 100-event pilot cohort from India and have not been fitted to empirical outcomes.
3. **Spatial Scale Interpretation**: Larger spatial extent represents physical event scale/extent; it does **not** automatically mean greater industrial danger. Expansive footprints often reflect broad landscape burning rather than localized industrial hazards.
4. **Sentinel-2 is Optical/SWIR (Not Thermal)**: Sentinel-2 B11/B12 measure surface reflectance contrast, not emitted heat or temperature. `swir2_anomaly_ratio` detects surface-reflectance contrast, which does not prove combustion, active fire, gas flaring, or surface temperature.
5. **OSM Vector Incompleteness & Absence**: OSM coverage in India is incomplete (60% null in pilot). An absent OSM match represents no mapped industrial association; it is **NOT** evidence that no facility exists. Furthermore, absence of mapped industrial infrastructure must not be conflated with database query failure or poor overall evidence quality.
6. **WorldCover Role**: WorldCover provides baseline land-cover context only. It has zero weight in the risk score and applies no multiplicative factor.
7. **Feature Correlations**: Known correlations (e.g., `distinct_detection_days` and `detection_count` at r=0.70) are mitigated by unequal internal sub-weights, but residual correlation remains. Dimensions must be interpreted as convergent indicators rather than fully orthogonal statistical factors.
8. **Absence of Population Exposure**: Current scoring reflects physical/contextual event characteristics only; it does not measure societal severity or population exposure.

---

## 14. Future Improvements

| improvement | evidence_gap_addressed | priority |
|---|---|---|
| Human ground-truth labeling (Phase VI completion) | Enables calibration and empirical validation of risk tier thresholds | CRITICAL |
| Empirical calibration of provisional anchors | Replaces provisional pilot anchors with empirically calibrated thresholds | CRITICAL |
| FRP standard deviation | Distinguishes pulsed (fire) from stable (industrial) thermal sources | HIGH |
| FRP temporal trend | Growing/declining/stable patterns discriminate event types | HIGH |
| FIRMS per-detection confidence aggregation | Weights detections by their individual sensor confidence | HIGH |
| OSM facility density (buffer counts) | Contextualises single-nearest-facility with surrounding industrial density | MEDIUM |
| Nighttime light (VIIRS-DNB) integration | Strong discriminator between inhabited/industrial and remote fire events | MEDIUM |
| Population density / exposure layer | Adds severity dimension to risk (high-risk event near city vs. remote) | MEDIUM |
| Ground-truth-trained ML classifier | Replace surrogate-trained model with human-labeled model probabilities as risk input | HIGH (after labeling) |
| Sensitivity analysis on weights | Quantify how risk scores change under weight perturbation | MEDIUM |
| Terrain / elevation integration | Disfavours fixed industrial priors on steep terrain | LOW |
| SHAP per-event attribution | Replace global Gini importance with per-event feature attribution in explanations | LOW |

---

## 15. Do Not Claim (Scientific and Operational Guardrails)

> [!CAUTION]
> The following statements must NEVER be made about ThermoGuard risk scores or any output from this pipeline:

1. **Do NOT claim** that a risk score proves an industrial facility is operating illegally or non-compliantly.
2. **Do NOT claim** that a risk score proves an active fire, combustion, or gas flare occurred at a specific location.
3. **Do NOT claim** that a HIGH or CRITICAL risk score constitutes an emergency alert or replaces official emergency response systems.
4. **Do NOT claim** that Sentinel-2 SWIR spectral indices are temperature measurements, thermal infrared data, or proof of active combustion.
5. **Do NOT claim** that `swir2_anomaly_ratio` directly measures thermal emissions (it measures optical surface reflectance contrast).
6. **Do NOT claim** that OSM proximity proves industrial activity caused the thermal event.
7. **Do NOT claim** that an absent OSM match is evidence that no facility exists (incompleteness gap).
8. **Do NOT claim** that WorldCover land-cover class determines the event type or directly adjusts the risk score.
9. **Do NOT claim** that current ML model predictions are validated classification evidence (baseline models were trained on surrogate `sampling_stratum`, not expert ground truth).
10. **Do NOT use** current ML outputs as primary risk inputs.
11. **Do NOT claim** that `sampling_stratum` is ground truth.
12. **Do NOT allow** `sampling_stratum`, `label`, `label_confidence`, `label_reason`, `review_status`, or `reviewed_at` to enter operational risk scoring.
13. **Do NOT claim** that larger spatial extent automatically means greater industrial danger.
14. **Do NOT interpret** a lower numerical score caused by missing evidence as lower real-world danger.
15. **Do NOT treat** a LOW Risk + LOW Evidence Confidence result as confirmed safety (it indicates insufficient evidence).
16. **Do NOT claim** that provisional pilot weights and normalization anchors are optimal or empirically calibrated.
17. **Do NOT treat** Evidence Confidence as class probability.
18. **Do NOT redistribute or renormalize weights** when data sources are missing.

---

```
PHASE IX METHODOLOGY STATUS: READY WITH LIMITATIONS
```

**Evidence for READY**:
- Risk dimensions systematically structured with explicit weights: Thermal Intensity (30%), Persistence (25%), Industrial / Contextual Association (20%), Spatial Scale (10%), Spectral / Surface Evidence (15%).
- WorldCover correctly designated as Context Only (0% score weight, no multiplicative factor).
- `distinct_satellites` relocated to Evidence Confidence as sensor corroboration.
- OSM category/subcategory multipliers removed in favor of objective spatial metrics.
- Sentinel-2 SWIR precisely defined as optical/SWIR surface reflectance contrast (not thermal/temperature).
- Weight redistribution removed; missing data strictly reduces Evidence Confidence / available evidence.
- Risk Score (physical/contextual evidence strength) and Evidence Confidence (completeness/corroboration) strictly separated.
- ML and ground-truth guardrails explicitly documented (`sampling_stratum` is surrogate only; no leakage fields).
- Normalization anchors explicitly labeled as provisional pilot/expert anchors.
- Spatial scale clearly contextualized (extent scale != industrial danger).

**Evidence for LIMITATIONS**:
1. No human ground-truth labels yet available to empirically validate tier thresholds or calibrate provisional anchors.
2. OSM vector coverage has geographic gaps (60% null in pilot).
3. Sentinel-2 scenes have temporal deltas and cloud contamination requiring reliability discounting.
4. Absence of population exposure and air quality dispersion modeling.
5. Provisional weights require empirical sensitivity analysis prior to operational deployment.

---

*This document is a design specification only. No datasets were modified. No models were trained. No real event scores were computed. No external APIs were called.*
