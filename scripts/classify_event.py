"""
classify_event.py -- ThermoGuard Phase VIII Explainable Inference Pipeline
==========================================================================

Purpose:
    Classify a single event from the validated ThermoGuard feature dataset using
    the trained baseline models (Logistic Regression and Random Forest).

    This script is strictly for EXPLAINABLE INFERENCE only.

    It:
      - Loads a validated event by event_id from the ML feature dataset.
      - Runs the event through both saved baseline models.
      - Reports the predicted class, class probabilities, and top contributing
        features from the Random Forest's Gini importances.
      - NEVER overwrites or modifies the human ground-truth dataset.
      - NEVER presents model predictions as ground truth.
      - Clearly distinguishes HUMAN LABEL from MODEL PREDICTION.

Usage:
    python classify_event.py --event_id <event_id>
    python classify_event.py --event_id <event_id> --model rf
    python classify_event.py --list_events
    python classify_event.py --demo

Input:
    data/satellite/processed/thermoguard_ml_features_pilot.parquet  (features)
    data/satellite/processed/firms_ground_truth_pilot.parquet        (human labels, read-only)
    models/logistic_regression_baseline.joblib
    models/random_forest_baseline.joblib

Output:
    Printed inference report (stdout). No files are written or modified.

Version:
    model_version: v0.1-baseline-pilot
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import joblib

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MODEL_VERSION = "v0.1-baseline-pilot"

ALLOWED_MODELS = ("lr", "rf", "both")

# Features passed to the sklearn pipelines (matches training time exactly)
# These are the 41 candidate features excluding event_id and target_label
FEATURE_COLUMNS = [
    "duration_days",
    "detection_count",
    "distinct_detection_days",
    "spatial_extent_km2",
    "distinct_satellites",
    "distinct_instruments",
    "centroid_lat",
    "centroid_lon",
    "frp_mean",
    "frp_max",
    "brightness_mean",
    "has_osm_industrial_match",
    "min_distance_m",
    "osm_matched_fraction",
    "osm_containment_fraction",
    "osm_proximity_fraction",
    "osm_tier",
    "osm_primary_category",
    "osm_sub_category",
    "worldcover_class",
    "worldcover_class_name",
    "has_spectral_features",
    "b02_blue_mean",
    "b03_green_mean",
    "b04_red_mean",
    "b08_nir_mean",
    "b11_swir1_mean",
    "b12_swir2_mean",
    "b12_swir2_center",
    "b12_swir2_bg_mean",
    "swir2_anomaly_ratio",
    "swir2_swir1_ratio",
    "ndvi",
    "nbr",
    "nbr2",
    "bsi",
    "has_satellite_scene",
    "satellite_cloud_cover_scene",
    "scl_clear_fraction",
    "scl_cloud_fraction",
    "temporal_delta_days",
]

CATEGORICAL_FEATURES = ["osm_primary_category", "osm_sub_category", "worldcover_class_name"]
NUMERIC_FEATURES = [c for c in FEATURE_COLUMNS if c not in CATEGORICAL_FEATURES]

# Evidence fields displayed in the report for human interpretability
EVIDENCE_DISPLAY_FIELDS = [
    "duration_days",
    "detection_count",
    "distinct_detection_days",
    "spatial_extent_km2",
    "frp_mean",
    "frp_max",
    "brightness_mean",
    "has_osm_industrial_match",
    "min_distance_m",
    "osm_tier",
    "osm_primary_category",
    "osm_sub_category",
    "worldcover_class_name",
    "swir2_anomaly_ratio",
    "ndvi",
    "nbr",
    "has_spectral_features",
    "satellite_cloud_cover_scene",
]


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

def resolve_paths():
    """Resolve data and model directories from standard candidate locations."""
    base = Path(r"C:\AWS Hackathon")
    data_candidates = [
        base / "data" / "satellite" / "processed",
        Path(__file__).resolve().parent.parent.parent / "data" / "satellite" / "processed",
        Path("data/satellite/processed"),
    ]
    models_candidates = [
        Path(__file__).resolve().parent.parent / "models",
        base / "Bharat-Builds-Tour" / "models",
        Path("models"),
    ]

    data_dir = None
    for p in data_candidates:
        if (p / "thermoguard_ml_features_pilot.parquet").exists():
            data_dir = p
            break

    models_dir = None
    for p in models_candidates:
        if (p / "logistic_regression_baseline.joblib").exists():
            models_dir = p
            break

    if data_dir is None:
        raise FileNotFoundError(
            "Cannot locate thermoguard_ml_features_pilot.parquet. "
            "Run build_ml_features.py first."
        )
    if models_dir is None:
        raise FileNotFoundError(
            "Cannot locate model files under 'models/'. "
            "Run train_baseline_models.py first."
        )

    return data_dir, models_dir


# ---------------------------------------------------------------------------
# Load resources
# ---------------------------------------------------------------------------

def load_feature_dataset(data_dir: Path) -> pd.DataFrame:
    path = data_dir / "thermoguard_ml_features_pilot.parquet"
    df = pd.read_parquet(path)
    return df


def load_ground_truth(data_dir: Path) -> pd.DataFrame:
    """Load ground truth strictly for READ ONLY human label display."""
    path = data_dir / "firms_ground_truth_pilot.parquet"
    if not path.exists():
        return pd.DataFrame(columns=["event_id", "label", "label_confidence", "review_status"])
    gt = pd.read_parquet(path)[["event_id", "label", "label_confidence", "review_status"]]
    return gt


def load_models(models_dir: Path):
    lr = joblib.load(models_dir / "logistic_regression_baseline.joblib")
    rf = joblib.load(models_dir / "random_forest_baseline.joblib")
    return lr, rf


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

def validate_event_row(row: pd.Series, event_id: str):
    """
    Validate that the event row has the required features.
    Rejects events with all-null numeric features.
    """
    missing_cols = [c for c in FEATURE_COLUMNS if c not in row.index]
    if missing_cols:
        raise ValueError(
            f"Event '{event_id}' is missing required feature columns: {missing_cols}"
        )

    all_null_numeric = all(pd.isna(row[c]) for c in NUMERIC_FEATURES)
    if all_null_numeric:
        raise ValueError(
            f"Event '{event_id}' has ALL numeric features null. "
            "Cannot produce a meaningful prediction. Event rejected."
        )


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------

def run_inference(model, model_name: str, X: pd.DataFrame, class_labels):
    """Run a single model pipeline and return prediction info."""
    y_pred = model.predict(X)[0]

    # Probabilities (not available for all models, but both LR and RF support it)
    try:
        proba = model.predict_proba(X)[0]
        proba_dict = {cls: round(float(p), 4) for cls, p in zip(class_labels, proba)}
        confidence = round(float(max(proba)), 4)
    except Exception:
        proba_dict = {}
        confidence = None

    return {
        "model": model_name,
        "predicted_class": y_pred,
        "prediction_probability": proba_dict,
        "confidence": confidence,
    }


def get_rf_top_features(rf_pipeline, X: pd.DataFrame, top_n: int = 10) -> list:
    """
    Extract top contributing features from the Random Forest model using
    Gini-based feature importances. These are global model importances,
    NOT per-sample SHAP values.
    """
    rf_clf = rf_pipeline.named_steps["classifier"]
    preprocessor = rf_pipeline.named_steps["preprocessor"]

    # Reconstruct transformed feature names
    cat_encoder = preprocessor.named_transformers_["cat"].named_steps["onehot"]
    cat_feature_names = list(cat_encoder.get_feature_names_out(CATEGORICAL_FEATURES))
    transformed_feature_names = NUMERIC_FEATURES + cat_feature_names

    importances = rf_clf.feature_importances_

    feat_df = pd.DataFrame({
        "feature": transformed_feature_names,
        "importance": importances
    }).sort_values("importance", ascending=False)

    top = feat_df.head(top_n).to_dict(orient="records")
    return [{"feature": r["feature"], "importance": round(r["importance"], 4)} for r in top]


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------

SEP = "=" * 70
SEP2 = "-" * 70


def print_inference_report(
    event_id: str,
    event_row: pd.Series,
    human_label_row,
    lr_result: dict,
    rf_result: dict,
    top_features: list,
):
    print()
    print(SEP)
    print("  THERMOGUARD -- EXPLAINABLE EVENT CLASSIFICATION REPORT")
    print(SEP)
    print(f"  Model Version : {MODEL_VERSION}")
    print(f"  Event ID      : {event_id}")
    lat = event_row.get("centroid_lat", "N/A")
    lon = event_row.get("centroid_lon", "N/A")
    print(f"  Location      : Lat={lat}, Lon={lon}")
    print()

    # ---- Human Label ----
    print(SEP2)
    print("  HUMAN LABEL (Ground Truth — READ ONLY)")
    print(SEP2)
    if human_label_row is not None and not pd.isna(human_label_row.get("label")):
        print(f"  Label          : {human_label_row['label']}")
        print(f"  Confidence     : {human_label_row.get('label_confidence', 'N/A')}")
        print(f"  Review Status  : {human_label_row.get('review_status', 'N/A')}")
    else:
        print("  Label          : NOT YET ASSIGNED (pending human review)")
        print("  Review Status  : pending")
    print()
    print("  [!] IMPORTANT: The human label is NOT derived from model output.")
    print("    Model predictions below are independent and do NOT overwrite")
    print("    or substitute for the human ground-truth record.")
    print()

    # ---- Model Predictions ----
    print(SEP2)
    print("  MODEL PREDICTIONS (Explainable Baseline — NOT Ground Truth)")
    print(SEP2)
    print()

    for result in [lr_result, rf_result]:
        print(f"  Model         : {result['model']}")
        print(f"  Predicted     : {result['predicted_class']}")
        if result.get("confidence") is not None:
            print(f"  Confidence    : {result['confidence']:.4f} ({result['confidence']*100:.1f}%)")
        if result.get("prediction_probability"):
            print("  Class Probabilities:")
            for cls, p in result["prediction_probability"].items():
                bar = "#" * int(p * 20)
                print(f"    {cls:<35} {p:.4f}  {bar}")
        print()

    # ---- Top Contributing Features ----
    print(SEP2)
    print("  TOP CONTRIBUTING FEATURES (Random Forest — Global Gini Importance)")
    print(SEP2)
    print("  Note: These are global model importances, NOT per-event attributions.")
    print()
    for rank, item in enumerate(top_features, 1):
        bar = "#" * int(item["importance"] * 200)
        print(f"  {rank:2}. {item['feature']:<40} {item['importance']:.4f}  {bar}")
    print()

    # ---- Evidence Fields ----
    print(SEP2)
    print("  EVIDENCE FIELDS USED BY MODEL (from validated feature dataset)")
    print(SEP2)
    for field in EVIDENCE_DISPLAY_FIELDS:
        val = event_row.get(field, "N/A")
        if pd.isna(val) if not isinstance(val, str) else False:
            val = "NULL"
        print(f"  {field:<35} : {val}")
    print()

    # ---- Limitations ----
    print(SEP2)
    print("  SCIENTIFIC LIMITATIONS & DISCLAIMERS")
    print(SEP2)
    print("  1. This model was trained on a 100-event pilot dataset.")
    print("  2. Target labels used sampling_stratum as surrogate (not human labels).")
    print("  3. Accuracy figures reflect geographic test block, not generalizable performance.")
    print("  4. Feature importances are Gini-based (global), not SHAP (per-event).")
    print("  5. DO NOT use model output to override or substitute human expert review.")
    print("  6. DO NOT treat predictions as ground truth for policy or operational decisions.")
    print(SEP)
    print()


# ---------------------------------------------------------------------------
# Event listing helper
# ---------------------------------------------------------------------------

def list_events(feat_df: pd.DataFrame, gt_df: pd.DataFrame):
    """Print all available event IDs with their human review status."""
    merged = feat_df[["event_id", "centroid_lat", "centroid_lon"]].copy()
    if not gt_df.empty:
        merged = merged.merge(gt_df[["event_id", "label", "review_status"]], on="event_id", how="left")
    else:
        merged["label"] = None
        merged["review_status"] = "unknown"

    print()
    print(SEP)
    print("  AVAILABLE EVENTS IN PILOT DATASET")
    print(SEP)
    print(f"  {'event_id':<45} {'lat':>8} {'lon':>9}  {'review_status':<18} {'label'}")
    print(SEP2)
    for _, row in merged.iterrows():
        lbl = row.get("label") if not pd.isna(row.get("label", float("nan"))) else "—"
        rs = row.get("review_status", "—")
        print(f"  {str(row['event_id']):<45} {row['centroid_lat']:>8.3f} {row['centroid_lon']:>9.3f}  {str(rs):<18} {lbl}")
    print()
    print(f"  Total events: {len(merged)}")
    print(SEP)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="ThermoGuard Phase VIII — Explainable Event Classifier",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python classify_event.py --list_events
  python classify_event.py --demo
  python classify_event.py --event_id <event_id>
  python classify_event.py --event_id <event_id> --model rf
        """
    )
    parser.add_argument(
        "--event_id",
        type=str,
        default=None,
        help="event_id to classify. Required unless --list_events or --demo."
    )
    parser.add_argument(
        "--model",
        type=str,
        choices=ALLOWED_MODELS,
        default="both",
        help="Which model(s) to use: 'lr', 'rf', or 'both' (default: both)."
    )
    parser.add_argument(
        "--top_n",
        type=int,
        default=10,
        help="Number of top features to display (default: 10)."
    )
    parser.add_argument(
        "--list_events",
        action="store_true",
        help="List all available events and exit."
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run classification on the first available event_id."
    )

    args = parser.parse_args()

    # Resolve paths
    try:
        data_dir, models_dir = resolve_paths()
    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)

    # Load datasets
    feat_df = load_feature_dataset(data_dir)
    gt_df = load_ground_truth(data_dir)

    # List events mode
    if args.list_events:
        list_events(feat_df, gt_df)
        sys.exit(0)

    # Determine event_id
    event_id = args.event_id
    if args.demo:
        if feat_df.empty:
            print("[ERROR] Feature dataset is empty.")
            sys.exit(1)
        event_id = str(feat_df["event_id"].iloc[0])
        print(f"\n[DEMO MODE] Using first event_id: {event_id}")

    if event_id is None:
        print("[ERROR] Provide --event_id <id> or use --list_events / --demo.")
        parser.print_help()
        sys.exit(1)

    # Look up the event in the feature dataset
    mask = feat_df["event_id"].astype(str) == str(event_id)
    if mask.sum() == 0:
        print(f"\n[ERROR] event_id '{event_id}' not found in feature dataset.")
        print("Use --list_events to see available IDs.")
        sys.exit(1)
    if mask.sum() > 1:
        print(f"\n[WARNING] Multiple rows found for event_id '{event_id}'. Using first match.")

    event_row = feat_df[mask].iloc[0]

    # Validate event
    try:
        validate_event_row(event_row, event_id)
    except ValueError as e:
        print(f"\n[ERROR] Event validation failed: {e}")
        sys.exit(1)

    # Look up human label (read-only)
    human_label_row = None
    if not gt_df.empty:
        gt_mask = gt_df["event_id"].astype(str) == str(event_id)
        if gt_mask.sum() > 0:
            human_label_row = gt_df[gt_mask].iloc[0].to_dict()

    # Load models
    try:
        lr_model, rf_model = load_models(models_dir)
    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)

    # Prepare feature row as DataFrame (model expects DataFrame with named columns)
    X = event_row[FEATURE_COLUMNS].to_frame().T.reset_index(drop=True)

    # Safety: never include leakage columns
    for forbidden in ["target_label", "sampling_stratum", "label", "review_status",
                      "label_confidence", "label_source", "label_reason"]:
        if forbidden in X.columns:
            print(f"\n[ERROR] Leakage column '{forbidden}' found in feature input. Aborting.")
            sys.exit(1)

    class_labels = list(lr_model.classes_)

    # Run inference
    lr_result = None
    rf_result = None

    if args.model in ("lr", "both"):
        lr_result = run_inference(lr_model, "Logistic Regression (v0.1-baseline)", X, class_labels)

    if args.model in ("rf", "both"):
        rf_result = run_inference(rf_model, "Random Forest (v0.1-baseline)", X, class_labels)

    # If only one model requested, build placeholder for the other
    if lr_result is None:
        lr_result = {"model": "Logistic Regression", "predicted_class": "NOT RUN",
                     "prediction_probability": {}, "confidence": None}
    if rf_result is None:
        rf_result = {"model": "Random Forest", "predicted_class": "NOT RUN",
                     "prediction_probability": {}, "confidence": None}

    # Get top features from Random Forest
    top_features = get_rf_top_features(rf_model, X, top_n=args.top_n)

    # Print report
    print_inference_report(
        event_id=event_id,
        event_row=event_row,
        human_label_row=human_label_row,
        lr_result=lr_result,
        rf_result=rf_result,
        top_features=top_features,
    )

    # Final model version line
    print(f"  Model version used: {MODEL_VERSION}")
    print()


if __name__ == "__main__":
    main()
