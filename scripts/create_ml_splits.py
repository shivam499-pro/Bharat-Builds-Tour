import os
from pathlib import Path
from math import radians, cos, sin, asin, sqrt
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans


def get_paths():
    import sys
    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from repo_paths import require_processed_file

    input_path = require_processed_file("thermoguard_ml_features_pilot.parquet")
    output_dir = input_path.parent
    train_path = output_dir / "ml_train.parquet"
    val_path = output_dir / "ml_validation.parquet"
    test_path = output_dir / "ml_test.parquet"
    return input_path, output_dir, train_path, val_path, test_path


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    return 2 * r * asin(sqrt(a))


def main():
    input_path, output_dir, train_path, val_path, test_path = get_paths()
    print(f"Reading features from: {input_path}")

    df = pd.read_parquet(input_path)
    total_events = len(df)
    print(f"Total dataset events: {total_events}")

    # Geographic Clustering using deterministic seed
    # Group into 5 spatial regions across India
    kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
    coords = df[["centroid_lat", "centroid_lon"]].values
    df["spatial_region_id"] = kmeans.fit_predict(coords)

    # Cluster mapping:
    # Cluster 1 (East/Central-East: 39 events) -> Train
    # Cluster 4 (Central: 14 events) -> Train
    # Cluster 0 (North/Northwest: 11 events) -> Train
    # Total Train = 64 events (64%)
    # Cluster 3 (South/Southwest: 16 events) -> Validation (16%)
    # Cluster 2 (Northeast / Far-East: 20 events) -> Test (20%)
    train_mask = df["spatial_region_id"].isin([0, 1, 4])
    val_mask = df["spatial_region_id"] == 3
    test_mask = df["spatial_region_id"] == 2

    train_df = df[train_mask].copy().drop(columns=["spatial_region_id"])
    val_df = df[val_mask].copy().drop(columns=["spatial_region_id"])
    test_df = df[test_mask].copy().drop(columns=["spatial_region_id"])

    # Rows per split
    print("\n--- Rows Per Split ---")
    print(f"Train rows      : {len(train_df)} ({len(train_df)/total_events*100:.1f}%)")
    print(f"Validation rows : {len(val_df)} ({len(val_df)/total_events*100:.1f}%)")
    print(f"Test rows       : {len(test_df)} ({len(test_df)/total_events*100:.1f}%)")

    # Class distribution per split
    print("\n--- Target Class Distribution Per Split ---")
    for name, s_df in [("Train", train_df), ("Validation", val_df), ("Test", test_df)]:
        pop_count = int(s_df["target_label"].notna().sum())
        null_count = int(s_df["target_label"].isna().sum())
        print(f"{name:<10}: Populated labels={pop_count}, Unassigned/Pending labels={null_count}")

    # Geographic overlap check
    print("\n--- Geographic Overlap Audit ---")
    # Minimum pairwise distance between sets
    def min_pairwise_distance(df_a, df_b):
        min_d = float("inf")
        for _, r_a in df_a.iterrows():
            for _, r_b in df_b.iterrows():
                d = haversine_km(r_a["centroid_lat"], r_a["centroid_lon"], r_b["centroid_lat"], r_b["centroid_lon"])
                if d < min_d:
                    min_d = d
        return min_d

    d_train_val = min_pairwise_distance(train_df, val_df)
    d_train_test = min_pairwise_distance(train_df, test_df)
    d_val_test = min_pairwise_distance(val_df, test_df)

    print(f"Min Distance Train <-> Validation: {d_train_val:.2f} km")
    print(f"Min Distance Train <-> Test      : {d_train_test:.2f} km")
    print(f"Min Distance Val <-> Test        : {d_val_test:.2f} km")

    # Check for spatial block separation
    assert d_train_val > 50.0, "Spatial leakage risk: Train and Validation are too close!"
    assert d_train_test > 50.0, "Spatial leakage risk: Train and Test are too close!"
    assert d_val_test > 50.0, "Spatial leakage risk: Validation and Test are too close!"
    print("Geographic Overlap Check: PASSED (Zero spatial overlap; >50km inter-split buffer)")

    # Temporal overlap check
    print("\n--- Temporal Overlap Audit ---")
    # Check temporal delta ranges in each split
    print(f"Train temporal delta days range      : [{train_df['temporal_delta_days'].min():.1f}, {train_df['temporal_delta_days'].max():.1f}]")
    print(f"Validation temporal delta days range : [{val_df['temporal_delta_days'].min():.1f}, {val_df['temporal_delta_days'].max():.1f}]")
    print(f"Test temporal delta days range       : [{test_df['temporal_delta_days'].min():.1f}, {test_df['temporal_delta_days'].max():.1f}]")

    # Scientific Size Warning
    print("\n--- Scientific Sample Size Evaluation ---")
    if total_events < 500:
        print("SCIENTIFIC NOTICE: Total pilot dataset consists of N=100 events.")
        print("While spatial block holdout prevents spatial leakage, a 20-event test set")
        print("has high statistical variance across 6 candidate classes (average ~3.3 samples/class).")
        print("This partition is appropriate for initial pipeline verification and spatial holdout benchmarking,")
        print("but formal model validation requires larger labeled test batches.")

    # Write splits to Parquet
    train_df.to_parquet(train_path, index=False)
    val_df.to_parquet(val_path, index=False)
    test_df.to_parquet(test_path, index=False)

    print(f"\nWritten: {train_path}")
    print(f"Written: {val_path}")
    print(f"Written: {test_path}")


if __name__ == "__main__":
    main()
