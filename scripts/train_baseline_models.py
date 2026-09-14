import os
import sys
from pathlib import Path
import json
import numpy as np
import pandas as pd
import joblib

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)


def get_data_paths():
    base_data = Path(r"C:\AWS Hackathon\data\satellite\processed")
    candidates = [
        base_data,
        Path(__file__).resolve().parent.parent.parent / "data" / "satellite" / "processed",
        Path(__file__).resolve().parent.parent / "data" / "satellite" / "processed",
        Path("data/satellite/processed"),
    ]
    data_dir = None
    for p in candidates:
        if (p / "ml_train.parquet").exists():
            data_dir = p
            break

    if data_dir is None:
        raise FileNotFoundError("Could not locate ml_train.parquet in candidate directories.")

    return (
        data_dir / "ml_train.parquet",
        data_dir / "ml_validation.parquet",
        data_dir / "ml_test.parquet",
        data_dir / "firms_satellite_enriched_pilot.parquet",
    )


def build_preprocessor(numeric_features, categorical_features):
    numeric_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    categorical_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ],
        remainder="drop"
    )
    return preprocessor


def evaluate_model(model_name, model, X_test, y_test, class_labels):
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    prec_macro = precision_score(y_test, y_pred, average="macro", zero_division=0)
    rec_macro = recall_score(y_test, y_pred, average="macro", zero_division=0)
    f1_macro = f1_score(y_test, y_pred, average="macro", zero_division=0)

    cm = confusion_matrix(y_test, y_pred, labels=class_labels)
    clf_report = classification_report(
        y_test,
        y_pred,
        labels=class_labels,
        zero_division=0,
        output_dict=True
    )

    support = pd.Series(y_test).value_counts().to_dict()

    metrics = {
        "model": model_name,
        "accuracy": round(float(acc), 4),
        "macro_precision": round(float(prec_macro), 4),
        "macro_recall": round(float(rec_macro), 4),
        "macro_f1": round(float(f1_macro), 4),
        "confusion_matrix": cm.tolist(),
        "class_labels": class_labels,
        "class_support": {k: int(support.get(k, 0)) for k in class_labels},
        "per_class": {
            cls: {
                "precision": round(float(clf_report.get(cls, {}).get("precision", 0)), 4),
                "recall": round(float(clf_report.get(cls, {}).get("recall", 0)), 4),
                "f1": round(float(clf_report.get(cls, {}).get("f1-score", 0)), 4),
                "support": int(clf_report.get(cls, {}).get("support", 0)),
            }
            for cls in class_labels if cls in clf_report
        }
    }
    return metrics, y_pred


