# ThermoGuard – Satellite‑Based Industrial, Agricultural & Forest Event Detection

## Overview
ThermoGuard is an open‑source research project developed for the **Smart India Hackathon (SIH 2026)** problem statement **SIH26162** (*"AI-Based Detection and Classification of Industrial Fires and Persistent Thermal Sources Using NASA FIRMS, OSM & Satellite Data"*) and the **AWS Hackathon** (First Commit 2026 "Ship It" track). It combines **fire‑hotspot data (NASA FIRMS)**, **OpenStreetMap (OSM)** industrial infrastructure context, **ESA WorldCover** land-use baselines, and **Sentinel‑2 / Landsat** satellite imagery to identify, characterize, and prioritize thermal events across India. The system is built as a series of progressive phases that enrich raw thermal detections with geospatial, temporal, and spectral evidence.

---

## Problem Statement
Rapid, accurate detection and characterization of thermal events is critical for:
- Public‑health and air‑quality alerts,
- Industrial safety, disaster response, and regulatory resource allocation,
- Environmental monitoring and emissions accounting.

Existing global fire products (e.g., NASA FIRMS) provide point detections with limited contextual information. By linking those detections to high‑resolution optical / NIR / SWIR bands and to OSM‑derived land‑use features, ThermoGuard produces **event‑level evidence** that can be used by environmental analysts, regulatory investigators, and researchers.

---

## Architecture & Pipeline

### Ingestion & Feature Engineering (Phases I–V)
| Phase | Description | Key Outputs |
|------|-------------|-------------|
| **I – FIRMS ingestion** | Load and filter FIRMS fire‑hotspot CSVs, persist as a Parquet table (`firms_raw.parquet`). | `firms_raw.parquet` (5.19M detections) |
| **II – WorldCover enrichment** | Join FIRMS points to the **ESA WorldCover** raster to obtain land‑cover class, and compute simple spatial statistics. | `firms_worldcover_enriched.parquet` |
| **III – OSM contextualisation** | Spatially join enriched points to OSM building / road / land‑use vectors, generating proximity, containment and category fractions. | `firms_osm_enriched.parquet` |
| **IV – Persistence & quality** | Store the fully‑joined table as `firms_persistent_events_worldcover.parquet`. This is the *Phase IV* baseline dataset used for all downstream work. | `firms_persistent_events_worldcover.parquet` |
| **V – Sentinel‑2 feature extraction (pilot)** | For a **stratified pilot of 100 events** (40 industrial, 30 agricultural, 30 forest) query the **AWS Element84 STAC API**, access Sentinel‑2 Level‑2A COGs, and compute band means, spectral indices (NDVI, NBR, NBR2, BSI, SWIR‑ratio) and quality metrics (cloud cover, SCL fractions, temporal deltas). | `firms_satellite_enriched_pilot.parquet` (100 rows, 89 fully enriched) |

### Evidence Review, Baseline Modeling & Risk Methodology (Phases VI–IX)
| Phase | Description | Key Outputs |
|------|-------------|-------------|
| **VI – Evidence Review & Labeling Protocol** | Define formal human review protocol, evidence checklists, and ground-truth templates to prepare for eventual expert labeling. | `docs/PhaseVI_LABELING_PROTOCOL.md`, `PhaseVI_REVIEW_CHECKLIST.md` |
| **VII – Feature Specification** | Establish unified 54-column feature schema decoupling physical evidence from observational strata. | `docs/PhaseVII_FEATURE_SPEC.md`, `PhaseVII_FEATURE_DATASET_REPORT.md` |
| **VIII – Baseline ML & Split Strategy** | Leakage-safe spatial block splitting (Central, South, North, Northeast) and baseline classifier benchmarking on surrogate strata. | `docs/PhaseVIII_SPLIT_STRATEGY.md`, `PhaseVIII_BASELINE_RESULTS.md` |
| **IX – Deterministic Risk Methodology** | Formulate the locked 5-dimension evidence-weighted thermal-risk scoring engine and decoupled Evidence Confidence indicator. | `docs/PhaseIX_RISK_METHODOLOGY.md`, `PhaseIX_RISK_INPUT_AUDIT.md` |

---

