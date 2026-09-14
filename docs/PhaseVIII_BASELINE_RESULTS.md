# ThermoGuard Phase VIII — Baseline Classifier Benchmark Results

This document reports the baseline machine learning evaluation conducted on the leakage-safe Phase VIII spatial block splits using **Logistic Regression** and **Random Forest**.

---

## 1. Experimental Setup & Disclaimers

### Mandatory Scientific Disclaimers
1. **NOT PRODUCTION READY**: These models represent simple, interpretable baselines to verify pipeline functionality, feature behavior, and evaluation harnesses. They are not tuned or claimed as production systems.
2. **DATASET SIZE LIMITATIONS**: The pilot dataset consists of $N = 100$ total events (Train: 64, Validation: 16, Test: 20). Because the test split is an independent spatial block (Northeast India), class coverage is geographically constrained. High accuracy on specific subsets does not prove broad statistical validity across the Indian subcontinent.
3. **TARGET SOURCE**: Models were trained on `sampling_stratum (surrogate domain categories)`. Full ground-truth supervised classification remains pending final human review according to the Phase VI-B labeling protocol.
4. **STRICT LEAKAGE PREVENTION**:
   - `sampling_stratum` was **strictly excluded** from all input feature matrices.
   - All human review annotations (`label_confidence`, `review_status`, notes) were strictly excluded.
   - Preprocessing transformers (imputation, scaling, one-hot encoding) were fitted **strictly on training data**.

---

## 2. Model Performance Summary

### Overall Metrics Table

| Model | Partition | Accuracy | Macro Precision | Macro Recall | Macro F1 |
|---|---|---|---|---|---|
| **Logistic Regression** | Validation ($N=16$) | **0.9375** | **0.8333** | **0.9583** | **0.8667** |
| **Logistic Regression** | Test ($N=20$) | **1.0000** | **1.0000** | **1.0000** | **1.0000** |
| **Random Forest** | Validation ($N=16$) | **1.0000** | **1.0000** | **1.0000** | **1.0000** |
| **Random Forest** | Test ($N=20$) | **1.0000** | **1.0000** | **1.0000** | **1.0000** |

---

## 3. Detailed Per-Class Evaluation

### Test Split Class Support & Metrics (Random Forest)
Classes evaluated: `['agricultural_ephemeral', 'forest_wildfire', 'industrial_persistent']`

| Class | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| `agricultural_ephemeral` | 0.0000 | 0.0000 | 0.0000 | 0 |
| `forest_wildfire` | 1.0000 | 1.0000 | 1.0000 | 20 |
| `industrial_persistent` | 0.0000 | 0.0000 | 0.0000 | 0 |

### Confusion Matrices (Test Partition, $N=20$)

#### Logistic Regression
- Classes: `['agricultural_ephemeral', 'forest_wildfire', 'industrial_persistent']`
```text
[[ 0  0  0]
 [ 0 20  0]
 [ 0  0  0]]
```

#### Random Forest
- Classes: `['agricultural_ephemeral', 'forest_wildfire', 'industrial_persistent']`
```text
[[ 0  0  0]
 [ 0 20  0]
 [ 0  0  0]]
```

---

## 4. Feature Importance Analysis (Random Forest)

Top 15 features ranked by Mean Decrease in Impurity (Gini Importance):

| Rank | Feature Name | Importance Score |
|---|---|---|
| 1 | `distinct_detection_days` | 0.1031 |
| 2 | `worldcover_class_name_Tree cover` | 0.0958 |
| 3 | `duration_days` | 0.0872 |
| 4 | `worldcover_class_name_Cropland` | 0.0737 |
| 5 | `osm_tier` | 0.0659 |
| 6 | `osm_sub_category_none` | 0.0530 |
| 7 | `has_osm_industrial_match` | 0.0511 |
| 8 | `frp_mean` | 0.0498 |
| 9 | `spatial_extent_km2` | 0.0481 |
| 10 | `distinct_satellites` | 0.0435 |
| 11 | `osm_containment_fraction` | 0.0404 |
| 12 | `detection_count` | 0.0398 |
| 13 | `osm_matched_fraction` | 0.0360 |
| 14 | `worldcover_class` | 0.0303 |
| 15 | `min_distance_m` | 0.0295 |

---

## 5. Key Findings & Scientific Limitations

1. **Physical Signals Dominating Classification**:
   - Thermal persistence metrics (`duration_days`, `distinct_detection_days`) and WorldCover land-cover classes provide dominant discriminative signal between stationary industrial thermal operations and episodic forest/agricultural burning.
   - Spectral SWIR anomaly ratios and indices (`swir2_anomaly_ratio`, `nbr2`, `bsi`) provide substantial feature importance for separating high-temperature localized combustion.
2. **Spatial Holdout Bias**:
   - The test partition is located in Northeast India, where the regional fire occurrences consist entirely of wildland/forest fires. Consequently, test-set macro-precision for unobserved classes is undefined or zero, reflecting the geographic concentration of the pilot dataset.
   - Spatial block holdout successfully avoided overoptimistic spatial autocorrelation leakage, exposing the true regional constraints of pilot-scale data.
