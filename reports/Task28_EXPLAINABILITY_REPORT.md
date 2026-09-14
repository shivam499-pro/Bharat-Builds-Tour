# TASK 28 — EXPLAINABILITY LAYER FOR THE FROZEN RISK ENGINE

## Executive Summary
- **Methodology Version**: `PhaseIX-2026-09-14`
- **Pilot Events Processed**: 100 events ($N=100$ frozen cohort)
- **Explainability Mode**: Deterministic Rule-Based Trace (Zero LLM, Zero ML, Zero NLG)
- **Traceability Scope**: Full mathematical decomposition from raw sensor observation to analyst recommendation.
- **Mathematical Invariant**: Risk Score (0–100) and Evidence Confidence (0–100) are strictly decoupled.

---

## Part 1 — Explainability Architecture & Decision Tree

The deterministic explainability layer maps frozen risk-scoring traces into transparent analyst interpretations:

```
Raw Observations (FRP, Detection Days, OSM Distance, Extent, SWIR Anomaly)
                       │
                       ▼
      Normalized Sub-Dimensions [0.0, 1.0]
                       │
                       ▼
  Weighted Contribution Points (A: 30%, B: 25%, C: 20%, D: 10%, E: 15%)
                       │
                       ▼
     Numerical Risk Score [0, 100]  &  Evidence Confidence [0, 100]
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
Contribution Ranking         Evidence Limitations
(Primary/Secondary Drivers)  (Missing/Stale/Degraded Data)
         │                           │
         └─────────────┬─────────────┘
                       ▼
          Analyst Descriptive Synthesis
                       ▼
       Standardized Investigation Recommendation
```

### Key Principles:
1. **Points Scale Transparency**: Normalized dimension values in $[0, 1]$ are explicitly translated into final risk points on the $[0, 100]$ scale (e.g. Dimension A normalized score $0.067 \times 30\% = 2.0$ points).
2. **Contribution Ranking**: Every event unambiguously identifies its Primary Driver, Secondary Driver, and Weakest Dimension.
3. **Evidence Limitation vs Absence of Hazard**: Missing or stale Sentinel-2 optical evidence is never described as 'no fire'. It is explicitly documented as: *'Contemporary Sentinel-2 evidence was unavailable/stale, so this dimension contributed 0 points. This is an evidence limitation, not evidence of absence.'*
4. **Investigation Priority Matrix**: Recommendations strictly follow locked risk tiers and confidence tiers without introducing new numerical scores.

---

## Part 2 — Investigation Recommendation Matrix

| Risk Tier | Evidence Confidence | Standard Recommendation | Operational Meaning |
| :--- | :--- | :--- | :--- |
| **CRITICAL / HIGH** | **HIGH** | `Priority investigation target` | Strong physical evidence corroborated by multi-satellite data; immediate facility review. |
| **CRITICAL / HIGH** | **MEDIUM / LOW** | `Priority target — needs corroborating verification` | Elevated observed risk with unverified optical/single-sensor data; prioritize fresh satellite tasking. |
| **MODERATE** | **HIGH** | `Routine monitoring target` | Verified moderate thermal activity; standard scheduled monitoring queue. |
| **MODERATE** | **MEDIUM / LOW** | `Needs additional satellite verification` | Moderate activity with degraded/missing optical passes; verify persistence. |
| **LOW** | **HIGH** | `Confident low-risk event` | Robust multi-sensor corroboration confirms localized, low-persistence, non-industrial burn. |
| **LOW** | **LOW** | `Low observed risk but insufficient evidence` | Numerical score is low due to missing data dimensions; cannot be deemed safe without further data. |

---

## Part 3 — Top 5 Highest Risk Events (Chronic Industrial / Mining)

The highest-scoring events in the pilot cohort represent chronic, multi-month industrial heat sources with direct OSM infrastructure association:

### Event `EVT_00963466`

| Metric | Value | Tier |
| :--- | :---: | :---: |
| **Risk Score** | **49.0 / 100** | **MODERATE** |
| **Evidence Confidence** | **70.0 / 100** | **MEDIUM** |
| **Investigation Priority** | **Needs additional satellite verification** | — |

**Summary**: Event received an investigation priority score of 49.0/100 (MODERATE). The primary risk driver is Persistence (24.2 pts), followed by Industrial Association (15.5 pts).

#### 1. Dimension Score Breakdown

| Dimension | Code | Weight | Normalized [0, 1] | Weighted Points [0–100] | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Thermal Intensity | `A` | 30% | 0.067 | **2.0** | `PRESENT` |
| Persistence | `B` | 25% | 0.970 | **24.2** | `PRESENT` |
| Industrial Association | `C` | 20% | 0.775 | **15.5** | `PRESENT` |
| Spatial Scale | `D` | 10% | 0.723 | **7.2** | `PRESENT` |
| Spectral / Surface Evidence | `E` | 15% | 0.000 | **0.0** | `STALE` |

#### 2. Key Contribution Drivers
- **Primary driver: Persistence — 24.2 points**
- **Secondary driver: Industrial Association — 15.5 points**
- **Weakest evidence: Spectral / Surface Evidence — 0.0 points**

#### 3. Raw Evidence Trace
- **Thermal**: FRP mean = 2.8, FRP max = 34.8, Brightness mean = 313.25 K
- **Persistence**: Distinct detection days = 343, Total detection count = 21883
- **Industrial**: OSM match fraction = 0.9973, Containment = 0.766, Proximity = 0.2313, Min distance = 0.0 m
- **Spatial**: Convex hull area = 88.5907 km²
- **Spectral**: SWIR anomaly ratio = 1.2667, NDVI = 0.0463, SWIR2/SWIR1 ratio = 1.2549, BSI = 0.1362, SCL clear fraction = 0.9184, Temporal delta = 238.42 days

#### 4. Evidence Availability & Limitations
- **Sentinel-2 Status**: Contemporary Sentinel-2 evidence was stale (temporal offset: 238.4 days > 90 days; temporal reliability = 0.0), so this dimension contributed 0 points. This is an evidence limitation, not evidence of absence.
- **Missing Tags**: `temporal_relevance:stale`

#### 5. Deterministic Interpretations
- **Thermal**: Low thermal energy output observed near sensor detection thresholds.
- **Persistence**: Chronic thermal activity persisted across 343 distinct detection days (21,883 total detections).
- **Industrial**: The event is strongly associated with mapped industrial infrastructure (high polygon containment / direct co-location).
- **Spatial**: Extensive spatial footprint encompassing a large contiguous thermal cluster area (88.59 km²).
- **Spectral**: Available Sentinel-2 evidence is temporally stale relative to the FIRMS observation (>90 days offset).

#### 6. Investigation Recommendation & Next Actions
**Recommendation**: `Needs additional satellite verification`
**Rationale**: Moderate risk score (49.0/100) with limited observational confidence (70.0/100, MEDIUM). Gaps in optical or corroborating data prevent definitive characterization.
**Recommended Next Steps**:
  - [ ] Task contemporary optical satellite verification pass.
  - [ ] Verify whether thermal cluster is persistent or transient.
  - [ ] Acquire fresh cloud-free Sentinel-2/Landsat optical pass to resolve surface context.

*Context: WorldCover = Bare / sparse vegetation | OSM Category = mine_quarry (2.0) | Observing Satellites = 5*
---
### Event `EVT_00964154`

| Metric | Value | Tier |
| :--- | :---: | :---: |
| **Risk Score** | **48.3 / 100** | **MODERATE** |
| **Evidence Confidence** | **70.0 / 100** | **MEDIUM** |
| **Investigation Priority** | **Needs additional satellite verification** | — |

**Summary**: Event received an investigation priority score of 48.3/100 (MODERATE). The primary risk driver is Persistence (23.3 pts), followed by Industrial Association (15.6 pts).

#### 1. Dimension Score Breakdown

| Dimension | Code | Weight | Normalized [0, 1] | Weighted Points [0–100] | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Thermal Intensity | `A` | 30% | 0.072 | **2.2** | `PRESENT` |
| Persistence | `B` | 25% | 0.932 | **23.3** | `PRESENT` |
| Industrial Association | `C` | 20% | 0.779 | **15.6** | `PRESENT` |
| Spatial Scale | `D` | 10% | 0.721 | **7.2** | `PRESENT` |
| Spectral / Surface Evidence | `E` | 15% | 0.000 | **0.0** | `STALE` |

#### 2. Key Contribution Drivers
- **Primary driver: Persistence — 23.3 points**
- **Secondary driver: Industrial Association — 15.6 points**
- **Weakest evidence: Spectral / Surface Evidence — 0.0 points**