## Current Progress (as of 2026‑09‑14)
- **Phases I–IV**: Completed and validated across the full 5,191,144 FIRMS detection archive.
- **Phase V Pilot**: Completed across the frozen $N=100$ pilot cohort (89 complete Sentinel-2 scenes, 11 scenes with missing/degraded optical coverage).
- **Phase VI**: Labeling protocols, evidence checklists, and ground-truth templates drafted and validated.
- **Phase VII**: 54-column feature specification and data validation reports completed.
- **Phase VIII**: Spatial-block splitting strategy and surrogate baseline models evaluated.
- **Phase IX & Task 25**: Deterministic risk engine implemented in `risk_engine/` and executed across the pilot cohort (`reports/pilot_risk_scores.parquet`).
- **Task 26**: Pilot observational analysis completed (`reports/Task26_PILOT_OBSERVATIONAL_ANALYSIS.md`).
- **Task 27**: Scientific audit completed: **`TASK 27 — PASS`** (0 defects across monotonicity, boundary stability, missing data, and sensitivity).
- **Task 28**: Deterministic explainability layer implemented: **`TASK 28 — PASS`** (canonical JSON traces, contribution rankings, limitation phrasing).
- **Task 29**: Comprehensive SIH26162 and AWS First Commit 2026 "Ship It" readiness audit completed: **`TASK 29 — PASS`**.

---

## Current Deterministic Thermal-Risk Engine (Phase IX)

The active risk engine implements the frozen methodology specified in `docs/PhaseIX_RISK_METHODOLOGY.md` (`Methodology Version: PhaseIX-2026-09-14`). It computes a transparent, deterministic **0–100 investigation-priority / risk score** based on five additive physical and contextual dimensions:

$$\text{Risk Score} = 100 \times \left[ 0.30 \cdot D_A + 0.25 \cdot D_B + 0.20 \cdot D_C + 0.10 \cdot D_D + 0.15 \cdot D_E \right]$$

### The Five Risk Dimensions:
1. **Dimension A — Thermal Intensity (30%)**:
   - $0.50 \times \text{FRP mean}$ (anchor 100 MW) $+ 0.35 \times \text{FRP max}$ (anchor 500 MW) $+ 0.15 \times \text{Brightness temperature}$ (linear [300 K, 370 K]).
2. **Dimension B — Persistence (25%)**:
   - $0.70 \times \frac{\ln(1 + \text{distinct\_detection\_days})}{\ln(1 + 365)} + 0.30 \times \frac{\ln(1 + \text{detection\_count})}{\ln(1 + 50000)}$.
3. **Dimension C — Industrial Association (20%)**:
   - $0.35 \times \text{OSM matched fraction} + 0.30 \times \text{containment fraction} + 0.20 \times \text{proximity fraction} + 0.15 \times \max(0, 1 - \frac{\text{min\_distance\_m}}{5000})$.
4. **Dimension D — Spatial Scale (10%)**:
   - $1.00 \times \frac{\ln(1 + \text{spatial\_extent\_km2})}{\ln(1 + 500)}$ based on convex hull area.
5. **Dimension E — Spectral / Surface Evidence (15%)**:
   - $\left[ 0.45 \cdot \text{SWIR}_2\text{ anomaly} + 0.25 \cdot \text{NDVI disturbance} + 0.20 \cdot \frac{\text{SWIR}_2}{\text{SWIR}_1} + 0.10 \cdot \text{BSI} \right] \times \text{spectral\_reliability}$.
   - `spectral_reliability = temporal_reliability × cloud_reliability`, matching `docs/PhaseIX_RISK_METHODOLOGY.md` Section 9.1 and `risk_engine/dimensions.py`.
   - Temporal reliability is **linear**: $1 - \Delta t/90$ for $0 < \Delta t < 90$, $0$ if $\Delta t \ge 90$ days (not exponential $e^{-\lambda \Delta t}$).
   - Cloud reliability: $1.0$ if $SCL_{\text{clear}} \ge 0.9$, $SCL_{\text{clear}}$ if $0.5 \le SCL_{\text{clear}} < 0.9$, else $0.0$.

**Contextual Metadata (0% Direct Risk Weight)**: ESA WorldCover land cover class and OSM facility category/tier (`mine_quarry`, `factory_works`, `brick_kiln`) are preserved strictly for contextual explanation and have **0% direct weight** in the numerical score.

---

## Evidence Confidence & Missing Data Handling

