# ThermoGuard — Proof & Evidence of Completed Work

**Audience**: SIH 2026 Evaluators, Technical Reviewers, and Hackathon Judges
**Repository**: `c:\AWS Hackathon\Bharat-Builds-Tour`
**Methodology Baseline**: `docs/PhaseIX_RISK_METHODOLOGY.md` (`PhaseIX-2026-09-14`)
**Scope**: Completed Work Only (Phases I–IX, Tasks 25–29)
**Document Generation Date**: 2026-09-14

---

## 1. Executive Evidence Summary

ThermoGuard currently implements a **deterministic, evidence-weighted thermal-anomaly investigation pipeline** that converts satellite-observed thermal detections into spatio-temporal events, enriches them with geospatial and optical/spectral evidence, calculates an investigation-priority risk score, independently quantifies evidence confidence, and produces traceable explanations.

### Defensible Operational Positioning:
- **Current System Role**: **Decision Support & Investigation Prioritization**.
- **What It Does**: Aggregates multi-sensor thermal observations, temporal persistence, OpenStreetMap industrial proximity, spatial scale, and Sentinel-2 surface reflectance contrast into an auditable, rank-ordered investigation queue.
- **What It Does NOT Do**: It is **NOT** yet a validated operational industrial-fire classifier. It does not predict class probabilities, confirm active industrial structural fires, or evaluate false-positive/false-negative rates against ground truth.

---

## 2. Completed Technical Pipeline

The implemented, end-to-end reproducible pipeline consists exclusively of completed and validated components:

```text
       NASA FIRMS Thermal Hotspot Archive (5.19M Detections)
                               │
                               ▼
        Spatio-Temporal Event Clustering (550m Grid, STRtree)
                               │
                               ▼
           Persistence Analysis (Days & Count Log-Scales)
                               │
                               ▼
   Industrial Geospatial Association (OSM Polygon Containment & Proximity)
                               │
                               ▼
  Sentinel-2 Spectral / Surface Evidence (AWS Element84 STAC COG Indices)
                               │
                               ▼
 ┌─────────────────────────────┴─────────────────────────────┐
 │                                                           │
 ▼                                                           ▼
Independent Evidence Confidence [0, 100]        Deterministic Risk Score [0, 100]
(Observational Quality & Corroboration)         (5-Dimension Additive Formulation)
 │                                                           │
 └─────────────────────────────┬─────────────────────────────┘
                               ▼
             Explainability & Driver Ranking (Task 28)
           (Primary / Secondary Drivers, Raw Trace, Limitations)
                               │
                               ▼
      Standardized Investigation Recommendation (Decision Support)
```

---

## 3. Phase IX Methodology

The active risk engine implements the frozen methodology specified in `docs/PhaseIX_RISK_METHODOLOGY.md` (`Methodology Version: PhaseIX-2026-09-14`).

### Mathematical Formulation:
$$\text{Risk Score} = 100 \times \left[ 0.30 \cdot D_A + 0.25 \cdot D_B + 0.20 \cdot D_C + 0.10 \cdot D_D + 0.15 \cdot D_E \right]$$

### Risk Dimensions & Exact Weights:
1. **Dimension A — Thermal Intensity (30%)**:
   - FRP mean ($50\%$, anchor 100 MW) $+$ FRP max ($35\%$, anchor 500 MW) $+$ Brightness temperature ($15\%$, linear [300 K, 370 K]).
2. **Dimension B — Persistence (25%)**:
   - Distinct detection days ($70\%$, anchor 365 days) $+$ Detection count ($30\%$, anchor 50,000 detections), log-normalized.
3. **Dimension C — Industrial Association (20%)**:
   - OSM matched fraction ($35\%$) $+$ Containment fraction ($30\%$) $+$ Proximity fraction ($20\%$) $+$ Linear distance decay ($15\%$, 0 to 5,000 m).
4. **Dimension D — Spatial Scale (10%)**:
   - Convex hull cluster area, log-normalized ($100\%$, anchor 500 km²).
5. **Dimension E — Spectral / Surface Evidence (15%)**:
   - Linear combination of SWIR2 anomaly ratio ($45\%$), NDVI disturbance ($25\%$), SWIR2/SWIR1 ratio ($20\%$), and BSI ($10\%$), modulated by cloud clarity ($SCL_{\text{clear}}$) and exponential temporal decay ($e^{-\lambda \cdot \Delta t}$, reaching 0.0 at $>90$ days).

### Strict Decoupling of Evidence Confidence:
- **Evidence Confidence** is an independent $0\text{--}100$ metric measuring observational quality, cloud cover, temporal lag, and sensor corroboration (`distinct_satellites`).
- **Evidence Confidence is NOT**:
  - A multiplier on risk,
  - A ceiling on risk,
  - A replacement for risk,
  - A probability of fire.
