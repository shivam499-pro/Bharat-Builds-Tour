# ThermoGuard Phase VIII — Explainable Inference Pipeline

This document describes the design, inputs, outputs, limitations, and scientific constraints of the ThermoGuard explainable inference pipeline (`scripts/classify_event.py`).

---

## 1. Purpose

The inference pipeline provides a transparent, human-reviewable classification output for individual thermal events in the ThermoGuard pilot dataset. It is designed for:

- **Analyst-facing explainability**: Each prediction is accompanied by the evidence fields observed, the class probability breakdown, and the top contributing model features.
- **Scientific integrity**: Model predictions are **never** presented as ground truth. The pipeline explicitly separates HUMAN LABEL from MODEL PREDICTION at every output stage.
- **Auditability**: Model version is recorded and output is entirely deterministic given the saved model weights.

This pipeline is **NOT** a production decision system. It is a scientific baseline inference tool for pilot evaluation only.

---

## 2. Input Specification

### 2.1 Required Files

| File | Purpose |
|---|---|
| `data/satellite/processed/thermoguard_ml_features_pilot.parquet` | Validated ML feature dataset (100 events) |
| `data/satellite/processed/firms_ground_truth_pilot.parquet` | Human ground-truth labels — **read-only** |
| `models/logistic_regression_baseline.joblib` | Trained Logistic Regression sklearn Pipeline |
| `models/random_forest_baseline.joblib` | Trained Random Forest sklearn Pipeline |

### 2.2 Input Event Format

The pipeline accepts a single `event_id` string. It resolves the corresponding feature row from the ML feature dataset. The input must contain all 41 feature columns defined in the approved `PhaseVII_FEATURE_SPEC.md`.

### 2.3 Input Validation Rules

The pipeline enforces the following input guards:

1. **event_id must exist** in the validated feature dataset. Unknown IDs are rejected.
2. **All-null numeric features** trigger a hard rejection with an error message.
3. **Forbidden leakage columns** (`sampling_stratum`, `target_label`, `label`, `review_status`, `label_confidence`, etc.) are checked for absence before inference. Any leakage column present causes an immediate abort.
4. **Missing values** in individual features are handled by the fitted sklearn Pipeline (median imputation for numeric, constant fill for categorical), exactly as during training.

---

## 3. Preprocessing

The preprocessing pipeline is **identical** to the training-time pipeline recovered from the saved `joblib` model artifacts:

| Step | Type | Detail |
|---|---|---|
| Numeric imputation | `SimpleImputer(strategy='median')` | Medians fitted on training data only |
| Numeric scaling | `StandardScaler()` | Mean/std from training data only |
| Categorical imputation | `SimpleImputer(strategy='constant', fill_value='missing')` | Training-safe |
| Categorical encoding | `OneHotEncoder(handle_unknown='ignore')` | Unknown categories produce zero vectors |

> [!IMPORTANT]
> Preprocessing parameters (medians, means, stds, category vocabularies) were fitted **strictly on the training split** during `train_baseline_models.py`. Inference applies the same frozen transformers — no data leakage is possible at inference time.

---

## 4. Models

### 4.1 Model Registry

| Model ID | Algorithm | Saved Path | Model Version |
|---|---|---|---|
| `lr` | Logistic Regression | `models/logistic_regression_baseline.joblib` | `v0.1-baseline-pilot` |
| `rf` | Random Forest | `models/random_forest_baseline.joblib` | `v0.1-baseline-pilot` |

### 4.2 Output Classes

Both models predict one of three domain categories derived from `sampling_stratum` (surrogate baseline target):

| Class | Meaning |
|---|---|
| `agricultural_ephemeral` | Episodic burning consistent with agricultural land management patterns |
| `forest_wildfire` | Persistent biomass burning consistent with wildland/forest fire |
| `industrial_persistent` | Long-duration, spatially stable thermal signature consistent with industrial operations or mining |

> [!WARNING]
> These class labels are **not equivalent** to the human ground-truth labels defined in `PhaseVI_LABELING_PROTOCOL.md`. The surrogate target classes were inferred from geographic and temporal clustering, not from human expert review. Full human-reviewed labels remain pending.

---

## 5. Prediction Output