### Decoupled Evidence Confidence (0–100)
Evidence Confidence is computed as an **independent 0–100 observational quality indicator**. It reflects:
- Sentinel-2 cloud clarity ($SCL_{\text{clear}}$),
- Temporal freshness (temporal delta $\Delta t$ in days),
- Multi-satellite platform corroboration (`distinct_satellites`: `clip(n, 1, 5) / 5`; one platform = 0.20, five platforms = 1.00), as implemented in `risk_engine/confidence.py`,
- Feature extraction completeness.

> **Critical Invariant**: Evidence Confidence does **NOT** multiply, cap, boost, or alter the numerical Risk Score. High Risk + High Confidence indicates verified active evidence; Low Risk + Low Confidence indicates insufficient data, **NOT** safety.

### Missing & Stale Data Policy: Zero Weight Redistribution
When any dimension is missing or stale:
- Its numerical contribution drops strictly to **0.0 points** on the fixed 0–100 scale.
- The weights of remaining dimensions are **never redistributed or scaled up**.
- **Missing Sentinel-2 evidence is never treated as evidence of absence**:
  > *"Contemporary Sentinel-2 evidence was unavailable/stale, so this dimension contributed 0 points. This is an evidence limitation, not evidence of absence."*

---

## Task 28 Deterministic Explainability

Every scored event produces a transparent, machine-readable audit trace and an analyst-readable explanation ([`reports/task28_explanations.json`](reports/task28_explanations.json) and [`reports/Task28_EXPLAINABILITY_REPORT.md`](reports/Task28_EXPLAINABILITY_REPORT.md)). The explanation layer is 100% deterministic (no LLMs, ML, or generative text models) and exposes:

1. **Score Breakdown**: Dimension normalized scores $[0, 1]$ and explicit points on the $[0, 100]$ final risk scale.
2. **Contribution Ranking**: Explicit identification of Primary Driver, Secondary Driver, and Weakest Dimension.
3. **Raw Evidence Trace**: Only observed physical values (FRP, detection days, OSM distance, extent, SWIR anomaly) without fabrication.
4. **Missing / Stale Evidence Categorization**: Explicit categorization (`PRESENT`, `PARTIAL`, `MISSING`, `UNAVAILABLE`, `EXTRACTION_FAILURE`, `STALE`, `ZERO_OBSERVED_CONTRIBUTION`).
5. **Evidence Confidence Breakdown**: Clear separation statement and sensor corroboration factors.
6. **Analyst Interpretations**: Descriptive templates for each dimension and an overall synthesis.
7. **Standardized Investigation Recommendations**: Rule-based priority categories mapped to locked risk/confidence tiers:
   - *Priority investigation target*
   - *Priority target — needs corroborating verification*
   - *Routine monitoring target*
   - *Needs additional satellite verification*
   - *Confident low-risk event*
   - *Low observed risk but insufficient evidence*
8. **Traceability & Caveats**: Complete mathematical reproducibility and mandatory scientific disclaimers.

---

## Validation & Scientific Audit Status

- **Task 27 Scientific Audit**: **`TASK 27 — PASS`** ([`reports/Task27_SCIENTIFIC_AUDIT.md`](reports/Task27_SCIENTIFIC_AUDIT.md)).
  - Part A (Formulas & Weights): PASS
  - Part B (Monotonicity across 16 parameter scans): PASS (0 violations)
  - Part C (Boundary & Edge cases): PASS
  - Part D (Missing evidence & zero redistribution): PASS
  - Part E (Sensitivity analysis $\pm 10\%$): PASS (smooth response, no cliffs)
  - Part F (Ranking sanity): PASS
  - Part G (Independence check): PASS ($r = -0.225$)
  - Part H (Maximum risk score 49.0 investigation): PASS
- **Task 28 Explainability Audit**: **`TASK 28 — PASS`** (all 12 verification invariants confirmed in `tests/test_explainability.py`).
- **Current Test Suite**: **38 unit and regression tests passing** across `tests/` (`Ran 38 tests in 0.130s OK`).

---

## Pilot Cohort Observations ($N=100$)

