import os
from pathlib import Path
import pandas as pd
import numpy as np


def get_paths():
    possible_en = [
        Path(r"C:\AWS Hackathon\data\satellite\processed\firms_satellite_enriched_pilot.parquet"),
        Path(__file__).resolve().parent.parent.parent / "data" / "satellite" / "processed" / "firms_satellite_enriched_pilot.parquet",
        Path(__file__).resolve().parent.parent / "data" / "satellite" / "processed" / "firms_satellite_enriched_pilot.parquet",
        Path("data/satellite/processed/firms_satellite_enriched_pilot.parquet"),
    ]
    en_path = None
    for p in possible_en:
        if p.exists():
            en_path = p
            break
    if en_path is None:
        raise FileNotFoundError("Could not find firms_satellite_enriched_pilot.parquet")

    possible_gt = [
        Path(r"C:\AWS Hackathon\data\satellite\processed\firms_ground_truth_pilot.parquet"),
        Path(__file__).resolve().parent.parent.parent / "data" / "satellite" / "processed" / "firms_ground_truth_pilot.parquet",
        Path(__file__).resolve().parent.parent / "data" / "satellite" / "processed" / "firms_ground_truth_pilot.parquet",
        Path("data/satellite/processed/firms_ground_truth_pilot.parquet"),
    ]
    gt_path = None
    for p in possible_gt:
        if p.exists():
            gt_path = p
            break
    if gt_path is None:
        raise FileNotFoundError("Could not find firms_ground_truth_pilot.parquet")

    output_dir = en_path.parent
    output_path = output_dir / "thermoguard_ml_features_pilot.parquet"
    return en_path, gt_path, output_dir, output_path