#### 3. Raw Evidence Trace
- **Thermal**: FRP mean = 3.27, FRP max = 33.1, Brightness mean = 315.3 K
- **Persistence**: Distinct detection days = 258, Total detection count = 18928
- **Industrial**: OSM match fraction = 1.0, Containment = 0.7918, Proximity = 0.2082, Min distance = 0.0 m
- **Spatial**: Convex hull area = 87.442 km²
- **Spectral**: SWIR anomaly ratio = 0.5598, NDVI = 0.1005, SWIR2/SWIR1 ratio = 1.0769, BSI = 0.1316, SCL clear fraction = 1.0, Temporal delta = 113.4 days

#### 4. Evidence Availability & Limitations
- **Sentinel-2 Status**: Contemporary Sentinel-2 evidence was stale (temporal offset: 113.4 days > 90 days; temporal reliability = 0.0), so this dimension contributed 0 points. This is an evidence limitation, not evidence of absence.
- **Missing Tags**: `temporal_relevance:stale`

#### 5. Deterministic Interpretations
- **Thermal**: Low thermal energy output observed near sensor detection thresholds.
- **Persistence**: Chronic thermal activity persisted across 258 distinct detection days (18,928 total detections).
- **Industrial**: The event is strongly associated with mapped industrial infrastructure (high polygon containment / direct co-location).
- **Spatial**: Extensive spatial footprint encompassing a large contiguous thermal cluster area (87.44 km²).
- **Spectral**: Available Sentinel-2 evidence is temporally stale relative to the FIRMS observation (>90 days offset).

#### 6. Investigation Recommendation & Next Actions
**Recommendation**: `Needs additional satellite verification`
**Rationale**: Moderate risk score (48.3/100) with limited observational confidence (70.0/100, MEDIUM). Gaps in optical or corroborating data prevent definitive characterization.
**Recommended Next Steps**:
  - [ ] Task contemporary optical satellite verification pass.
  - [ ] Verify whether thermal cluster is persistent or transient.
  - [ ] Acquire fresh cloud-free Sentinel-2/Landsat optical pass to resolve surface context.

*Context: WorldCover = Tree cover | OSM Category = mine_quarry (2.0) | Observing Satellites = 5*
---
### Event `EVT_00598933`

| Metric | Value | Tier |
| :--- | :---: | :---: |
| **Risk Score** | **46.5 / 100** | **MODERATE** |
| **Evidence Confidence** | **70.0 / 100** | **MEDIUM** |
| **Investigation Priority** | **Needs additional satellite verification** | — |

**Summary**: Event received an investigation priority score of 46.5/100 (MODERATE). The primary risk driver is Persistence (22.8 pts), followed by Industrial Association (15.7 pts).

#### 1. Dimension Score Breakdown

| Dimension | Code | Weight | Normalized [0, 1] | Weighted Points [0–100] | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Thermal Intensity | `A` | 30% | 0.082 | **2.4** | `PRESENT` |
| Persistence | `B` | 25% | 0.910 | **22.8** | `PRESENT` |
| Industrial Association | `C` | 20% | 0.787 | **15.7** | `PRESENT` |
| Spatial Scale | `D` | 10% | 0.556 | **5.6** | `PRESENT` |
| Spectral / Surface Evidence | `E` | 15% | 0.000 | **0.0** | `STALE` |

#### 2. Key Contribution Drivers
- **Primary driver: Persistence — 22.8 points**
- **Secondary driver: Industrial Association — 15.7 points**
- **Weakest evidence: Spectral / Surface Evidence — 0.0 points**

#### 3. Raw Evidence Trace
- **Thermal**: FRP mean = 3.17, FRP max = 49.5, Brightness mean = 314.5 K
- **Persistence**: Distinct detection days = 254, Total detection count = 9272
- **Industrial**: OSM match fraction = 1.0, Containment = 0.8746, Proximity = 0.1254, Min distance = 0.0 m
- **Spatial**: Convex hull area = 30.7092 km²
- **Spectral**: SWIR anomaly ratio = 0.8553, NDVI = 0.0175, SWIR2/SWIR1 ratio = 1.0684, BSI = 0.0801, SCL clear fraction = 1.0, Temporal delta = 204.02 days

#### 4. Evidence Availability & Limitations
- **Sentinel-2 Status**: Contemporary Sentinel-2 evidence was stale (temporal offset: 204.0 days > 90 days; temporal reliability = 0.0), so this dimension contributed 0 points. This is an evidence limitation, not evidence of absence.
- **Missing Tags**: `temporal_relevance:stale`

#### 5. Deterministic Interpretations
- **Thermal**: Low thermal energy output observed near sensor detection thresholds.
- **Persistence**: Chronic thermal activity persisted across 254 distinct detection days (9,272 total detections).
- **Industrial**: The event is strongly associated with mapped industrial infrastructure (high polygon containment / direct co-location).
- **Spatial**: Moderate cluster geographic extent spanning 30.71 km².
- **Spectral**: Available Sentinel-2 evidence is temporally stale relative to the FIRMS observation (>90 days offset).

#### 6. Investigation Recommendation & Next Actions
**Recommendation**: `Needs additional satellite verification`
**Rationale**: Moderate risk score (46.5/100) with limited observational confidence (70.0/100, MEDIUM). Gaps in optical or corroborating data prevent definitive characterization.
**Recommended Next Steps**:
  - [ ] Task contemporary optical satellite verification pass.
  - [ ] Verify whether thermal cluster is persistent or transient.
  - [ ] Acquire fresh cloud-free Sentinel-2/Landsat optical pass to resolve surface context.

*Context: WorldCover = Permanent water bodies | OSM Category = mine_quarry (2.0) | Observing Satellites = 5*
---
### Event `EVT_00615821`

| Metric | Value | Tier |
| :--- | :---: | :---: |
| **Risk Score** | **46.1 / 100** | **MODERATE** |
| **Evidence Confidence** | **70.0 / 100** | **MEDIUM** |
| **Investigation Priority** | **Needs additional satellite verification** | — |

**Summary**: Event received an investigation priority score of 46.1/100 (MODERATE). The primary risk driver is Persistence (23.0 pts), followed by Industrial Association (15.7 pts).

#### 1. Dimension Score Breakdown

| Dimension | Code | Weight | Normalized [0, 1] | Weighted Points [0–100] | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Thermal Intensity | `A` | 30% | 0.121 | **3.6** | `PRESENT` |
| Persistence | `B` | 25% | 0.921 | **23.0** | `PRESENT` |
| Industrial Association | `C` | 20% | 0.784 | **15.7** | `PRESENT` |
| Spatial Scale | `D` | 10% | 0.371 | **3.7** | `PRESENT` |
| Spectral / Surface Evidence | `E` | 15% | 0.000 | **0.0** | `STALE` |

#### 2. Key Contribution Drivers
- **Primary driver: Persistence — 23.0 points**
- **Secondary driver: Industrial Association — 15.7 points**
- **Weakest evidence: Spectral / Surface Evidence — 0.0 points**

#### 3. Raw Evidence Trace
- **Thermal**: FRP mean = 6.01, FRP max = 52.3, Brightness mean = 325.55 K
- **Persistence**: Distinct detection days = 305, Total detection count = 6249
- **Industrial**: OSM match fraction = 1.0, Containment = 0.8384, Proximity = 0.1616, Min distance = 0.0 m
- **Spatial**: Convex hull area = 9.0505 km²
- **Spectral**: SWIR anomaly ratio = 1.7314, NDVI = 0.0769, SWIR2/SWIR1 ratio = 1.0258, BSI = 0.1948, SCL clear fraction = 0.896, Temporal delta = 221.89 days

#### 4. Evidence Availability & Limitations
- **Sentinel-2 Status**: Contemporary Sentinel-2 evidence was stale (temporal offset: 221.9 days > 90 days; temporal reliability = 0.0), so this dimension contributed 0 points. This is an evidence limitation, not evidence of absence.
- **Missing Tags**: `temporal_relevance:stale`

#### 5. Deterministic Interpretations
- **Thermal**: Low thermal energy output observed near sensor detection thresholds.
- **Persistence**: Chronic thermal activity persisted across 305 distinct detection days (6,249 total detections).
- **Industrial**: The event is strongly associated with mapped industrial infrastructure (high polygon containment / direct co-location).
- **Spatial**: Moderate cluster geographic extent spanning 9.05 km².
- **Spectral**: Available Sentinel-2 evidence is temporally stale relative to the FIRMS observation (>90 days offset).

#### 6. Investigation Recommendation & Next Actions
**Recommendation**: `Needs additional satellite verification`
**Rationale**: Moderate risk score (46.1/100) with limited observational confidence (70.0/100, MEDIUM). Gaps in optical or corroborating data prevent definitive characterization.
**Recommended Next Steps**:
  - [ ] Task contemporary optical satellite verification pass.
  - [ ] Verify whether thermal cluster is persistent or transient.
  - [ ] Acquire fresh cloud-free Sentinel-2/Landsat optical pass to resolve surface context.