- High Risk + High Confidence = Verified active evidence.
- Low Risk + Low Confidence = Insufficient data, **NOT** evidence of safety.

---

## 4. Pilot Evidence ($N = 100$ Events)

The risk engine was executed across the frozen pilot cohort (`data/satellite/processed/firms_satellite_enriched_pilot.parquet`). Exact statistics from `reports/pilot_risk_summary.json` and `reports/task26_observational_summary.json`:

### Cohort Statistical Distribution:
| Metric | Value |
| :--- | :---: |
| **Total Pilot Events ($N$)** | 100 |
| **Successfully Scored Events** | 100 ($100.0\%$) |
| **Execution Failures** | 0 ($0.0\%$) |
| **Minimum Risk Score** | 6.3 / 100 |
| **Maximum Risk Score** | 49.0 / 100 |
| **Mean Risk Score** | 26.63 / 100 |
| **Median Risk Score (p50)** | 18.35 / 100 |
| **Standard Deviation** | 14.20 |
| **10th Percentile (p10)** | 12.40 |
| **25th Percentile (p25)** | 13.98 |
| **75th Percentile (p75)** | 42.82 |
| **90th Percentile (p90)** | 44.46 |

### Tier Breakdown:
- **Risk Tiers**:
  - `LOW` ($0.0 \le \text{Score} < 30.0$): **58 events** ($58.0\%$)
  - `MODERATE` ($30.0 \le \text{Score} < 60.0$): **42 events** ($42.0\%$)
  - `HIGH` ($60.0 \le \text{Score} < 85.0$): **0 events** ($0.0\%$)
  - `CRITICAL` ($85.0 \le \text{Score} \le 100.0$): **0 events** ($0.0\%$)
- **Evidence Confidence Tiers**:
  - `LOW` ($0.0 \le \text{Conf} < 50.0$): **2 events** ($2.0\%$)
  - `MEDIUM` ($50.0 \le \text{Conf} < 75.0$): **47 events** ($47.0\%$)
  - `HIGH` ($75.0 \le \text{Conf} \le 100.0$): **51 events** ($51.0\%$)

### Key Observational Findings:
- **Zero Industrial Match Events**: 60 events ($60.0\%$) had zero OSM industrial match within 5,000 m ($D_C = 0$).
- **Zero Spatial Area Events**: 19 events ($19.0\%$) consisted of single-detection points with $0.0\text{ km}^2$ convex hull area ($D_D = 0$).
- **Missing or Stale Spectral Events**: 47 events ($47.0\%$) received 0.0 spectral points ($D_E = 0$) due to absent scenes or temporal offset $>90$ days.

---

## 5. Representative Event — `EVT_00963466`

`EVT_00963466` is the highest-scoring event in the pilot cohort, representing an active, chronic open-pit coal quarry in Dhanbad, Jharkhand.

### Exact Record Data (from `reports/task28_explanations.json`):
- **Event ID**: `EVT_00963466`
- **Methodology Version**: `PhaseIX-2026-09-14`
- **Final Risk Score**: **49.0 / 100** (`MODERATE`)
- **Evidence Confidence**: **70.0 / 100** (`MEDIUM`)
- **Investigation Priority**: `Needs additional satellite verification`

### Dimension Score Breakdown:
| Dimension | Code | Weight | Normalized [0, 1] | Weighted Points [0–100] | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Thermal Intensity** | `A` | 30% | 0.0668 | **2.0 pts** | `PRESENT` |
| **Persistence** | `B` | 25% | 0.9697 | **24.2 pts** | `PRESENT` |
| **Industrial Association** | `C` | 20% | 0.7751 | **15.5 pts** | `PRESENT` |
| **Spatial Scale** | `D` | 10% | 0.7231 | **7.2 pts** | `PRESENT` |
| **Spectral / Surface Evidence** | `E` | 15% | 0.0000 | **0.0 pts** | `STALE` |
| **Total** | — | **100%** | — | **49.0 pts** | — |

### Contribution Ranking:
- **Primary Driver**: Persistence — 24.2 points (343 distinct days, 21,883 detections)
- **Secondary Driver**: Industrial Association — 15.5 points (99.7% matched inside OSM `mine_quarry` polygon)
- **Weakest Evidence**: Spectral / Surface Evidence — 0.0 points

### Raw Physical Evidence Trace:
- **Thermal**: FRP mean = 2.80 MW, FRP max = 34.80 MW, Brightness mean = 313.25 K
- **Persistence**: Distinct detection days = 343, Total detection count = 21,883
- **Industrial**: OSM match fraction = 0.9973, Containment = 0.7660, Proximity = 0.2313, Min distance = 0.0 m
- **Spatial**: Convex hull area = 88.59 km²
- **Spectral**: SWIR anomaly ratio = 1.2667, NDVI = 0.0463, Temporal delta = 238.42 days