def main():
    en_path, gt_path, output_dir, output_path = get_paths()
    print(f"Loading enriched features from : {en_path}")
    print(f"Loading ground truth labels from: {gt_path}")

    df_en = pd.read_parquet(en_path)
    df_gt = pd.read_parquet(gt_path)

    input_en_rows = len(df_en)
    input_gt_rows = len(df_gt)
    print(f"Input enriched rows: {input_en_rows}, Input GT rows: {input_gt_rows}")

    # 1. Join using event_id only
    merged = pd.merge(
        df_en,
        df_gt[["event_id", "label"]],
        on="event_id",
        how="inner",
        suffixes=("", "_gt")
    )
    print(f"Merged row count: {len(merged)}")

    # 2. Build explicit ML Feature Dataset
    # STRICT LEAKAGE PREVENTION:
    # Explicitly verify that prohibited columns are NOT included as features:
    prohibited_candidates = [
        "sampling_stratum", "label_confidence", "label_source", "label_reason",
        "review_status", "reviewed_at", "evidence_type", "evidence_url",
        "evidence_notes", "independent_evidence", "conflicting_evidence",
        "sampling_criteria_rationale", "stac_search_start", "stac_search_end",
        "satellite_source", "satellite_scene_id", "satellite_acq_datetime",
        "first_detection", "last_detection"
    ]

    ml_df = pd.DataFrame()
    ml_df["event_id"] = merged["event_id"]

    # --- Group 1: FIRMS Temporal & Spatial ---
    ml_df["duration_days"] = merged["duration_days"].astype(float)
    ml_df["detection_count"] = merged["detection_count"].astype(int)
    ml_df["distinct_detection_days"] = merged["distinct_detection_days"].astype(int)
    ml_df["spatial_extent_km2"] = merged["spatial_extent_km2"].astype(float)
    ml_df["distinct_satellites"] = merged["distinct_satellites"].astype(int)
    ml_df["distinct_instruments"] = merged["distinct_instruments"].astype(int)
    ml_df["centroid_lat"] = merged["centroid_lat"].astype(float)
    ml_df["centroid_lon"] = merged["centroid_lon"].astype(float)

    # --- Group 2: FIRMS Thermal ---
    ml_df["frp_mean"] = merged["frp_mean"].astype(float)
    ml_df["frp_max"] = merged["frp_max"].astype(float)
    ml_df["brightness_mean"] = merged["brightness_mean"].astype(float)

    # --- Group 3: OSM Infrastructure ---
    # Missingness: 60 events have no nearby industrial match
    ml_df["has_osm_industrial_match"] = merged["min_distance_m"].notna().astype(int)
    ml_df["min_distance_m"] = merged["min_distance_m"].fillna(10000.0).astype(float)
    ml_df["osm_matched_fraction"] = merged["osm_matched_fraction"].astype(float)
    ml_df["osm_containment_fraction"] = merged["osm_containment_fraction"].astype(float)
    ml_df["osm_proximity_fraction"] = merged["osm_proximity_fraction"].astype(float)
    ml_df["osm_tier"] = merged["osm_tier"].fillna(0.0).astype(float)
    ml_df["osm_primary_category"] = merged["osm_primary_category"].fillna("none").astype(str)
    ml_df["osm_sub_category"] = merged["osm_sub_category"].fillna("none").astype(str)

    # --- Group 4: ESA WorldCover ---
    ml_df["worldcover_class"] = merged["worldcover_class"].astype(int)
    ml_df["worldcover_class_name"] = merged["worldcover_class_name"].astype(str)

    # --- Group 5: Sentinel-2 Spectral Features ---
    spectral_cols = [
        "b02_blue_mean", "b03_green_mean", "b04_red_mean", "b08_nir_mean",
        "b11_swir1_mean", "b12_swir2_mean", "b12_swir2_center", "b12_swir2_bg_mean",
        "swir2_anomaly_ratio", "swir2_swir1_ratio", "ndvi", "nbr", "nbr2", "bsi"
    ]
    # Missing indicator for spectral observation
    ml_df["has_spectral_features"] = merged["b02_blue_mean"].notna().astype(int)
    for col in spectral_cols:
        ml_df[col] = merged[col]

    # --- Group 6: Sentinel-2 Quality & Cloud Features ---
    ml_df["has_satellite_scene"] = (merged["satellite_scene_id"].notna()).astype(int)
    ml_df["satellite_cloud_cover_scene"] = merged["satellite_cloud_cover_scene"].fillna(-1.0).astype(float)
    ml_df["scl_clear_fraction"] = merged["scl_clear_fraction"].fillna(0.0).astype(float)
    ml_df["scl_cloud_fraction"] = merged["scl_cloud_fraction"].fillna(1.0).astype(float)

    # --- Group 7: Temporal Alignment ---
    ml_df["temporal_delta_days"] = merged["temporal_delta_days"].fillna(999.0).astype(float)

    # --- Target Variable ---
    # Final human label separately as target (may be NULL at this stage)
    ml_df["target_label"] = merged["label"]

    # 3. Leakage Checks
    for col in prohibited_candidates:
        assert col not in ml_df.columns, f"LEAKAGE DETECTED: Prohibited column {col} in ML features!"

    assert "sampling_stratum" not in ml_df.columns, "LEAKAGE: sampling_stratum present in ML dataset!"

    # 4. Summary and Missingness Statistics
    output_rows = len(ml_df)
    excluded_rows = input_en_rows - output_rows
    feature_cols = [c for c in ml_df.columns if c not in ["event_id", "target_label"]]
    feature_count = len(feature_cols)

    print("\n--- ML Feature Dataset Summary ---")
    print(f"Input rows            : {input_en_rows}")
    print(f"Output rows           : {output_rows}")
    print(f"Excluded rows         : {excluded_rows}")
    print(f"Feature count         : {feature_count}")
    print(f"Target column         : target_label")
    print(f"Populated target count: {ml_df['target_label'].notna().sum()}")
    print(f"Null target count     : {ml_df['target_label'].isna().sum()}")

    # Missing value audit
    print("\nFeature Missing Values Audit:")
    null_counts = ml_df[feature_cols].isna().sum()
    for col, n in null_counts[null_counts > 0].items():
        print(f"  - {col}: {n} missing")

    # 5. Write Parquet
    output_dir.mkdir(parents=True, exist_ok=True)
    ml_df.to_parquet(output_path, index=False)
    print(f"\nML feature dataset successfully written to: {output_path}")

    # Read back verification
    verify = pd.read_parquet(output_path)
    assert len(verify) == output_rows
    assert "event_id" in verify.columns
    assert "target_label" in verify.columns
    assert "sampling_stratum" not in verify.columns
    print("Verification passed successfully.")


if __name__ == "__main__":
    main()