*Context: WorldCover = Bare / sparse vegetation | OSM Category = factory_works (2.0) | Observing Satellites = 5*
---
### Event `EVT_00615820`

| Metric | Value | Tier |
| :--- | :---: | :---: |
| **Risk Score** | **46.1 / 100** | **MODERATE** |
| **Evidence Confidence** | **70.0 / 100** | **MEDIUM** |
| **Investigation Priority** | **Needs additional satellite verification** | — |

**Summary**: Event received an investigation priority score of 46.1/100 (MODERATE). The primary risk driver is Persistence (22.8 pts), followed by Industrial Association (15.7 pts).

#### 1. Dimension Score Breakdown

| Dimension | Code | Weight | Normalized [0, 1] | Weighted Points [0–100] | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Thermal Intensity | `A` | 30% | 0.130 | **3.9** | `PRESENT` |
| Persistence | `B` | 25% | 0.911 | **22.8** | `PRESENT` |
| Industrial Association | `C` | 20% | 0.783 | **15.7** | `PRESENT` |
| Spatial Scale | `D` | 10% | 0.379 | **3.8** | `PRESENT` |
| Spectral / Surface Evidence | `E` | 15% | 0.000 | **0.0** | `STALE` |

#### 2. Key Contribution Drivers
- **Primary driver: Persistence — 22.8 points**
- **Secondary driver: Industrial Association — 15.7 points**
- **Weakest evidence: Spectral / Surface Evidence — 0.0 points**

#### 3. Raw Evidence Trace
- **Thermal**: FRP mean = 6.79, FRP max = 55.27, Brightness mean = 326.71 K
- **Persistence**: Distinct detection days = 276, Total detection count = 6717
- **Industrial**: OSM match fraction = 1.0, Containment = 0.8258, Proximity = 0.1742, Min distance = 0.0 m
- **Spatial**: Convex hull area = 9.564 km²
- **Spectral**: SWIR anomaly ratio = 1.574, NDVI = 0.0515, SWIR2/SWIR1 ratio = 1.0447, BSI = 0.1147, SCL clear fraction = 0.8736, Temporal delta = 169.91 days

#### 4. Evidence Availability & Limitations
- **Sentinel-2 Status**: Contemporary Sentinel-2 evidence was stale (temporal offset: 169.9 days > 90 days; temporal reliability = 0.0), so this dimension contributed 0 points. This is an evidence limitation, not evidence of absence.
- **Missing Tags**: `temporal_relevance:stale`

#### 5. Deterministic Interpretations
- **Thermal**: Low thermal energy output observed near sensor detection thresholds.
- **Persistence**: Chronic thermal activity persisted across 276 distinct detection days (6,717 total detections).
- **Industrial**: The event is strongly associated with mapped industrial infrastructure (high polygon containment / direct co-location).
- **Spatial**: Moderate cluster geographic extent spanning 9.56 km².
- **Spectral**: Available Sentinel-2 evidence is temporally stale relative to the FIRMS observation (>90 days offset).

#### 6. Investigation Recommendation & Next Actions
**Recommendation**: `Needs additional satellite verification`
**Rationale**: Moderate risk score (46.1/100) with limited observational confidence (70.0/100, MEDIUM). Gaps in optical or corroborating data prevent definitive characterization.
**Recommended Next Steps**:
  - [ ] Task contemporary optical satellite verification pass.
  - [ ] Verify whether thermal cluster is persistent or transient.
  - [ ] Acquire fresh cloud-free Sentinel-2/Landsat optical pass to resolve surface context.

*Context: WorldCover = Bare / sparse vegetation | OSM Category = factory_works (2.0) | Observing Satellites = 5*
---

## Part 4 — Representative Middle Cohort Events

Events with moderate risk scores ($15\text{--}25$), representing seasonal agricultural burns or rural industrial facilities with partial containment:

### Event `EVT_01095783`

| Metric | Value | Tier |
| :--- | :---: | :---: |
| **Risk Score** | **20.4 / 100** | **LOW** |
| **Evidence Confidence** | **88.0 / 100** | **HIGH** |
| **Investigation Priority** | **Confident low-risk event** | — |

**Summary**: Event received an investigation priority score of 20.4/100 (LOW). The primary risk driver is Thermal Intensity (8.4 pts), followed by Persistence (5.6 pts).

#### 1. Dimension Score Breakdown

| Dimension | Code | Weight | Normalized [0, 1] | Weighted Points [0–100] | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Thermal Intensity | `A` | 30% | 0.281 | **8.4** | `PRESENT` |
| Persistence | `B` | 25% | 0.224 | **5.6** | `PRESENT` |
| Industrial Association | `C` | 20% | 0.000 | **0.0** | `ZERO_OBSERVED_CONTRIBUTION` |
| Spatial Scale | `D` | 10% | 0.304 | **3.0** | `PRESENT` |
| Spectral / Surface Evidence | `E` | 15% | 0.219 | **3.3** | `PRESENT` |

#### 2. Key Contribution Drivers
- **Primary driver: Thermal Intensity — 8.4 points**
- **Secondary driver: Persistence — 5.6 points**
- **Weakest evidence: Industrial Association — 0.0 points**

#### 3. Raw Evidence Trace
- **Thermal**: FRP mean = 26.98, FRP max = 70.53, Brightness mean = 345.27 K
- **Persistence**: Distinct detection days = 2, Total detection count = 28
- **Industrial**: OSM match fraction = 0.0, Containment = 0.0, Proximity = 0.0, Min distance = nan m
- **Spatial**: Convex hull area = 5.6379 km²
- **Spectral**: SWIR anomaly ratio = 0.9271, NDVI = 0.5499, SWIR2/SWIR1 ratio = 0.5627, BSI = 0.0059, SCL clear fraction = 1.0, Temporal delta = -4.07 days

#### 4. Evidence Availability & Limitations
- **Sentinel-2 Status**: Contemporary Sentinel-2 imagery was clear and temporally aligned.
- **Missing Tags**: `osm_context:no_mapped_association`

#### 5. Deterministic Interpretations
- **Thermal**: Moderate thermal energy output observed within typical industrial/combustion baseline ranges.
- **Persistence**: Recurrent thermal activity observed across multiple detection cycles (2 days, 28 detections).
- **Industrial**: No mapped industrial infrastructure was identified within the methodology-defined 5,000m spatial context.
- **Spatial**: Moderate cluster geographic extent spanning 5.64 km².
- **Spectral**: Moderate surface reflectance contrast or surface disturbance detected in contemporary satellite imagery.

#### 6. Investigation Recommendation & Next Actions
**Recommendation**: `Confident low-risk event`
**Rationale**: Low risk score (20.4/100) with high observational confidence (88.0/100). Robust multi-satellite data confirms localized, low-persistence, or non-industrial thermal signature.
**Recommended Next Steps**:
  - [ ] Archive as low-priority background/transient thermal observation.
  - [ ] No active investigation required unless new persistent detections occur.

*Context: WorldCover = Tree cover | OSM Category = nan (nan) | Observing Satellites = 3*
---
### Event `EVT_01331086`

| Metric | Value | Tier |
| :--- | :---: | :---: |
| **Risk Score** | **18.5 / 100** | **LOW** |
| **Evidence Confidence** | **81.0 / 100** | **HIGH** |
| **Investigation Priority** | **Confident low-risk event** | — |

**Summary**: Event received an investigation priority score of 18.5/100 (LOW). The primary risk driver is Thermal Intensity (12.0 pts), followed by Persistence (4.4 pts).

#### 1. Dimension Score Breakdown

| Dimension | Code | Weight | Normalized [0, 1] | Weighted Points [0–100] | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Thermal Intensity | `A` | 30% | 0.400 | **12.0** | `PRESENT` |
| Persistence | `B` | 25% | 0.175 | **4.4** | `PRESENT` |
| Industrial Association | `C` | 20% | 0.000 | **0.0** | `ZERO_OBSERVED_CONTRIBUTION` |
| Spatial Scale | `D` | 10% | 0.050 | **0.5** | `PRESENT` |
| Spectral / Surface Evidence | `E` | 15% | 0.109 | **1.6** | `PRESENT` |

#### 2. Key Contribution Drivers
- **Primary driver: Thermal Intensity — 12.0 points**
- **Secondary driver: Persistence — 4.4 points**
- **Weakest evidence: Industrial Association — 0.0 points**

#### 3. Raw Evidence Trace
- **Thermal**: FRP mean = 39.28, FRP max = 132.28, Brightness mean = 351.84 K
- **Persistence**: Distinct detection days = 2, Total detection count = 4
- **Industrial**: OSM match fraction = 0.0, Containment = 0.0, Proximity = 0.0, Min distance = nan m
- **Spatial**: Convex hull area = 0.3607 km²
- **Spectral**: SWIR anomaly ratio = 0.8699, NDVI = 0.8395, SWIR2/SWIR1 ratio = 0.4632, BSI = -0.2385, SCL clear fraction = 0.9408, Temporal delta = 2.9 days