Across the frozen pilot cohort (`data/satellite/processed/firms_satellite_enriched_pilot.parquet`):
- **Maximum Observed Risk Score**: **49.0 / 100** (`EVT_00963466`, chronic open-pit coal quarry in Dhanbad mining basin).
  - Persistence: $24.2 / 25.0$ pts (343 days, 21,883 detections).
  - Industrial Association: $15.5 / 20.0$ pts (99.7% matched inside OSM `mine_quarry` polygon).
  - Spatial Scale: $7.2 / 10.0$ pts ($88.59\text{ km}^2$ cluster).
  - Thermal Intensity: $2.0 / 30.0$ pts (mean FRP 2.8 MW vs 100 MW anchor).
  - Spectral Evidence: $0.0 / 15.0$ pts (Sentinel-2 scene acquired 238 days away; decayed to 0.0 reliability).
- **Cohort Score Distribution**:
  - Top Tier (Scores 45–49): Chronic multi-month mining and industrial complexes.
  - Middle Tier (Scores 18–35): Seasonal agricultural burns or rural industrial facilities with partial containment.
  - Bottom Tier (Scores 6–12): Single-day, single-detection rural brush burns with zero industrial association.

---

## Mandatory Scientific & Operational Limitations

To maintain strict scientific integrity and regulatory compliance, the following limitations are explicitly enforced:
1. **No Ground-Truth Labels Currently Exist**: The repository does not currently contain human-validated ground-truth labels for active industrial fires.
2. **No Supervised Industrial-Fire Classifier**: The system does **NOT** currently have a validated industrial-fire classification model.
3. **Prohibited Predictive Claims**:
   - Do **NOT** claim classification accuracy, precision, recall, F1-score, or ROC-AUC.
   - Do **NOT** claim false-positive or false-negative rates.
   - Do **NOT** claim the system predicts "fire probability" or confirms an active industrial fire.
4. **Safety Interpretation**: Low numerical risk does **NOT** mean absence of danger when Evidence Confidence is low.
5. **Operational Scope**: The current system is a **Decision Support & Investigation Prioritization** tool, not an automated operational dispatch or fire confirmation system.

---

## AWS First Commit 2026 "Ship It" Status & Architecture

### Current Deployment State (Task 29 Audit)
- **Current State**: The scientific, risk-scoring, and explainability cores are fully implemented and verified locally.
- **Not Yet Implemented**: AWS cloud resources, public REST API, live web frontend, and CI/CD pipelines are currently **NOT IMPLEMENTED** (zero AWS resources deployed).

### Proposed / Planned Cloud Architecture (Next Phase)
To satisfy the AWS First Commit 2026 "Ship It" track requirements, the following serverless architecture is recommended:
- **Frontend**: Single-Page Application (SPA) hosted on **AWS Amplify Hosting** (interactive map of India, event filter, sliding Task 28 explainability drawer).
- **API**: **Amazon API Gateway** (HTTP API routing `/api/events`, `/api/events/{id}`, `/api/score`).
- **Compute**: **AWS Lambda** (planned stateless Python 3.11 runtime executing `risk_engine` and Task 28 explainability; execution latency and resource utilization will be empirically benchmarked after AWS deployment).
- **Data Store**: **Amazon DynamoDB** (`ThermalTraceEvents` table planned for event and explanation retrieval; query latency and throughput will be empirically benchmarked after AWS deployment).
- **Object Storage**: **Amazon S3** (hosting Parquet tables, GeoJSON layers, and audit artifacts).
- **Event Bus**: **Amazon EventBridge** (periodic FIRMS ingestion triggers).
- **Analyst Assistant (Grounded)**: **Amazon Bedrock** (Claude 3.5 Sonnet synthesizing executive intelligence memos strictly from deterministic Task 28 JSON; **Bedrock never computes risk scores or modifies weights**).

---

## Project Roadmap

### Completed
- [x] **Phase I–IV**: Ingestion, WorldCover join, OSM spatial correlation, and spatio-temporal clustering across 5.19M FIRMS detections.
- [x] **Phase V**: Sentinel-2 STAC satellite feature extraction for the 100-event pilot.
- [x] **Phase VI**: Ground-truth review checklists and labeling protocols.
- [x] **Phase VII**: 54-column feature specification and dataset verification.
- [x] **Phase VIII**: Spatial-block splitting strategy and surrogate baseline modeling.
- [x] **Phase IX**: Locked 5-dimension deterministic risk methodology (`PhaseIX-2026-09-14`).
- [x] **Task 25**: Deterministic risk engine implementation and pilot scoring.
- [x] **Task 26**: Pilot observational analysis.
- [x] **Task 27**: Scientific audit of frozen risk engine (PASS, 0 defects).
- [x] **Task 28**: Deterministic explainability layer and canonical JSON audit records (PASS).
- [x] **Task 29**: SIH26162 and AWS Ship It readiness audit (PASS).