### Evidence Limitation & Recommendation:
- **Sentinel-2 Statement**: *"Contemporary Sentinel-2 evidence was stale (temporal offset: 238.4 days > 90 days; temporal reliability = 0.0), so this dimension contributed 0 points. This is an evidence limitation, not evidence of absence."*
- **Investigation Action Checklist**:
  - [ ] Task contemporary optical satellite verification pass.
  - [ ] Verify whether thermal cluster is persistent or transient.
  - [ ] Acquire fresh cloud-free Sentinel-2/Landsat optical pass to resolve surface context.

---

## 6. Missing Evidence Demonstration

To prove that missing evidence is never misrepresented as safety or negative evidence, consider pilot event **`EVT_01557619`**:

### Exact Record Data:
- **Event ID**: `EVT_01557619`
- **Risk Score**: **11.2 / 100** (`LOW`)
- **Evidence Confidence**: **46.0 / 100** (`LOW`)
- **Missing Tags**: `osm_context:no_mapped_association`, `dimension_E_spectral_missing`, `spectral_coverage:extraction_failed`
- **Investigation Recommendation**: **`Low observed risk but insufficient evidence`**
- **Rationale**: *"Low numerical score (11.2/100) coincides with low evidence confidence (46.0/100). Key observational dimensions were unavailable or unobserved; low score reflects absence of data rather than confirmed absence of hazard."*
- **Sentinel-2 Explanation**: *"Sentinel-2 scene was present but spectral feature extraction failed, so this dimension contributed 0 points. This is an evidence limitation, not evidence of absence."*

### Key Principle Verified:
A low score caused by unobserved dimensions is explicitly flagged as **insufficient data**, preventing dangerous false-negative assumptions.

---

## 7. Explainability Evidence (Task 28)

Task 28 outputs complete, deterministic JSON records (`reports/task28_explanations.json`) conforming to the canonical schema:

```json
{
  "event_id": "string",
  "methodology_version": "PhaseIX-2026-09-14",
  "final_risk_score": 0.0,
  "risk_tier": "LOW | MODERATE | HIGH | CRITICAL",
  "evidence_confidence": 0.0,
  "confidence_tier": "LOW | MEDIUM | HIGH",
  "score_breakdown": { "thermal": {}, "persistence": {}, "industrial": {}, "spatial": {}, "spectral": {} },
  "contribution_ranking": { "primary_driver": {}, "secondary_driver": {}, "weakest_dimension": {} },
  "raw_evidence_trace": { "thermal": {}, "persistence": {}, "industrial": {}, "spatial": {}, "spectral": {} },
  "missing_and_stale_evidence": { "status_by_dimension": {}, "sentinel2_explanation": "" },
  "evidence_confidence_breakdown": { "separation_statement": "", "contributing_factors": {} },
  "analyst_interpretations": { "dimension_statements": {}, "overall_synthesis": "" },
  "investigation_priority": { "recommendation": "", "rationale": "", "recommended_next_actions": [] },
  "contextual_annotations": { "worldcover_class_name": "", "osm_primary_category": "", "osm_tier": "" },
  "traceability": { "formula": "", "sum_of_weights": 1.00 },
  "scientific_caveats": []
}
```

### Traceability Guarantee:
Every analyst recommendation is connected via an unbroken, deterministic chain:
$$\text{Raw Sensor Observation} \rightarrow \text{Normalized Sub-Dimensions} \rightarrow \text{Weighted Points} \rightarrow \text{Risk Tier} \rightarrow \text{Confidence} \rightarrow \text{Explanation} \rightarrow \text{Action Checklist}$$

---

## 8. Scientific Audit Evidence (Task 27)

Task 27 performed an exhaustive mathematical and algorithmic audit of the frozen risk engine:
- **Final Verdict**: **`TASK 27 — PASS`** (0 defects discovered).
- **Categories Tested & Passed**:
  1. *Formula & Weight Audit*: Exact sum to 1.000 (30% + 25% + 20% + 10% + 15%).
  2. *Monotonicity Testing*: Verified $\frac{\partial \text{Risk}}{\partial x} \ge 0$ across 16 parameter scans (0 violations).
  3. *Boundary Behavior*: Strictly clamped in $[0.0, 100.0]$ across zero, extreme saturation, and negative inputs.
  4. *Missing Evidence Behavior*: 0.0 points applied with zero weight redistribution.
  5. *Sensitivity Perturbation Analysis*: Smooth, proportional response to $\pm 10\%$ input variations (no cliff discontinuities).
  6. *Ranking Sanity*: Logical stratification from chronic quarries down to transient single-detection burns.
  7. *Risk vs. Confidence Independence*: Pearson correlation **$r = -0.225$**.
     > **Auditor Note**: This correlation confirms that Evidence Confidence does not mathematically drive or scale the Risk Score in the pilot cohort; it does not claim global statistical independence across all possible geographic domains.
  8. *Maximum-Risk Headroom Audit*: Proved that the observed max score of 49.0 is mathematically consistent with low thermal FRP and stale optical imagery.