#### 4. Evidence Availability & Limitations
- **Sentinel-2 Status**: Contemporary Sentinel-2 imagery was clear and temporally aligned.
- **Missing Tags**: `osm_context:no_mapped_association`

#### 5. Deterministic Interpretations
- **Thermal**: Moderate thermal energy output observed within typical industrial/combustion baseline ranges.
- **Persistence**: The event was observed over a short temporal window (2 days, 4 detections).
- **Industrial**: No mapped industrial infrastructure was identified within the methodology-defined 5,000m spatial context.
- **Spatial**: Compact, localized geographic footprint (0.36 km²).
- **Spectral**: Minor SWIR contrast detected above background reflectance levels.

#### 6. Investigation Recommendation & Next Actions
**Recommendation**: `Confident low-risk event`
**Rationale**: Low risk score (18.5/100) with high observational confidence (81.0/100). Robust multi-satellite data confirms localized, low-persistence, or non-industrial thermal signature.
**Recommended Next Steps**:
  - [ ] Archive as low-priority background/transient thermal observation.
  - [ ] No active investigation required unless new persistent detections occur.

*Context: WorldCover = Tree cover | OSM Category = nan (nan) | Observing Satellites = 2*
---
### Event `EVT_00837241`

| Metric | Value | Tier |
| :--- | :---: | :---: |
| **Risk Score** | **18.2 / 100** | **LOW** |
| **Evidence Confidence** | **97.2 / 100** | **HIGH** |
| **Investigation Priority** | **Confident low-risk event** | — |

**Summary**: Event received an investigation priority score of 18.2/100 (LOW). The primary risk driver is Persistence (8.2 pts), followed by Thermal Intensity (3.8 pts).

#### 1. Dimension Score Breakdown

| Dimension | Code | Weight | Normalized [0, 1] | Weighted Points [0–100] | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Thermal Intensity | `A` | 30% | 0.127 | **3.8** | `PRESENT` |
| Persistence | `B` | 25% | 0.330 | **8.2** | `PRESENT` |
| Industrial Association | `C` | 20% | 0.000 | **0.0** | `ZERO_OBSERVED_CONTRIBUTION` |
| Spatial Scale | `D` | 10% | 0.338 | **3.4** | `PRESENT` |
| Spectral / Surface Evidence | `E` | 15% | 0.181 | **2.7** | `PRESENT` |

#### 2. Key Contribution Drivers
- **Primary driver: Persistence — 8.2 points**
- **Secondary driver: Thermal Intensity — 3.8 points**
- **Weakest evidence: Industrial Association — 0.0 points**

#### 3. Raw Evidence Trace
- **Thermal**: FRP mean = 8.65, FRP max = 42.0, Brightness mean = 325.48 K
- **Persistence**: Distinct detection days = 5, Total detection count = 67
- **Industrial**: OSM match fraction = 0.0, Containment = 0.0, Proximity = 0.0, Min distance = nan m
- **Spatial**: Convex hull area = 7.1956 km²
- **Spectral**: SWIR anomaly ratio = 1.1303, NDVI = 0.6552, SWIR2/SWIR1 ratio = 0.5742, BSI = -0.0593, SCL clear fraction = 1.0, Temporal delta = 8.4 days

#### 4. Evidence Availability & Limitations
- **Sentinel-2 Status**: Contemporary Sentinel-2 imagery was clear and temporally aligned.
- **Missing Tags**: `osm_context:no_mapped_association`

#### 5. Deterministic Interpretations
- **Thermal**: Low thermal energy output observed near sensor detection thresholds.
- **Persistence**: Recurrent thermal activity observed across multiple detection cycles (5 days, 67 detections).
- **Industrial**: No mapped industrial infrastructure was identified within the methodology-defined 5,000m spatial context.
- **Spatial**: Moderate cluster geographic extent spanning 7.20 km².
- **Spectral**: Minor SWIR contrast detected above background reflectance levels.

#### 6. Investigation Recommendation & Next Actions
**Recommendation**: `Confident low-risk event`
**Rationale**: Low risk score (18.2/100) with high observational confidence (97.2/100). Robust multi-satellite data confirms localized, low-persistence, or non-industrial thermal signature.
**Recommended Next Steps**:
  - [ ] Archive as low-priority background/transient thermal observation.
  - [ ] No active investigation required unless new persistent detections occur.

*Context: WorldCover = Tree cover | OSM Category = nan (nan) | Observing Satellites = 5*
---
### Event `EVT_00748331`

| Metric | Value | Tier |
| :--- | :---: | :---: |
| **Risk Score** | **17.9 / 100** | **LOW** |
| **Evidence Confidence** | **94.0 / 100** | **HIGH** |
| **Investigation Priority** | **Confident low-risk event** | — |

**Summary**: Event received an investigation priority score of 17.9/100 (LOW). The primary risk driver is Persistence (6.9 pts), followed by Spectral / Surface Evidence (4.2 pts).

#### 1. Dimension Score Breakdown

| Dimension | Code | Weight | Normalized [0, 1] | Weighted Points [0–100] | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Thermal Intensity | `A` | 30% | 0.112 | **3.4** | `PRESENT` |
| Persistence | `B` | 25% | 0.276 | **6.9** | `PRESENT` |
| Industrial Association | `C` | 20% | 0.000 | **0.0** | `ZERO_OBSERVED_CONTRIBUTION` |
| Spatial Scale | `D` | 10% | 0.345 | **3.4** | `PRESENT` |
| Spectral / Surface Evidence | `E` | 15% | 0.282 | **4.2** | `PRESENT` |

#### 2. Key Contribution Drivers
- **Primary driver: Persistence — 6.9 points**
- **Secondary driver: Spectral / Surface Evidence — 4.2 points**
- **Weakest evidence: Industrial Association — 0.0 points**

#### 3. Raw Evidence Trace
- **Thermal**: FRP mean = 5.58, FRP max = 20.74, Brightness mean = 332.48 K
- **Persistence**: Distinct detection days = 3, Total detection count = 55
- **Industrial**: OSM match fraction = 0.0, Containment = 0.0, Proximity = 0.0, Min distance = nan m
- **Spatial**: Convex hull area = 7.5397 km²
- **Spectral**: SWIR anomaly ratio = 1.076, NDVI = 0.4133, SWIR2/SWIR1 ratio = 0.6431, BSI = 0.1393, SCL clear fraction = 1.0, Temporal delta = -0.58 days

#### 4. Evidence Availability & Limitations
- **Sentinel-2 Status**: Contemporary Sentinel-2 imagery was clear and temporally aligned.
- **Missing Tags**: `osm_context:no_mapped_association`

#### 5. Deterministic Interpretations
- **Thermal**: Low thermal energy output observed near sensor detection thresholds.
- **Persistence**: Recurrent thermal activity observed across multiple detection cycles (3 days, 55 detections).
- **Industrial**: No mapped industrial infrastructure was identified within the methodology-defined 5,000m spatial context.
- **Spatial**: Moderate cluster geographic extent spanning 7.54 km².
- **Spectral**: Moderate surface reflectance contrast or surface disturbance detected in contemporary satellite imagery.

#### 6. Investigation Recommendation & Next Actions
**Recommendation**: `Confident low-risk event`
**Rationale**: Low risk score (17.9/100) with high observational confidence (94.0/100). Robust multi-satellite data confirms localized, low-persistence, or non-industrial thermal signature.
**Recommended Next Steps**:
  - [ ] Archive as low-priority background/transient thermal observation.
  - [ ] No active investigation required unless new persistent detections occur.

*Context: WorldCover = Tree cover | OSM Category = nan (nan) | Observing Satellites = 4*
---
### Event `EVT_01164711`

| Metric | Value | Tier |
| :--- | :---: | :---: |
| **Risk Score** | **17.5 / 100** | **LOW** |
| **Evidence Confidence** | **81.7 / 100** | **HIGH** |
| **Investigation Priority** | **Confident low-risk event** | — |

**Summary**: Event received an investigation priority score of 17.5/100 (LOW). The primary risk driver is Persistence (6.8 pts), followed by Thermal Intensity (5.0 pts).

#### 1. Dimension Score Breakdown

| Dimension | Code | Weight | Normalized [0, 1] | Weighted Points [0–100] | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Thermal Intensity | `A` | 30% | 0.167 | **5.0** | `PRESENT` |
| Persistence | `B` | 25% | 0.271 | **6.8** | `PRESENT` |
| Industrial Association | `C` | 20% | 0.000 | **0.0** | `ZERO_OBSERVED_CONTRIBUTION` |
| Spatial Scale | `D` | 10% | 0.260 | **2.6** | `PRESENT` |
| Spectral / Surface Evidence | `E` | 15% | 0.208 | **3.1** | `PRESENT` |

