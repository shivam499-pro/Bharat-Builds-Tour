# ThermoGuard Phase VIII — Leakage-Safe Data Split Strategy

This document specifies the scientific methodology used to partition the ThermoGuard 100-event pilot dataset (`thermoguard_ml_features_pilot.parquet`) into training, validation, and test subsets (`ml_train.parquet`, `ml_validation.parquet`, `ml_test.parquet`).

---

## 1. Principles of Leakage Prevention

In geospatial machine learning, standard random cross-validation or blind random splitting creates severe **spatial autocorrelation leakage**. Thermal events, local soil types, industrial clusters, and meteorological conditions are spatially correlated; a model evaluated on random splits will memorize regional land-cover characteristics rather than learning generalizable fire signatures.

To guarantee scientific validity, the Phase VIII splitting strategy enforces:
1. **Spatial Block Holdout**: Events are partitioned by geographic regional clusters with substantial physical buffer distances ($> 50\text{ km}$) separating splits.
2. **Zero Coordinate Overlap**: No training and testing events share geographic coordinates or immediate spatial buffers.
3. **No Target Leakage**: Splitting is computed strictly on spatial coordinates (`centroid_lat`, `centroid_lon`) using a deterministic seed (`random_state=42`), without knowledge of the target label.
4. **Data Integrity**: Source datasets remain read-only and un-mutated.

---

## 2. Geographic Partitioning Scheme

Events are grouped into 5 macro-geographic spatial regions across India using deterministic spatial clustering:

| Partition | Regional Corridors | Region IDs | Event Count | % of Dataset | Bounding Envelope |
|---|---|---|---|---|---|
| **Training (`ml_train`)** | Central India (MP/Vidarbha), East/Central-East (Jharkhand, Odisha, AP), North/Northwest (Punjab, Haryana, Rajasthan) | Clusters 0, 1, 4 | **64** | 64.0% | Lat: $[17.4, 32.8]^\circ\text{N}$, Lon: $[74.2, 87.3]^\circ\text{E}$ |
| **Validation (`ml_val`)** | Southwest / Western Coastal (Maharashtra, Karnataka, Gujarat Coast) | Cluster 3 | **16** | 16.0% | Lat: $[12.4, 22.9]^\circ\text{N}$, Lon: $[69.7, 77.9]^\circ\text{E}$ |
| **Test (`ml_test`)** | Northeast / Far East (Assam, Meghalaya, Arunachal, Eastern Border) | Cluster 2 | **20** | 20.0% | Lat: $[22.5, 28.0]^\circ\text{N}$, Lon: $[90.8, 96.8]^\circ\text{E}$ |

---

## 3. Leakage & Overlap Audit

- **Minimum Pairwise Spatial Distance**:
  - `Train <-> Validation`: **74.15 km** (No spatial overlap)
  - `Train <-> Test`: **344.20 km** (No spatial overlap)
  - `Validation <-> Test`: **1,348.50 km** (No spatial overlap)
- **Temporal Profile**: All three splits span observations between 2023 and 2025, ensuring models are not trained solely on one season and tested on an unrelated calendar year.
- **Target Label Distribution**:
  - `ml_train.parquet`: 0 populated labels, 64 pending nulls
  - `ml_validation.parquet`: 0 populated labels, 16 pending nulls
  - `ml_test.parquet`: 0 populated labels, 20 pending nulls

---

## 4. Scientific Sample Size Limitation Statement

> **IMPORTANT SCIENTIFIC NOTICE**: The total pilot dataset consists of $N = 100$ events. While spatial block holdout successfully eliminates spatial autocorrelation leakage, a 20-event test partition provides limited statistical power across the 6 candidate classes (average $\approx 3.3$ events per class). This split is scientifically rigorous for pipeline integration and spatial holdout benchmarking; however, definitive model performance claims require expanding the labeled evaluation set beyond the pilot phase.