### 5.1 Fields Reported

| Field | Description |
|---|---|
| `predicted_class` | Argmax class from the classifier |
| `prediction_probability` | Per-class probability vector (from `predict_proba`) |
| `confidence` | Maximum class probability (scalar) |
| `top_contributing_features` | Top N features by Random Forest Gini importance (global, not per-event) |
| `evidence_fields` | Raw observed values of key evidence fields for the event |
| `model_version` | `v0.1-baseline-pilot` |

### 5.2 Feature Importance Caveat

Feature importances reported are **global Gini-based importances** from the Random Forest (Mean Decrease in Impurity). These reflect which features are most discriminative across **all training events**, not which features most influenced this specific event's prediction.

Per-event attribution (e.g., SHAP values) is not implemented in this baseline pipeline and would require an additional explainability library such as `shap`.

---

## 6. Human Label vs. Model Prediction Distinction

The pipeline enforces an explicit separation between human-reviewed evidence and model-generated predictions:

```
HUMAN LABEL (Ground Truth -- READ ONLY)
-----------------------------------------
Label         : [assigned by a qualified human reviewer per PhaseVI_LABELING_PROTOCOL.md]
Confidence    : [high / medium / low — as assessed by human reviewer]
Review Status : [pending / reviewed / final]

MODEL PREDICTIONS (Explainable Baseline -- NOT Ground Truth)
-----------------------------------------
Predicted     : [model output class]
Confidence    : [model class probability]
```

**The model output is NEVER written to `firms_ground_truth_pilot.parquet`.**
**Human labels are NEVER overwritten.**
**Model predictions are NEVER substituted for human expert review.**

---

## 7. Usage Reference

```bash
# List all available events and their human review status
python scripts/classify_event.py --list_events

# Run demo classification on the first available event
python scripts/classify_event.py --demo

# Classify a specific event using both models
python scripts/classify_event.py --event_id EVT_00963466

# Classify using only Random Forest, show top 15 features
python scripts/classify_event.py --event_id EVT_00963466 --model rf --top_n 15

# Classify using only Logistic Regression
python scripts/classify_event.py --event_id EVT_00963466 --model lr
```

---

## 8. Scientific Limitations

> [!CAUTION]
> The following limitations apply to all outputs of this inference pipeline. Failure to account for them may lead to scientifically invalid conclusions.

1. **Pilot scale**: The models were trained on N=100 events. Statistical significance of class-level performance estimates is low.
2. **Surrogate labels**: Models were trained on `sampling_stratum` (geographic/temporal clustering proxy), not on human-expert labels. Model output does not reflect expert classification.
3. **Geographic bias**: The spatial block split exposed that the test partition (Northeast India) contains exclusively wildland fire events. Class coverage varies strongly by geography.
4. **No per-event attribution**: Gini importances are global. They do not explain individual predictions.
5. **No calibration**: Model probabilities are uncalibrated. A confidence of 99.9% does not imply 99.9% empirical accuracy.
6. **No uncertainty quantification**: The pipeline reports point predictions and probabilities only. Epistemic uncertainty is not estimated.
7. **Version pinning**: Model artifacts are tied to the Phase VII feature schema. Any changes to feature engineering require model retraining.

---

## 9. Model Version

| Field | Value |
|---|---|
| Version | `v0.1-baseline-pilot` |
| Training phase | Phase VIII |
| Feature schema | Phase VII (PhaseVII_FEATURE_SPEC.md) |
| Training dataset | `thermoguard_ml_features_pilot.parquet` (N=100) |
| Target | `sampling_stratum` surrogate (not human ground truth) |
| Training script | `scripts/train_baseline_models.py` |
| Inference script | `scripts/classify_event.py` |
| Models saved | `models/logistic_regression_baseline.joblib`, `models/random_forest_baseline.joblib` |

---

## 10. What This Pipeline Does NOT Do

- Does **not** call any external AI APIs.
- Does **not** download satellite data.
- Does **not** modify any source datasets.
- Does **not** write predictions to the ground-truth parquet file.
- Does **not** claim production readiness.
- Does **not** provide SHAP or counterfactual explanations.
- Does **not** support batch inference (single-event only, by design for this pilot stage).