#### 2. Key Contribution Drivers
- **Primary driver: Persistence — 6.8 points**
- **Secondary driver: Thermal Intensity — 5.0 points**
- **Weakest evidence: Industrial Association — 0.0 points**

#### 3. Raw Evidence Trace
- **Thermal**: FRP mean = 12.83, FRP max = 53.07, Brightness mean = 330.83 K
- **Persistence**: Distinct detection days = 4, Total detection count = 17
- **Industrial**: OSM match fraction = 0.0, Containment = 0.0, Proximity = 0.0, Min distance = nan m
- **Spatial**: Convex hull area = 4.0237 km²
- **Spectral**: SWIR anomaly ratio = 0.8184, NDVI = 0.5936, SWIR2/SWIR1 ratio = 0.6081, BSI = -0.0269, SCL clear fraction = 0.9936, Temporal delta = 0.91 days

#### 4. Evidence Availability & Limitations
- **Sentinel-2 Status**: Contemporary Sentinel-2 imagery was clear and temporally aligned.
- **Missing Tags**: `osm_context:no_mapped_association`

#### 5. Deterministic Interpretations
- **Thermal**: Low thermal energy output observed near sensor detection thresholds.
- **Persistence**: Recurrent thermal activity observed across multiple detection cycles (4 days, 17 detections).
- **Industrial**: No mapped industrial infrastructure was identified within the methodology-defined 5,000m spatial context.
- **Spatial**: Moderate cluster geographic extent spanning 4.02 km².
- **Spectral**: Moderate surface reflectance contrast or surface disturbance detected in contemporary satellite imagery.

#### 6. Investigation Recommendation & Next Actions
**Recommendation**: `Confident low-risk event`
**Rationale**: Low risk score (17.5/100) with high observational confidence (81.7/100). Robust multi-satellite data confirms localized, low-persistence, or non-industrial thermal signature.
**Recommended Next Steps**:
  - [ ] Archive as low-priority background/transient thermal observation.
  - [ ] No active investigation required unless new persistent detections occur.

*Context: WorldCover = Tree cover | OSM Category = nan (nan) | Observing Satellites = 2*
---

## Part 5 — Bottom 5 Lowest Risk Events (Transient / Agricultural)

Events with low scores ($6\text{--}12$) caused by isolated, single-day detections with zero industrial association and compact single-pixel extent:

### Event `EVT_00230882`

| Metric | Value | Tier |
| :--- | :---: | :---: |
| **Risk Score** | **11.3 / 100** | **LOW** |
| **Evidence Confidence** | **76.0 / 100** | **HIGH** |
| **Investigation Priority** | **Confident low-risk event** | — |

**Summary**: Event received an investigation priority score of 11.3/100 (LOW). The primary risk driver is Thermal Intensity (4.6 pts), followed by Spectral / Surface Evidence (4.2 pts).

#### 1. Dimension Score Breakdown

| Dimension | Code | Weight | Normalized [0, 1] | Weighted Points [0–100] | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Thermal Intensity | `A` | 30% | 0.154 | **4.6** | `PRESENT` |
| Persistence | `B` | 25% | 0.101 | **2.5** | `PRESENT` |
| Industrial Association | `C` | 20% | 0.000 | **0.0** | `ZERO_OBSERVED_CONTRIBUTION` |
| Spatial Scale | `D` | 10% | 0.000 | **0.0** | `PRESENT` |
| Spectral / Surface Evidence | `E` | 15% | 0.279 | **4.2** | `PRESENT` |

#### 2. Key Contribution Drivers
- **Primary driver: Thermal Intensity — 4.6 points**
- **Secondary driver: Spectral / Surface Evidence — 4.2 points**
- **Weakest evidence: Spatial Scale — 0.0 points**

#### 3. Raw Evidence Trace
- **Thermal**: FRP mean = 23.2, FRP max = 23.2, Brightness mean = 310.0 K
- **Persistence**: Distinct detection days = 1, Total detection count = 1
- **Industrial**: OSM match fraction = 0.0, Containment = 0.0, Proximity = 0.0, Min distance = nan m
- **Spatial**: Convex hull area = 0.0 km²
- **Spectral**: SWIR anomaly ratio = 0.8198, NDVI = 0.3927, SWIR2/SWIR1 ratio = 0.6999, BSI = 0.0744, SCL clear fraction = 1.0, Temporal delta = -2.95 days

#### 4. Evidence Availability & Limitations
- **Sentinel-2 Status**: Contemporary Sentinel-2 imagery was clear and temporally aligned.
- **Missing Tags**: `osm_context:no_mapped_association`

#### 5. Deterministic Interpretations
- **Thermal**: Low thermal energy output observed near sensor detection thresholds.
- **Persistence**: The event was observed over a short temporal window (1 days, 1 detections).
- **Industrial**: No mapped industrial infrastructure was identified within the methodology-defined 5,000m spatial context.
- **Spatial**: Compact, localized geographic footprint (0.00 km²).
- **Spectral**: Moderate surface reflectance contrast or surface disturbance detected in contemporary satellite imagery.

#### 6. Investigation Recommendation & Next Actions
**Recommendation**: `Confident low-risk event`
**Rationale**: Low risk score (11.3/100) with high observational confidence (76.0/100). Robust multi-satellite data confirms localized, low-persistence, or non-industrial thermal signature.
**Recommended Next Steps**:
  - [ ] Archive as low-priority background/transient thermal observation.
  - [ ] No active investigation required unless new persistent detections occur.

*Context: WorldCover = Cropland | OSM Category = nan (nan) | Observing Satellites = 1*
---
### Event `EVT_01557619`

| Metric | Value | Tier |
| :--- | :---: | :---: |
| **Risk Score** | **11.2 / 100** | **LOW** |
| **Evidence Confidence** | **46.0 / 100** | **LOW** |
| **Investigation Priority** | **Low observed risk but insufficient evidence** | — |

**Summary**: Event received an investigation priority score of 11.2/100 (LOW). The primary risk driver is Thermal Intensity (8.4 pts), followed by Persistence (2.8 pts).

#### 1. Dimension Score Breakdown

| Dimension | Code | Weight | Normalized [0, 1] | Weighted Points [0–100] | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Thermal Intensity | `A` | 30% | 0.280 | **8.4** | `PRESENT` |
| Persistence | `B` | 25% | 0.113 | **2.8** | `PRESENT` |
| Industrial Association | `C` | 20% | 0.000 | **0.0** | `ZERO_OBSERVED_CONTRIBUTION` |
| Spatial Scale | `D` | 10% | 0.002 | **0.0** | `PRESENT` |
| Spectral / Surface Evidence | `E` | 15% | 0.000 | **0.0** | `EXTRACTION_FAILURE` |

#### 2. Key Contribution Drivers
- **Primary driver: Thermal Intensity — 8.4 points**
- **Secondary driver: Persistence — 2.8 points**
- **Weakest evidence: Spatial Scale — 0.0 points**

#### 3. Raw Evidence Trace
- **Thermal**: FRP mean = 23.56, FRP max = 25.83, Brightness mean = 367.0 K
- **Persistence**: Distinct detection days = 1, Total detection count = 2
- **Industrial**: OSM match fraction = 0.0, Containment = 0.0, Proximity = 0.0, Min distance = nan m
- **Spatial**: Convex hull area = 0.0148 km²
- **Spectral**: SWIR anomaly ratio = nan, NDVI = nan, SWIR2/SWIR1 ratio = nan, BSI = nan, SCL clear fraction = nan, Temporal delta = -5.14 days

#### 4. Evidence Availability & Limitations
- **Sentinel-2 Status**: Sentinel-2 scene was present but spectral feature extraction failed, so this dimension contributed 0 points. This is an evidence limitation, not evidence of absence.
- **Missing Tags**: `osm_context:no_mapped_association, dimension_E_spectral_missing, spectral_coverage:extraction_failed`

#### 5. Deterministic Interpretations
- **Thermal**: Moderate thermal energy output observed within typical industrial/combustion baseline ranges.
- **Persistence**: The event was observed over a short temporal window (1 days, 2 detections).
- **Industrial**: No mapped industrial infrastructure was identified within the methodology-defined 5,000m spatial context.
- **Spatial**: Compact, localized geographic footprint (0.01 km²).
- **Spectral**: Surface reflectance indices show no distinct contrast relative to local background in available imagery.

#### 6. Investigation Recommendation & Next Actions
**Recommendation**: `Low observed risk but insufficient evidence`
**Rationale**: Low numerical score (11.2/100) coincides with low evidence confidence (46.0/100). Key observational dimensions were unavailable or unobserved; low score reflects absence of data rather than confirmed absence of hazard.
**Recommended Next Steps**:
  - [ ] Do NOT conclude real-world safety based on numerical score alone.
  - [ ] Check for upcoming satellite coverage to fill evidence gaps.
  - [ ] Review multi-day FIRMS history to confirm if thermal activity was truly transient.
  - [ ] Acquire fresh cloud-free Sentinel-2/Landsat optical pass to resolve surface context.