---

## 9. Task 29 Compliance / Readiness Evidence

Task 29 conducted a formal hackathon compliance audit against SIH26162 and the AWS First Commit 2026 "Ship It" track:

| Evaluation Dimension | Exact Verdict | Implemented vs. Planned Status |
| :--- | :---: | :--- |
| **SIH26162 Alignment** | **`PARTIAL ALIGNMENT`** | Ingestion, clustering, persistence, OSM association, and satellite evidence are **IMPLEMENTED**. Supervised fire classification is **NOT IMPLEMENTED** (pending ground truth). |
| **Scientific Core Status** | **`PASS WITH LIMITATIONS`** | Core engine and explainability are **IMPLEMENTED & AUDITED**. Limitation: Produces an evidence-weighted prioritization index, not fire probability. |
| **AWS Ship It Status** | **`READY AFTER IMPLEMENTATION`** | Local Python engine is ready for Lambda. Cloud deployment is **NOT YET IMPLEMENTED** (0 AWS resources deployed). |
| **ML Classification Status**| **`NOT YET READY`** | Protocol defined. Validated ground-truth labels are **NOT YET IMPLEMENTED**. |

---

## 10. Validation Result (38 Tests Passing)

The entire test suite was executed against the repository:

### Test Execution Command:
```bash
python -m unittest discover tests
```

### Exact Terminal Output (Captured in `reports/validation_output.txt`):
```text
......................................
----------------------------------------------------------------------
Ran 38 tests in 0.199s

OK
```

### Test Breakdown:
- **`tests/test_risk_engine.py`**: 21 tests (Phase IX scoring, normalization anchors, edge cases, clamps)
- **`tests/test_scientific_audit.py`**: 5 tests (monotonicity, boundaries, missing evidence, zero-redistribution)
- **`tests/test_explainability.py`**: 12 tests (Task 28 ranking, points scale, limitation phrasing, confidence separation)

---

## 11. What This Evidence Proves

| Capability | Repository Evidence | Status |
| :--- | :--- | :---: |
| **Thermal Anomaly Ingestion** | 5.19M FIRMS detections processed in Phase I | **IMPLEMENTED** |
| **Spatio-Temporal Event Clustering** | `scripts/cluster_firms_events.py` (550m grid, STRtree) | **IMPLEMENTED** |
| **Temporal Persistence Analysis** | Dimension B log-normalized days & counts | **IMPLEMENTED** |
| **Industrial Geospatial Association** | Dimension C OSM containment & proximity | **IMPLEMENTED** |
| **Sentinel-2 Surface Extraction** | Dimension E SWIR/NDVI/BSI via STAC COGs | **IMPLEMENTED** |
| **Deterministic Risk Scoring** | `risk_engine/scoring.py` (5-dimension additive model) | **VALIDATED** |
| **Independent Evidence Confidence** | `risk_engine/confidence.py` ($r = -0.225$ with risk) | **VALIDATED** |
| **Explainability & Ranking** | `risk_engine/explanation.py` (canonical JSON & reports) | **VALIDATED** |
| **Missing/Stale Evidence Handling** | Zero redistribution + explicit limitation narratives | **VALIDATED** |
| **Industrial Fire Classification** | No validated ground-truth labels or trained model | **NOT IMPLEMENTED** |
| **AWS Cloud Deployment** | 0 AWS resources, 0 public URLs currently deployed | **NOT IMPLEMENTED** |

---

## 12. Scientific & Operational Limitations

To maintain strict scientific integrity, the following guardrails are permanent:
1. **Absence of Ground Truth**: The repository currently contains zero human-validated ground-truth labels for active industrial fires.
2. **No Classification Model**: The project does not currently possess a validated industrial-fire classification model.
3. **Prohibited Performance Claims**: No claims of classification accuracy, precision, recall, F1, ROC-AUC, or false-positive/negative rates are permitted.
4. **No Confirmation of Fire**: The system does not confirm that an event is an active industrial fire.
5. **Contextual Independence**: WorldCover and OSM categories are contextual evidence with 0% direct risk weight.
6. **Optical Missingness**: Missing Sentinel-2 imagery is strictly an evidence limitation, not evidence of absence.
7. **Score Integrity**: Risk thresholds are never artificially tuned to manufacture HIGH or CRITICAL events.
8. **Role Clarification**: The current system is strictly a **Decision Support & Investigation Prioritization** platform.