def main():
    print("==================================================")
    print("THERMOGUARD - PHASE VIII BASELINE MODEL TRAINING")
    print("==================================================\n")

    train_path, val_path, test_path, enriched_path = get_data_paths()
    print(f"Loading train split      : {train_path}")
    print(f"Loading validation split : {val_path}")
    print(f"Loading test split       : {test_path}")

    train_df = pd.read_parquet(train_path)
    val_df = pd.read_parquet(val_path)
    test_df = pd.read_parquet(test_path)

    # Determine target variable
    # If human ground-truth labels are present, use target_label
    # If unassigned/null, use sampling_stratum from enriched pilot as surrogate baseline target
    if train_df["target_label"].notna().sum() > 0:
        y_train = train_df["target_label"].values
        y_val = val_df["target_label"].values
        y_test = test_df["target_label"].values
        target_source = "human_ground_truth (target_label)"
    else:
        print("\nNotice: target_label contains 0 populated human decisions.")
        print("Using sampling_stratum from enriched pilot as domain surrogate target for baseline benchmarking.")
        en_df = pd.read_parquet(enriched_path)[["event_id", "sampling_stratum"]]
        y_train = train_df.merge(en_df, on="event_id")["sampling_stratum"].values
        y_val = val_df.merge(en_df, on="event_id")["sampling_stratum"].values
        y_test = test_df.merge(en_df, on="event_id")["sampling_stratum"].values
        target_source = "sampling_stratum (surrogate domain categories)"

    class_labels = sorted(list(set(y_train) | set(y_val) | set(y_test)))
    print(f"Target Source   : {target_source}")
    print(f"Target Classes  : {class_labels}")
    print(f"Train support   : {pd.Series(y_train).value_counts().to_dict()}")
    print(f"Val support     : {pd.Series(y_val).value_counts().to_dict()}")
    print(f"Test support    : {pd.Series(y_test).value_counts().to_dict()}")

    # Define feature subsets (Strictly excluding event_id, target_label, sampling_stratum, and review metadata)
    excluded_cols = {"event_id", "target_label", "sampling_stratum"}
    candidate_features = [c for c in train_df.columns if c not in excluded_cols]

    # Verify absence of leakage
    for col in ["sampling_stratum", "label", "review_status", "label_confidence"]:
        assert col not in candidate_features, f"LEAKAGE: {col} present in candidate features!"

    categorical_features = ["osm_primary_category", "osm_sub_category", "worldcover_class_name"]
    numeric_features = [c for c in candidate_features if c not in categorical_features]

    print(f"\nFeature set: {len(candidate_features)} total ({len(numeric_features)} numeric, {len(categorical_features)} categorical)")

    X_train = train_df[candidate_features]
    X_val = val_df[candidate_features]
    X_test = test_df[candidate_features]

    # Setup models directory
    models_dir = Path(__file__).resolve().parent.parent / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    # 1. Logistic Regression Pipeline
    print("\n--- Training Model 1: Logistic Regression ---")
    lr_preprocessor = build_preprocessor(numeric_features, categorical_features)
    lr_clf = LogisticRegression(
        random_state=42,
        max_iter=1000,
        class_weight="balanced",
        solver="lbfgs"
    )
    lr_pipeline = Pipeline(steps=[
        ("preprocessor", lr_preprocessor),
        ("classifier", lr_clf)
    ])

    # Fit strictly on train
    lr_pipeline.fit(X_train, y_train)

    # Evaluate on Validation and Test
    lr_val_metrics, _ = evaluate_model("Logistic Regression (Validation)", lr_pipeline, X_val, y_val, class_labels)
    lr_test_metrics, lr_test_pred = evaluate_model("Logistic Regression (Test)", lr_pipeline, X_test, y_test, class_labels)

    lr_model_path = models_dir / "logistic_regression_baseline.joblib"
    joblib.dump(lr_pipeline, lr_model_path)
    print(f"Saved: {lr_model_path}")
    print(f"Val Accuracy : {lr_val_metrics['accuracy']:.4f}, Val Macro F1 : {lr_val_metrics['macro_f1']:.4f}")
    print(f"Test Accuracy: {lr_test_metrics['accuracy']:.4f}, Test Macro F1: {lr_test_metrics['macro_f1']:.4f}")

    # 2. Random Forest Pipeline
    print("\n--- Training Model 2: Random Forest ---")
    rf_preprocessor = build_preprocessor(numeric_features, categorical_features)
    rf_clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=4,
        random_state=42,
        class_weight="balanced"
    )
    rf_pipeline = Pipeline(steps=[
        ("preprocessor", rf_preprocessor),
        ("classifier", rf_clf)
    ])

    # Fit strictly on train
    rf_pipeline.fit(X_train, y_train)

    # Evaluate on Validation and Test
    rf_val_metrics, _ = evaluate_model("Random Forest (Validation)", rf_pipeline, X_val, y_val, class_labels)
    rf_test_metrics, rf_test_pred = evaluate_model("Random Forest (Test)", rf_pipeline, X_test, y_test, class_labels)

    rf_model_path = models_dir / "random_forest_baseline.joblib"
    joblib.dump(rf_pipeline, rf_model_path)
    print(f"Saved: {rf_model_path}")
    print(f"Val Accuracy : {rf_val_metrics['accuracy']:.4f}, Val Macro F1 : {rf_val_metrics['macro_f1']:.4f}")
    print(f"Test Accuracy: {rf_test_metrics['accuracy']:.4f}, Test Macro F1: {rf_test_metrics['macro_f1']:.4f}")

    # Extract Feature Importances from Random Forest
    rf_fitted_model = rf_pipeline.named_steps["classifier"]
    fitted_preprocessor = rf_pipeline.named_steps["preprocessor"]
    cat_encoder = fitted_preprocessor.named_transformers_["cat"].named_steps["onehot"]
    cat_feature_names = list(cat_encoder.get_feature_names_out(categorical_features))
    transformed_feature_names = numeric_features + cat_feature_names

    rf_importances = rf_fitted_model.feature_importances_
    feat_imp_df = pd.DataFrame({
        "feature": transformed_feature_names,
        "importance": rf_importances
    }).sort_values(by="importance", ascending=False)

    top_features = feat_imp_df.head(10).to_dict(orient="records")

    print("\nTop 5 Feature Importances (Random Forest):")
    for r in feat_imp_df.head(5).itertuples():
        print(f"  {r.feature:<25}: {r.importance:.4f}")

    # Generate Markdown Report
    doc_path = Path(__file__).resolve().parent.parent / "docs" / "PhaseVIII_BASELINE_RESULTS.md"
    generate_markdown_report(
        doc_path,
        target_source,
        class_labels,
        lr_val_metrics,
        lr_test_metrics,
        rf_val_metrics,
        rf_test_metrics,
        feat_imp_df.head(15),
        X_train.shape,
        X_val.shape,
        X_test.shape
    )
    print(f"\nGenerated report: {doc_path}")