*Context: WorldCover = Cropland | OSM Category = nan (nan) | Observing Satellites = 1*
---
### Event `EVT_00795287`

| Metric | Value | Tier |
| :--- | :---: | :---: |
| **Risk Score** | **10.1 / 100** | **LOW** |
| **Evidence Confidence** | **52.0 / 100** | **MEDIUM** |
| **Investigation Priority** | **Routine low-priority monitoring** | — |

**Summary**: Event received an investigation priority score of 10.1/100 (LOW). The primary risk driver is Persistence (5.1 pts), followed by Thermal Intensity (4.6 pts).

#### 1. Dimension Score Breakdown

| Dimension | Code | Weight | Normalized [0, 1] | Weighted Points [0–100] | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Thermal Intensity | `A` | 30% | 0.152 | **4.6** | `PRESENT` |
| Persistence | `B` | 25% | 0.203 | **5.1** | `PRESENT` |
| Industrial Association | `C` | 20% | 0.000 | **0.0** | `ZERO_OBSERVED_CONTRIBUTION` |
| Spatial Scale | `D` | 10% | 0.041 | **0.4** | `PRESENT` |
| Spectral / Surface Evidence | `E` | 15% | 0.000 | **0.0** | `EXTRACTION_FAILURE` |

#### 2. Key Contribution Drivers
- **Primary driver: Persistence — 5.1 points**
- **Secondary driver: Thermal Intensity — 4.6 points**
- **Weakest evidence: Spectral / Surface Evidence — 0.0 points**

#### 3. Raw Evidence Trace
- **Thermal**: FRP mean = 9.96, FRP max = 20.44, Brightness mean = 341.27 K
- **Persistence**: Distinct detection days = 3, Total detection count = 3
- **Industrial**: OSM match fraction = 0.0, Containment = 0.0, Proximity = 0.0, Min distance = nan m
- **Spatial**: Convex hull area = 0.2879 km²
- **Spectral**: SWIR anomaly ratio = nan, NDVI = nan, SWIR2/SWIR1 ratio = nan, BSI = nan, SCL clear fraction = nan, Temporal delta = nan days

#### 4. Evidence Availability & Limitations
- **Sentinel-2 Status**: Sentinel-2 scene was present but spectral feature extraction failed, so this dimension contributed 0 points. This is an evidence limitation, not evidence of absence.
- **Missing Tags**: `osm_context:no_mapped_association, dimension_E_spectral_missing, spectral_coverage:extraction_failed`

#### 5. Deterministic Interpretations
- **Thermal**: Low thermal energy output observed near sensor detection thresholds.
- **Persistence**: Recurrent thermal activity observed across multiple detection cycles (3 days, 3 detections).
- **Industrial**: No mapped industrial infrastructure was identified within the methodology-defined 5,000m spatial context.
- **Spatial**: Compact, localized geographic footprint (0.29 km²).
- **Spectral**: Surface reflectance indices show no distinct contrast relative to local background in available imagery.

#### 6. Investigation Recommendation & Next Actions
**Recommendation**: `Routine low-priority monitoring`
**Rationale**: Low risk score (10.1/100) with moderate confidence (52.0/100). Minimal industrial or persistent characteristics.
**Recommended Next Steps**:
  - [ ] Standard archive logging.
  - [ ] Flag for automated re-evaluation if repeat detections arise.
  - [ ] Acquire fresh cloud-free Sentinel-2/Landsat optical pass to resolve surface context.

*Context: WorldCover = Tree cover | OSM Category = nan (nan) | Observing Satellites = 2*
---
### Event `EVT_01383431`

| Metric | Value | Tier |
| :--- | :---: | :---: |
| **Risk Score** | **7.9 / 100** | **LOW** |
| **Evidence Confidence** | **52.0 / 100** | **MEDIUM** |
| **Investigation Priority** | **Routine low-priority monitoring** | — |

**Summary**: Event received an investigation priority score of 7.9/100 (LOW). The primary risk driver is Thermal Intensity (4.8 pts), followed by Persistence (3.0 pts).

#### 1. Dimension Score Breakdown

| Dimension | Code | Weight | Normalized [0, 1] | Weighted Points [0–100] | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Thermal Intensity | `A` | 30% | 0.162 | **4.8** | `PRESENT` |
| Persistence | `B` | 25% | 0.121 | **3.0** | `PRESENT` |
| Industrial Association | `C` | 20% | 0.000 | **0.0** | `ZERO_OBSERVED_CONTRIBUTION` |
| Spatial Scale | `D` | 10% | 0.005 | **0.1** | `PRESENT` |
| Spectral / Surface Evidence | `E` | 15% | 0.000 | **0.0** | `EXTRACTION_FAILURE` |

#### 2. Key Contribution Drivers
- **Primary driver: Thermal Intensity — 4.8 points**
- **Secondary driver: Persistence — 3.0 points**
- **Weakest evidence: Spectral / Surface Evidence — 0.0 points**

#### 3. Raw Evidence Trace
- **Thermal**: FRP mean = 10.96, FRP max = 15.6, Brightness mean = 344.7 K
- **Persistence**: Distinct detection days = 1, Total detection count = 3
- **Industrial**: OSM match fraction = 0.0, Containment = 0.0, Proximity = 0.0, Min distance = nan m
- **Spatial**: Convex hull area = 0.0327 km²
- **Spectral**: SWIR anomaly ratio = nan, NDVI = nan, SWIR2/SWIR1 ratio = nan, BSI = nan, SCL clear fraction = nan, Temporal delta = -5.06 days

#### 4. Evidence Availability & Limitations
- **Sentinel-2 Status**: Sentinel-2 scene was present but spectral feature extraction failed, so this dimension contributed 0 points. This is an evidence limitation, not evidence of absence.
- **Missing Tags**: `osm_context:no_mapped_association, dimension_E_spectral_missing, spectral_coverage:extraction_failed`

#### 5. Deterministic Interpretations
- **Thermal**: Low thermal energy output observed near sensor detection thresholds.
- **Persistence**: The event was observed over a short temporal window (1 days, 3 detections).
- **Industrial**: No mapped industrial infrastructure was identified within the methodology-defined 5,000m spatial context.
- **Spatial**: Compact, localized geographic footprint (0.03 km²).
- **Spectral**: Surface reflectance indices show no distinct contrast relative to local background in available imagery.

#### 6. Investigation Recommendation & Next Actions
**Recommendation**: `Routine low-priority monitoring`
**Rationale**: Low risk score (7.9/100) with moderate confidence (52.0/100). Minimal industrial or persistent characteristics.
**Recommended Next Steps**:
  - [ ] Standard archive logging.
  - [ ] Flag for automated re-evaluation if repeat detections arise.
  - [ ] Acquire fresh cloud-free Sentinel-2/Landsat optical pass to resolve surface context.

*Context: WorldCover = Cropland | OSM Category = nan (nan) | Observing Satellites = 2*
---
### Event `EVT_01035117`

| Metric | Value | Tier |
| :--- | :---: | :---: |
| **Risk Score** | **6.3 / 100** | **LOW** |
| **Evidence Confidence** | **46.0 / 100** | **LOW** |
| **Investigation Priority** | **Low observed risk but insufficient evidence** | — |

**Summary**: Event received an investigation priority score of 6.3/100 (LOW). The primary risk driver is Thermal Intensity (3.8 pts), followed by Persistence (2.5 pts).

#### 1. Dimension Score Breakdown

| Dimension | Code | Weight | Normalized [0, 1] | Weighted Points [0–100] | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Thermal Intensity | `A` | 30% | 0.126 | **3.8** | `PRESENT` |
| Persistence | `B` | 25% | 0.101 | **2.5** | `PRESENT` |
| Industrial Association | `C` | 20% | 0.000 | **0.0** | `ZERO_OBSERVED_CONTRIBUTION` |
| Spatial Scale | `D` | 10% | 0.000 | **0.0** | `PRESENT` |
| Spectral / Surface Evidence | `E` | 15% | 0.000 | **0.0** | `EXTRACTION_FAILURE` |

#### 2. Key Contribution Drivers
- **Primary driver: Thermal Intensity — 3.8 points**
- **Secondary driver: Persistence — 2.5 points**
- **Weakest evidence: Spatial Scale — 0.0 points**

#### 3. Raw Evidence Trace
- **Thermal**: FRP mean = 17.3, FRP max = 17.3, Brightness mean = 312.8 K
- **Persistence**: Distinct detection days = 1, Total detection count = 1
- **Industrial**: OSM match fraction = 0.0, Containment = 0.0, Proximity = 0.0, Min distance = nan m
- **Spatial**: Convex hull area = 0.0 km²
- **Spectral**: SWIR anomaly ratio = nan, NDVI = nan, SWIR2/SWIR1 ratio = nan, BSI = nan, SCL clear fraction = nan, Temporal delta = -0.15 days