### Next (AWS Implementation & Submission Phase)
- [ ] **Task 30**: Modern interactive Single-Page Application frontend (React / MapLibre GL) with event inspector and Task 28 explanation drawer.
- [ ] **Task 31**: AWS Serverless Backend (AWS Lambda + Amazon API Gateway + Amazon DynamoDB).
- [ ] **Task 32**: AWS Amplify live public deployment.
- [ ] **Task 33**: Grounded Amazon Bedrock analyst briefing assistant.
- [ ] **Task 34**: End-to-end $\le 3$-minute live demonstration video.

### Future (Post-Hackathon Scientific Scale-Up)
- [ ] Multi-annotator human ground-truth labeling campaign per Phase VI protocol.
- [ ] Supervised industrial-fire vs. controlled persistent source classification.
- [ ] Empirical validation against verified ground-truth fire incident registries.

---

## Repository Layout
```
Bharat-Builds-Tour/
├─ .gitignore
├─ README.md                                    # This file
├─ requirements.txt                             # Python dependencies for the risk engine and tests
├─ repo_paths.py                                # Shared dataset path resolver
├─ analysis/
│   └─ baseline_feature_analysis.py             # Phase V pilot feature summary
├─ docs/
│   ├─ PhaseI.md                                # Phase I raw ingestion notes
│   ├─ PhaseV.md                                # Phase V satellite pilot documentation
│   ├─ PhaseVI_LABELING_PROTOCOL.md             # Ground truth review protocol & guidelines
│   ├─ PhaseVI_REVIEW_CHECKLIST.md              # Analyst labeling checklist
│   ├─ PhaseVI_REVIEW_WORKFLOW.md               # Labeling workflow specification
│   ├─ PhaseVI_EVIDENCE_REVIEW.md               # Pilot evidence review notes
│   ├─ PhaseVII_FEATURE_SPEC.md                 # 54-column feature specification
│   ├─ PhaseVII_FEATURE_DATASET_REPORT.md       # Feature dataset integrity report
│   ├─ PhaseVIII_SPLIT_STRATEGY.md              # Spatial block splitting documentation
│   ├─ PhaseVIII_BASELINE_RESULTS.md            # Baseline ML benchmarks on surrogate strata
│   ├─ PhaseVIII_INFERENCE.md                   # Inference specification
│   ├─ PhaseIX_RISK_METHODOLOGY.md              # Immutable locked Phase IX methodology
│   └─ PhaseIX_RISK_INPUT_AUDIT.md              # Risk engine input field audit
├─ risk_engine/                                 # Deterministic Risk & Explainability Core
│   ├─ __init__.py                              # Public package interface
│   ├─ normalization.py                         # Normalization anchors, ceilings & clamps
│   ├─ dimensions.py                            # Sub-dimension computation (A, B, C, D, E)
│   ├─ confidence.py                            # Decoupled Evidence Confidence engine
│   ├─ scoring.py                               # Additive 5-dimension risk scoring engine
│   ├─ explanation.py                           # Task 28 deterministic explainability layer
│   └─ validation.py                            # Pilot distribution validation metrics
├─ reports/                                     # Audit Reports & Scored Datasets
│   ├─ pilot_risk_scores.parquet                # Scored N=100 pilot events
│   ├─ pilot_risk_scores.csv                    # CSV export of pilot risk scores
│   ├─ task26_observational_summary.json        # Task 26 pilot statistics
│   ├─ Task26_PILOT_OBSERVATIONAL_ANALYSIS.md   # Task 26 observational report
│   ├─ task27_scientific_audit.json             # Task 27 audit records
│   ├─ Task27_SCIENTIFIC_AUDIT.md               # Task 27 scientific audit report
│   ├─ task28_explanations.json                 # Task 28 machine-readable JSON traces
│   ├─ Task28_EXPLAINABILITY_REPORT.md          # Task 28 analyst explainability report
│   ├─ task29_compliance_audit.json             # Task 29 compliance audit JSON
│   └─ Task29_SIH26162_AWS_SHIPIT_AUDIT.md      # Task 29 SIH26162 & AWS Ship It audit report
├─ scripts/                                     # Execution & Audit Scripts
│   ├─ run_risk_engine.py                       # Task 25 pilot execution script
│   ├─ task26_observational_analysis.py         # Task 26 analysis script
│   ├─ task27_scientific_audit.py               # Task 27 scientific audit script
│   ├─ task28_explainability.py                 # Task 28 explainability generator
│   ├─ build_ml_features.py                     # Feature matrix builder
│   ├─ create_ml_splits.py                      # Spatial-block split generator
│   ├─ train_baseline_models.py                 # Baseline ML training script
│   └─ create_ground_truth_template.py          # Ground-truth template generator
├─ tests/                                       # Automated Unit & Regression Tests (38 passing)
│   ├─ test_risk_engine.py                      # Task 25 engine unit tests (21 tests)
│   ├─ test_scientific_audit.py                 # Task 27 scientific audit tests (5 tests)
│   └─ test_explainability.py                   # Task 28 explainability tests (12 tests)
├─ models/                                      # Baseline Exploratory Artifacts
│   ├─ logistic_regression_baseline.joblib      # Surrogate stratum baseline model
│   └─ random_forest_baseline.joblib            # Surrogate stratum baseline model
└─ data/ (git-ignored)                          # Large Parquet, raster & satellite files
```

