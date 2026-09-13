# ThermoGuard – Satellite‑Based Industrial, Agricultural & Forest Event Detection

## Overview
ThermoGuard is an open‑source research project that combines **fire‑hotspot data (FIRMS)**, **OpenStreetMap (OSM)** context, and **Sentinel‑2 / Landsat** satellite imagery to identify and characterize thermal events across India.  The system is built as a series of **phases** that progressively enrich raw fire detections with increasingly sophisticated geospatial evidence.

---

## Problem Statement
Rapid, accurate detection of fire‑related events is critical for:
- Public‑health and air‑quality alerts,
- Disaster response and resource allocation,
- Environmental monitoring and emissions accounting.

Existing global fire products (e.g., FIRMS) provide point detections with limited contextual information.  By linking those detections to high‑resolution optical / NIR / SWIR bands and to OSM‑derived land‑use features, ThermoGuard aims to produce **event‑level evidence** that can be used by policymakers and researchers.

---

## Architecture & Pipeline (Phases I‑V)
| Phase | Description | Key Outputs |
|------|-------------|-------------|
| **I – FIRMS ingestion** | Load and filter FIRMS fire‑hotspot CSVs, persist as a Parquet table (`firms_raw.parquet`). | `firms_raw.parquet` |
| **II – WorldCover enrichment** | Join FIRMS points to the **ESA WorldCover** raster to obtain land‑cover class, and compute simple spatial statistics. | `firms_worldcover_enriched.parquet` |
| **III – OSM contextualisation** | Spatially join enriched points to OSM building / road / land‑use vectors, generating proximity, containment and category fractions. | `firms_osm_enriched.parquet` |
| **IV – Persistence & quality** | Store the fully‑joined table as `firms_persistent_events_worldcover.parquet`.  This is the *Phase IV* baseline dataset used for all downstream work. | `firms_persistent_events_worldcover.parquet` |
| **V – Sentinel‑2 / Landsat feature extraction (pilot)** | For a **stratified pilot of 100 events** (40 industrial, 30 agricultural, 30 forest) we query the **AWS Element84 STAC API**, download Sentinel‑2 Level‑2A COGs, and compute band means, spectral indices (NDVI, NBR, NBR2, BSI, SWIR‑ratio) and quality metrics (cloud cover, SCL fractions, temporal deltas). | `firms_satellite_enriched_pilot.parquet` (100 rows, 89 fully enriched) |

---

## Current Progress (as of 2026‑09‑13)
- **Phase I‑IV** fully implemented and validated on the full FIRMS → WorldCover → OSM pipeline.
- **Phase V pilot** completed:
  - 100 candidate events selected via `scripts/target_satellite_candidates.py`.
  - Satellite enrichment executed with `scripts/enrich_satellite_features.py`.
  - **89 events** contain all required spectral features.
  - **11 events** lack a clear Sentinel‑2 scene (cloud cover / missing data) and are excluded from feature‑based analysis.
- **Ground‑truth labels** are **not yet available**; supervised classification is therefore deferred.

---

## Roadmap
1. **Label acquisition** – manual expert annotation or linkage to verified fire incident registries.
2. **Supervised model development** – once labels exist, train and evaluate classifiers (ensuring `sampling_stratum` is never used as a target).
3. **Scale‑up** – expand from the 100‑event pilot to a country‑wide dataset (thousands of events).
4. **Integration** – expose results via a lightweight API / simple web dashboard.
5. **Publication** – release a DOI‑linked data package (large assets stored on public S3, referenced in the repository).

---

## Repository Layout
```
Bharat-Builds-Tour/
├─ .gitignore                 # ignores data, caches, secrets, IDE files
├─ README.md                  # this file
├─ docs/
│   ├─ PhaseI.md
│   ├─ PhaseII.md
│   ├─ PhaseIII.md
│   ├─ PhaseIV.md
│   └─ PhaseV.md
├─ scripts/
│   ├─ target_satellite_candidates.py
│   ├─ enrich_satellite_features.py
│   └─ ... (utility scripts)
├─ scratch/
│   ├─ baseline_feature_analysis.py   # reproducible feature‑analysis of the pilot
│   └─ baseline_feature_analysis_report.md
└─ data/ (git‑ignored)   # large Parquet, raster, and ancillary files
```
All **large datasets** (Parquet tables, COGs, raw FIRMS CSVs) are stored outside the repository and are referenced in the documentation with download instructions.

---

## Getting Started (Reproducing the Pilot)
1. Clone the repo.
2. Install the required Python environment (see `requirements.txt`).
3. Download the **Phase IV** Parquet dataset from the public S3 bucket (URL provided in the docs).
4. Run the pilot feature‑analysis script:
   ```bash
   python scratch/baseline_feature_analysis.py
   ```
   The script will load the pilot Parquet file, filter the 89 complete rows, and output a markdown report (`baseline_feature_analysis_report.md`).

---

## Data Provenance & Licensing
- **FIRMS** – NASA/NOAA open data, CC‑0.
- **ESA WorldCover** – ESA/ECMWF, CC‑BY‑4.0.
- **Sentinel‑2 L2A COGs** – Copernicus, CC‑BY‑4.0, accessed via the AWS Element84 STAC API.
- **OpenStreetMap** – ODbL.

All raw and processed **large files are intentionally excluded** from Git to keep the repository lightweight.  Instructions to obtain each dataset are described in the `docs/` folder.

---

## Acknowledgements
ThermoGuard is developed as part of the **AWS Hackathon** and builds on open‑source tools from the geospatial community (Rasterio, PyArrow, Pandas, GeoPandas, etc.).

---

*For any questions or contributions, please open an issue or submit a pull request.*