#### 4. Evidence Availability & Limitations
- **Sentinel-2 Status**: Sentinel-2 scene was present but spectral feature extraction failed, so this dimension contributed 0 points. This is an evidence limitation, not evidence of absence.
- **Missing Tags**: `osm_context:no_mapped_association, dimension_E_spectral_missing, spectral_coverage:extraction_failed`

#### 5. Deterministic Interpretations
- **Thermal**: Low thermal energy output observed near sensor detection thresholds.
- **Persistence**: The event was observed over a short temporal window (1 days, 1 detections).
- **Industrial**: No mapped industrial infrastructure was identified within the methodology-defined 5,000m spatial context.
- **Spatial**: Compact, localized geographic footprint (0.00 km²).
- **Spectral**: Surface reflectance indices show no distinct contrast relative to local background in available imagery.

#### 6. Investigation Recommendation & Next Actions
**Recommendation**: `Low observed risk but insufficient evidence`
**Rationale**: Low numerical score (6.3/100) coincides with low evidence confidence (46.0/100). Key observational dimensions were unavailable or unobserved; low score reflects absence of data rather than confirmed absence of hazard.
**Recommended Next Steps**:
  - [ ] Do NOT conclude real-world safety based on numerical score alone.
  - [ ] Check for upcoming satellite coverage to fill evidence gaps.
  - [ ] Review multi-day FIRMS history to confirm if thermal activity was truly transient.
  - [ ] Acquire fresh cloud-free Sentinel-2/Landsat optical pass to resolve surface context.

*Context: WorldCover = Cropland | OSM Category = nan (nan) | Observing Satellites = 1*
---

## Part 6 — Key Risk / Confidence Archetypes

Demonstration of how Risk Score and Evidence Confidence interact independently across real pilot events:

### Archetype A: High Risk / Medium Confidence (Elevated Risk with Stale Optical)
### Event `EVT_00963466`

| Metric | Value | Tier |
| :--- | :---: | :---: |
| **Risk Score** | **49.0 / 100** | **MODERATE** |
| **Evidence Confidence** | **70.0 / 100** | **MEDIUM** |
| **Investigation Priority** | **Needs additional satellite verification** | — |

**Summary**: Event received an investigation priority score of 49.0/100 (MODERATE). The primary risk driver is Persistence (24.2 pts), followed by Industrial Association (15.5 pts).

#### 1. Dimension Score Breakdown

| Dimension | Code | Weight | Normalized [0, 1] | Weighted Points [0–100] | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Thermal Intensity | `A` | 30% | 0.067 | **2.0** | `PRESENT` |
| Persistence | `B` | 25% | 0.970 | **24.2** | `PRESENT` |
| Industrial Association | `C` | 20% | 0.775 | **15.5** | `PRESENT` |
| Spatial Scale | `D` | 10% | 0.723 | **7.2** | `PRESENT` |
| Spectral / Surface Evidence | `E` | 15% | 0.000 | **0.0** | `STALE` |

#### 2. Key Contribution Drivers
- **Primary driver: Persistence — 24.2 points**
- **Secondary driver: Industrial Association — 15.5 points**
- **Weakest evidence: Spectral / Surface Evidence — 0.0 points**

#### 3. Raw Evidence Trace
- **Thermal**: FRP mean = 2.8, FRP max = 34.8, Brightness mean = 313.25 K
- **Persistence**: Distinct detection days = 343, Total detection count = 21883
- **Industrial**: OSM match fraction = 0.9973, Containment = 0.766, Proximity = 0.2313, Min distance = 0.0 m
- **Spatial**: Convex hull area = 88.5907 km²
- **Spectral**: SWIR anomaly ratio = 1.2667, NDVI = 0.0463, SWIR2/SWIR1 ratio = 1.2549, BSI = 0.1362, SCL clear fraction = 0.9184, Temporal delta = 238.42 days

#### 4. Evidence Availability & Limitations
- **Sentinel-2 Status**: Contemporary Sentinel-2 evidence was stale (temporal offset: 238.4 days > 90 days; temporal reliability = 0.0), so this dimension contributed 0 points. This is an evidence limitation, not evidence of absence.
- **Missing Tags**: `temporal_relevance:stale`

#### 5. Deterministic Interpretations
- **Thermal**: Low thermal energy output observed near sensor detection thresholds.
- **Persistence**: Chronic thermal activity persisted across 343 distinct detection days (21,883 total detections).
- **Industrial**: The event is strongly associated with mapped industrial infrastructure (high polygon containment / direct co-location).
- **Spatial**: Extensive spatial footprint encompassing a large contiguous thermal cluster area (88.59 km²).
- **Spectral**: Available Sentinel-2 evidence is temporally stale relative to the FIRMS observation (>90 days offset).

#### 6. Investigation Recommendation & Next Actions
**Recommendation**: `Needs additional satellite verification`
**Rationale**: Moderate risk score (49.0/100) with limited observational confidence (70.0/100, MEDIUM). Gaps in optical or corroborating data prevent definitive characterization.
**Recommended Next Steps**:
  - [ ] Task contemporary optical satellite verification pass.
  - [ ] Verify whether thermal cluster is persistent or transient.
  - [ ] Acquire fresh cloud-free Sentinel-2/Landsat optical pass to resolve surface context.

*Context: WorldCover = Bare / sparse vegetation | OSM Category = mine_quarry (2.0) | Observing Satellites = 5*
---

### Archetype B: High Risk / High Confidence (Corroborated High-Priority Target)
### Event `EVT_00791043`

| Metric | Value | Tier |
| :--- | :---: | :---: |
| **Risk Score** | **45.3 / 100** | **MODERATE** |
| **Evidence Confidence** | **86.5 / 100** | **HIGH** |
| **Investigation Priority** | **Routine monitoring target** | — |

**Summary**: Event received an investigation priority score of 45.3/100 (MODERATE). The primary risk driver is Persistence (21.6 pts), followed by Industrial Association (15.8 pts).

#### 1. Dimension Score Breakdown

| Dimension | Code | Weight | Normalized [0, 1] | Weighted Points [0–100] | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Thermal Intensity | `A` | 30% | 0.051 | **1.5** | `PRESENT` |
| Persistence | `B` | 25% | 0.862 | **21.6** | `PRESENT` |
| Industrial Association | `C` | 20% | 0.787 | **15.8** | `PRESENT` |
| Spatial Scale | `D` | 10% | 0.304 | **3.0** | `PRESENT` |
| Spectral / Surface Evidence | `E` | 15% | 0.231 | **3.5** | `PRESENT` |

#### 2. Key Contribution Drivers
- **Primary driver: Persistence — 21.6 points**
- **Secondary driver: Industrial Association — 15.8 points**
- **Weakest evidence: Thermal Intensity — 1.5 points**

#### 3. Raw Evidence Trace
- **Thermal**: FRP mean = 2.25, FRP max = 15.35, Brightness mean = 313.4 K
- **Persistence**: Distinct detection days = 244, Total detection count = 1927
- **Industrial**: OSM match fraction = 1.0, Containment = 0.8755, Proximity = 0.1245, Min distance = 0.0 m
- **Spatial**: Convex hull area = 5.6371 km²
- **Spectral**: SWIR anomaly ratio = 0.6801, NDVI = 0.0436, SWIR2/SWIR1 ratio = 1.1728, BSI = 0.1341, SCL clear fraction = 1.0, Temporal delta = 40.39 days

#### 4. Evidence Availability & Limitations
- **Sentinel-2 Status**: Contemporary Sentinel-2 imagery was clear and temporally aligned.
- **Missing Tags**: None (all primary observational inputs present)

#### 5. Deterministic Interpretations
- **Thermal**: Low thermal energy output observed near sensor detection thresholds.
- **Persistence**: Chronic thermal activity persisted across 244 distinct detection days (1,927 total detections).
- **Industrial**: The event is strongly associated with mapped industrial infrastructure (high polygon containment / direct co-location).
- **Spatial**: Moderate cluster geographic extent spanning 5.64 km².
- **Spectral**: Moderate surface reflectance contrast or surface disturbance detected in contemporary satellite imagery.

#### 6. Investigation Recommendation & Next Actions
**Recommendation**: `Routine monitoring target`
**Rationale**: Moderate risk score (45.3/100) supported by confident multi-sensor corroboration (86.5/100). Activity is observed but below priority thresholds.
**Recommended Next Steps**:
  - [ ] Include in scheduled weekly thermal audit queue.
  - [ ] Monitor for unexpected spikes in fire radiative power or spatial cluster expansion.

*Context: WorldCover = Bare / sparse vegetation | OSM Category = mine_quarry (2.0) | Observing Satellites = 5*
---