---

## Getting Started

### 1. Setup
```bash
git clone https://github.com/shivam499-pro/Bharat-Builds-Tour.git
cd Bharat-Builds-Tour
pip install -r requirements.txt
```

Large FIRMS / OSM / Sentinel parquet files are git-ignored. Place them under `data/satellite/processed/`, or set `THERMOGUARD_DATA_ROOT` to the directory that contains them.

If the Phase V pilot parquet is available:

```bash
python analysis/baseline_feature_analysis.py
```

### 2. Reproducing Risk Engine, Explainability & Scientific Audits
```bash
# Execute the deterministic Phase IX risk engine against the N=100 pilot
python scripts/run_risk_engine.py

# Execute the comprehensive scientific audit (Part A–I)
python scripts/task27_scientific_audit.py

# Generate Task 28 deterministic explainability traces and markdown reports
python scripts/task28_explainability.py

# Run the unit and regression tests
python -m unittest discover tests
```

### 3. AWS demo — DynamoDB seed (CloudShell)

Console table `ThermoGuardEvents` in `ap-south-1` (partition key `event_id`, String) is empty until this seed runs. CloudShell is already signed in:

```bash
export AWS_DEFAULT_REGION=ap-south-1
git clone https://github.com/shivam499-pro/Bharat-Builds-Tour.git
cd Bharat-Builds-Tour
python scripts/seed_dynamodb.py
```

Then DynamoDB → **Explore table items** → **Scan** → **Run**. Expect 100 items (example `EVT_00963466`, risk_score 49).

Read API code lives in `api/handler.py` (Lambda). Table definition for IaC is `infra/dynamodb.yaml`.

---

## Data Provenance & Licensing
- **NASA FIRMS** – NASA/NOAA open data, CC-0.
- **ESA WorldCover** – ESA/ECMWF, CC-BY-4.0.
- **Sentinel-2 L2A COGs** – Copernicus, CC-BY-4.0, accessed via the AWS Element84 STAC API.
- **OpenStreetMap** – OpenStreetMap Foundation, Open Database License (ODbL).

All raw and processed large datasets are stored outside Git to keep the repository lightweight. Instructions to reproduce datasets are provided in the `docs/` and `scripts/` directories.

---

## Acknowledgements
ThermoGuard is maintained by **Shivam** ([shivam499-pro](https://github.com/shivam499-pro)) for the **Smart India Hackathon (SIH 2026)** problem statement **SIH26162** and the **AWS Hackathon** (First Commit 2026). It builds on foundational open‑source geospatial libraries (Rasterio, Shapely, GeoPandas, PyArrow, Pandas, NumPy, Scikit-learn).

---

*For questions or technical inquiries regarding the Phase IX risk methodology or audit logs, please consult the audit reports in `reports/`.*