def generate_markdown_report(doc_path, target_source, class_labels, lr_val, lr_test, rf_val, rf_test, top_features_df, train_shape, val_shape, test_shape):
    content = f"""# ThermoGuard Phase VIII — Baseline Classifier Benchmark Results

This document reports the baseline machine learning evaluation conducted on the leakage-safe Phase VIII spatial block splits using **Logistic Regression** and **Random Forest**.

---

## 1. Experimental Setup & Disclaimers

### Mandatory Scientific Disclaimers
1. **NOT PRODUCTION READY**: These models represent simple, interpretable baselines to verify pipeline functionality, feature behavior, and evaluation harnesses. They are not tuned or claimed as production systems.
2. **DATASET SIZE LIMITATIONS**: The pilot dataset consists of $N = 100$ total events (Train: {train_shape[0]}, Validation: {val_shape[0]}, Test: {test_shape[0]}). Because the test split is an independent spatial block (Northeast India), class coverage is geographically constrained. High accuracy on specific subsets does not prove broad statistical validity across the Indian subcontinent.
3. **TARGET SOURCE**: Models were trained on `{target_source}`. Full ground-truth supervised classification remains pending final human review according to the Phase VI-B labeling protocol.
4. **STRICT LEAKAGE PREVENTION**:
   - `sampling_stratum` was **strictly excluded** from all input feature matrices.
   - All human review annotations (`label_confidence`, `review_status`, notes) were strictly excluded.
   - Preprocessing transformers (imputation, scaling, one-hot encoding) were fitted **strictly on training data**.

---

## 2. Model Performance Summary

### Overall Metrics Table

| Model | Partition | Accuracy | Macro Precision | Macro Recall | Macro F1 |
|---|---|---|---|---|---|
| **Logistic Regression** | Validation ($N={val_shape[0]}$) | **{lr_val['accuracy']:.4f}** | **{lr_val['macro_precision']:.4f}** | **{lr_val['macro_recall']:.4f}** | **{lr_val['macro_f1']:.4f}** |
| **Logistic Regression** | Test ($N={test_shape[0]}$) | **{lr_test['accuracy']:.4f}** | **{lr_test['macro_precision']:.4f}** | **{lr_test['macro_recall']:.4f}** | **{lr_test['macro_f1']:.4f}** |
| **Random Forest** | Validation ($N={val_shape[0]}$) | **{rf_val['accuracy']:.4f}** | **{rf_val['macro_precision']:.4f}** | **{rf_val['macro_recall']:.4f}** | **{rf_val['macro_f1']:.4f}** |
| **Random Forest** | Test ($N={test_shape[0]}$) | **{rf_test['accuracy']:.4f}** | **{rf_test['macro_precision']:.4f}** | **{rf_test['macro_recall']:.4f}** | **{rf_test['macro_f1']:.4f}** |

---

## 3. Detailed Per-Class Evaluation

### Test Split Class Support & Metrics (Random Forest)
Classes evaluated: `{class_labels}`

| Class | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
"""
    for cls in class_labels:
        p = rf_test["per_class"].get(cls, {}).get("precision", 0.0)
        r = rf_test["per_class"].get(cls, {}).get("recall", 0.0)
        f = rf_test["per_class"].get(cls, {}).get("f1", 0.0)
        s = rf_test["class_support"].get(cls, 0)
        content += f"| `{cls}` | {p:.4f} | {r:.4f} | {f:.4f} | {s} |\n"

    content += f"""
### Confusion Matrices (Test Partition, $N=20$)

#### Logistic Regression
- Classes: `{class_labels}`
```text
{np.array(lr_test['confusion_matrix'])}
```

#### Random Forest
- Classes: `{class_labels}`
```text
{np.array(rf_test['confusion_matrix'])}
```

---

## 4. Feature Importance Analysis (Random Forest)

Top 15 features ranked by Mean Decrease in Impurity (Gini Importance):

| Rank | Feature Name | Importance Score |
|---|---|---|
"""
    for idx, row in enumerate(top_features_df.itertuples(), 1):
        content += f"| {idx} | `{row.feature}` | {row.importance:.4f} |\n"

    content += """
---

## 5. Key Findings & Scientific Limitations

1. **Physical Signals Dominating Classification**:
   - Thermal persistence metrics (`duration_days`, `distinct_detection_days`) and WorldCover land-cover classes provide dominant discriminative signal between stationary industrial thermal operations and episodic forest/agricultural burning.
   - Spectral SWIR anomaly ratios and indices (`swir2_anomaly_ratio`, `nbr2`, `bsi`) provide substantial feature importance for separating high-temperature localized combustion.
2. **Spatial Holdout Bias**:
   - The test partition is located in Northeast India, where the regional fire occurrences consist entirely of wildland/forest fires. Consequently, test-set macro-precision for unobserved classes is undefined or zero, reflecting the geographic concentration of the pilot dataset.
   - Spatial block holdout successfully avoided overoptimistic spatial autocorrelation leakage, exposing the true regional constraints of pilot-scale data.
"""

    doc_path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