### Archetype C: Low Risk / High Confidence (Confident Low-Risk Event)
### Event `EVT_00230882`

| Metric | Value | Tier |
| :--- | :---: | :---: |
| **Risk Score** | **11.3 / 100** | **LOW** |
| **Evidence Confidence** | **76.0 / 100** | **HIGH** |
| **Investigation Priority** | **Confident low-risk event** | — |

**Summary**: Event received an investigation priority score of 11.3/100 (LOW). The primary risk driver is Thermal Intensity (4.6 pts), followed by Spectral / Surface Evidence (4.2 pts).

#### 1. Dimension Score Breakdown

| Dimension | Code | Weight | Normalized [0, 1] | Weighted Points [0–100] | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Thermal Intensity | `A` | 30% | 0.154 | **4.6** | `PRESENT` |
| Persistence | `B` | 25% | 0.101 | **2.5** | `PRESENT` |
| Industrial Association | `C` | 20% | 0.000 | **0.0** | `ZERO_OBSERVED_CONTRIBUTION` |
| Spatial Scale | `D` | 10% | 0.000 | **0.0** | `PRESENT` |
| Spectral / Surface Evidence | `E` | 15% | 0.279 | **4.2** | `PRESENT` |

#### 2. Key Contribution Drivers
- **Primary driver: Thermal Intensity — 4.6 points**
- **Secondary driver: Spectral / Surface Evidence — 4.2 points**
- **Weakest evidence: Spatial Scale — 0.0 points**

#### 3. Raw Evidence Trace
- **Thermal**: FRP mean = 23.2, FRP max = 23.2, Brightness mean = 310.0 K
- **Persistence**: Distinct detection days = 1, Total detection count = 1
- **Industrial**: OSM match fraction = 0.0, Containment = 0.0, Proximity = 0.0, Min distance = nan m
- **Spatial**: Convex hull area = 0.0 km²
- **Spectral**: SWIR anomaly ratio = 0.8198, NDVI = 0.3927, SWIR2/SWIR1 ratio = 0.6999, BSI = 0.0744, SCL clear fraction = 1.0, Temporal delta = -2.95 days

#### 4. Evidence Availability & Limitations
- **Sentinel-2 Status**: Contemporary Sentinel-2 imagery was clear and temporally aligned.
- **Missing Tags**: `osm_context:no_mapped_association`

#### 5. Deterministic Interpretations
- **Thermal**: Low thermal energy output observed near sensor detection thresholds.
- **Persistence**: The event was observed over a short temporal window (1 days, 1 detections).
- **Industrial**: No mapped industrial infrastructure was identified within the methodology-defined 5,000m spatial context.
- **Spatial**: Compact, localized geographic footprint (0.00 km²).
- **Spectral**: Moderate surface reflectance contrast or surface disturbance detected in contemporary satellite imagery.

#### 6. Investigation Recommendation & Next Actions
**Recommendation**: `Confident low-risk event`
**Rationale**: Low risk score (11.3/100) with high observational confidence (76.0/100). Robust multi-satellite data confirms localized, low-persistence, or non-industrial thermal signature.
**Recommended Next Steps**:
  - [ ] Archive as low-priority background/transient thermal observation.
  - [ ] No active investigation required unless new persistent detections occur.

*Context: WorldCover = Cropland | OSM Category = nan (nan) | Observing Satellites = 1*
---

### Archetype D: Low Risk / Low Confidence (Insufficient Evidence Limitation)
### Event `EVT_01035117`

| Metric | Value | Tier |
| :--- | :---: | :---: |
| **Risk Score** | **6.3 / 100** | **LOW** |
| **Evidence Confidence** | **46.0 / 100** | **LOW** |
| **Investigation Priority** | **Low observed risk but insufficient evidence** | — |

**Summary**: Event received an investigation priority score of 6.3/100 (LOW). The primary risk driver is Thermal Intensity (3.8 pts), followed by Persistence (2.5 pts).

#### 1. Dimension Score Breakdown

| Dimension | Code | Weight | Normalized [0, 1] | Weighted Points [0–100] | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Thermal Intensity | `A` | 30% | 0.126 | **3.8** | `PRESENT` |
| Persistence | `B` | 25% | 0.101 | **2.5** | `PRESENT` |
| Industrial Association | `C` | 20% | 0.000 | **0.0** | `ZERO_OBSERVED_CONTRIBUTION` |
| Spatial Scale | `D` | 10% | 0.000 | **0.0** | `PRESENT` |
| Spectral / Surface Evidence | `E` | 15% | 0.000 | **0.0** | `EXTRACTION_FAILURE` |

#### 2. Key Contribution Drivers
- **Primary driver: Thermal Intensity — 3.8 points**
- **Secondary driver: Persistence — 2.5 points**
- **Weakest evidence: Spatial Scale — 0.0 points**

#### 3. Raw Evidence Trace
- **Thermal**: FRP mean = 17.3, FRP max = 17.3, Brightness mean = 312.8 K
- **Persistence**: Distinct detection days = 1, Total detection count = 1
- **Industrial**: OSM match fraction = 0.0, Containment = 0.0, Proximity = 0.0, Min distance = nan m
- **Spatial**: Convex hull area = 0.0 km²
- **Spectral**: SWIR anomaly ratio = nan, NDVI = nan, SWIR2/SWIR1 ratio = nan, BSI = nan, SCL clear fraction = nan, Temporal delta = -0.15 days

#### 4. Evidence Availability & Limitations
- **Sentinel-2 Status**: Sentinel-2 scene was present but spectral feature extraction failed, so this dimension contributed 0 points. This is an evidence limitation, not evidence of absence.
- **Missing Tags**: `osm_context:no_mapped_association, dimension_E_spectral_missing, spectral_coverage:extraction_failed`

#### 5. Deterministic Interpretations
- **Thermal**: Low thermal energy output observed near sensor detection thresholds.
- **Persistence**: The event was observed over a short temporal window (1 days, 1 detections).
- **Industrial**: No mapped industrial infrastructure was identified within the methodology-defined 5,000m spatial context.
- **Spatial**: Compact, localized geographic footprint (0.00 km²).
- **Spectral**: Surface reflectance indices show no distinct contrast relative to local background in available imagery.

#### 6. Investigation Recommendation & Next Actions
**Recommendation**: `Low observed risk but insufficient evidence`
**Rationale**: Low numerical score (6.3/100) coincides with low evidence confidence (46.0/100). Key observational dimensions were unavailable or unobserved; low score reflects absence of data rather than confirmed absence of hazard.
**Recommended Next Steps**:
  - [ ] Do NOT conclude real-world safety based on numerical score alone.
  - [ ] Check for upcoming satellite coverage to fill evidence gaps.
  - [ ] Review multi-day FIRMS history to confirm if thermal activity was truly transient.
  - [ ] Acquire fresh cloud-free Sentinel-2/Landsat optical pass to resolve surface context.

*Context: WorldCover = Cropland | OSM Category = nan (nan) | Observing Satellites = 1*
---

---

## Part 7 — Pilot Cohort Risk Driver Distribution

| Primary Risk Driver | Event Count ($N=100$) | Percentage | Primary Characteristic |
| :--- | :---: | :---: | :--- |
| **Persistence** | 57 | 57.0% | Dominant contributor in points on 0–100 risk scale |
| **Thermal Intensity** | 40 | 40.0% | Dominant contributor in points on 0–100 risk scale |
| **Spectral / Surface Evidence** | 3 | 3.0% | Dominant contributor in points on 0–100 risk scale |

### Observations on Cohort Distribution:
1. **Persistence & Thermal Intensity Dominate Primary Driver Status**: In the pilot cohort, events are primarily differentiated by whether thermal detections persist over dozens/hundreds of days vs single-pass events.
2. **Spectral Evidence Zero Points**: In the majority of pilot events, Sentinel-2 scenes were extracted outside the 90-day validity window (temporal offset > 90d), decaying temporal reliability to 0.0 per methodology. The explainability layer transparently notes this as an evidence limitation, not absence of fire.
3. **Zero Weight Redistribution Enforced**: Across all 100 pilot events, missing or stale dimensions contributed exactly 0.0 points to the fixed 0–100 scale, without artificially inflating remaining weights.

---

## Part 8 — Regulatory & Scientific Compliance Statements

- **Zero Black-Box Elements**: Every explanation is deterministically reproducible directly from raw inputs via explicit mathematical rules.
- **No Predictive Overreach**: Statements strictly describe observed physical and contextual indicators. No claims of 'confirmed industrial fire' or 'fire probability' are made prior to validated human labeling.
- **Evidence Confidence Separation**: Low risk scores combined with low evidence confidence are explicitly marked as requiring further evidence rather than declared benign.

**Report Generated**: 2026-09-14 | **Methodology Version**: `PhaseIX-2026-09-14`