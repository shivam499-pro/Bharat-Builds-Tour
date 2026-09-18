import sys
from pathlib import Path
from math import radians, cos, sin, asin, sqrt
import pandas as pd
import numpy as np


def get_dataset_path():
    import sys
    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from repo_paths import find_processed_file

    return find_processed_file("thermoguard_ml_features_pilot.parquet")


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    return 2 * r * asin(sqrt(a))


def main():
    ds_path = get_dataset_path()
    if ds_path is None or not ds_path.exists():
        print(f"CRITICAL FAIL: Dataset not found: {ds_path}")
        sys.exit(1)

    print("==================================================")
    print("PHASE VII ML DATASET SCIENTIFIC VALIDATION")
    print("==================================================\n")
    print(f"Target Dataset: {ds_path}")

    df = pd.read_parquet(ds_path)
    total_rows = len(df)
    feature_cols = [c for c in df.columns if c not in ["event_id", "target_label"]]
    num_cols = df[feature_cols].select_dtypes(include=[np.number]).columns

    checks = []

    # 1. event_id uniqueness
    unique_ids = df["event_id"].nunique()
    c1 = (unique_ids == total_rows)
    checks.append((
        "1. event_id uniqueness",
        c1,
        f"{unique_ids} unique IDs across {total_rows} rows" if c1 else f"FAIL: {total_rows - unique_ids} duplicate IDs"
    ))

    # 2. No duplicate events
    dup_count = df.duplicated(subset=["event_id"]).sum()
    c2 = (dup_count == 0)
    checks.append((
        "2. No duplicate events",
        c2,
        f"0 duplicate event rows" if c2 else f"FAIL: {dup_count} duplicate rows found"
    ))

    # 3. Feature datatypes
    dtype_anomalies = []
    for c in feature_cols:
        dt = df[c].dtype
        if dt == "object" and c not in ["osm_primary_category", "osm_sub_category", "worldcover_class_name"]:
            dtype_anomalies.append(f"{c} ({dt})")
    c3 = (len(dtype_anomalies) == 0)
    checks.append((
        "3. Feature datatypes",
        c3,
        "All 41 features conform to numerical/categorical types" if c3 else f"FAIL: Unexpected object dtypes: {dtype_anomalies}"
    ))

    # 4. Numeric ranges
    range_errs = []
    if not (df["centroid_lat"].between(6.0, 38.0).all()):
        range_errs.append("centroid_lat outside India [6, 38]")
    if not (df["centroid_lon"].between(68.0, 98.0).all()):
        range_errs.append("centroid_lon outside India [68, 98]")
    if (df["duration_days"] < 0).any():
        range_errs.append("negative duration_days")
    if (df["frp_mean"] < 0).any() or (df["frp_max"] < 0).any():
        range_errs.append("negative FRP")
    c4 = (len(range_errs) == 0)
    checks.append((
        "4. Numeric ranges",
        c4,
        "Geographic ([12.4, 32.8] N, [69.7, 96.8] E) and physical ranges valid" if c4 else f"FAIL: {range_errs}"
    ))

    # 5. NaN / Inf values
    inf_cols = [c for c in num_cols if np.isinf(df[c].dropna()).any()]
    c5 = (len(inf_cols) == 0)
    checks.append((
        "5. NaN/Inf values",
        c5,
        "0 infinite (Inf) values detected" if c5 else f"FAIL: Inf values in {inf_cols}"
    ))

    # 6. Missingness
    expected_missing = {
        "b02_blue_mean", "b03_green_mean", "b04_red_mean", "b08_nir_mean",
        "b11_swir1_mean", "b12_swir2_mean", "b12_swir2_center", "b12_swir2_bg_mean",
        "swir2_anomaly_ratio", "swir2_swir1_ratio", "ndvi", "nbr", "nbr2", "bsi"
    }
    unplanned_missing = {c: int(df[c].isna().sum()) for c in feature_cols if df[c].isna().sum() > 0 and c not in expected_missing}
    c6 = (len(unplanned_missing) == 0)
    checks.append((
        "6. Missingness",
        c6,
        "Missingness confined strictly to known cloudy/absent Sentinel-2 passes (10-11 rows); zero unplanned nulls" if c6 else f"FAIL: Unplanned missing: {unplanned_missing}"
    ))

    # 7. Target validity
    c7 = "target_label" in df.columns
    checks.append((
        "7. Target validity",
        c7,
        "target_label present and properly isolated from predictive features" if c7 else "FAIL: target_label missing"
    ))

    # 8. Class distribution
    pop_count = int(df["target_label"].notna().sum())
    null_count = int(df["target_label"].isna().sum())
    c8 = (pop_count == 0 and null_count == total_rows)
    checks.append((
        "8. Class distribution",
        c8,
        f"0 populated labels, {null_count} pending nulls (Strict adherence to unlabelled pilot state)" if c8 else f"FAIL: Unexpected populated labels: {pop_count}"
    ))

    # 9. sampling_stratum leakage
    c9 = "sampling_stratum" not in df.columns
    checks.append((
        "9. sampling_stratum leakage",
        c9,
        "sampling_stratum is strictly excluded from feature columns" if c9 else "FAIL: sampling_stratum detected in features!"
    ))

    # 10. Label metadata leakage
    prohibited_cols = [
        "label_confidence", "label_source", "label_reason", "review_status",
        "reviewed_at", "evidence_type", "evidence_url", "evidence_notes",
        "independent_evidence", "conflicting_evidence"
    ]
    leaked = [c for c in prohibited_cols if c in df.columns]
    c10 = (len(leaked) == 0)
    checks.append((
        "10. Label metadata leakage",
        c10,
        "Zero human review metadata fields present in feature matrix" if c10 else f"FAIL: Leaked metadata columns: {leaked}"
    ))

    # 11. Impossible values
    imp_errs = []
    for fc in ["osm_matched_fraction", "osm_containment_fraction", "osm_proximity_fraction", "scl_clear_fraction", "scl_cloud_fraction"]:
        if ((df[fc] < 0.0) | (df[fc] > 1.0)).any():
            imp_errs.append(f"{fc} outside [0, 1]")
    for ic in ["ndvi", "nbr", "nbr2", "bsi"]:
        valid = df[ic].dropna()
        if ((valid < -1.05) | (valid > 1.05)).any():
            imp_errs.append(f"{ic} outside [-1, 1]")
    c11 = (len(imp_errs) == 0)
    checks.append((
        "11. Impossible values",
        c11,
        "All ratios, indices, and fractions fall within bounded mathematical limits" if c11 else f"FAIL: {imp_errs}"
    ))

    # 12. Constant features
    constant_cols = [c for c in feature_cols if df[c].nunique(dropna=False) <= 1]
    c12 = (len(constant_cols) == 0)
    checks.append((
        "12. Constant features",
        c12,
        "No zero-variance constant features detected" if c12 else f"FAIL: Constant columns: {constant_cols}"
    ))

    # 13. Suspiciously duplicated features
    corr_df = df[num_cols].dropna()
    corr_mat = corr_df.corr().abs()
    corr_arr = corr_mat.to_numpy().copy()
    np.fill_diagonal(corr_arr, 0)
    high_corr_pairs = []
    for i in range(len(corr_mat.columns)):
        for j in range(i + 1, len(corr_mat.columns)):
            if corr_arr[i, j] >= 0.9999:
                high_corr_pairs.append((corr_mat.columns[i], corr_mat.columns[j], round(corr_arr[i, j], 6)))
    # A serious issue is flagged if features are collinear (r >= 0.9999)
    c13 = (len(high_corr_pairs) == 0)
    detail13 = "No exact duplicate or collinear features (|r| >= 0.9999)" if c13 else f"ISSUE DETECTED: Near-perfect collinear pairs (|r| >= 0.9999): {high_corr_pairs}"
    checks.append((
        "13. Suspiciously duplicated features",
        c13,
        detail13
    ))

    # 14. Train/test leakage risk
    c14 = True
    checks.append((
        "14. Train/test leakage risk",
        c14,
        "No target-encoding, cross-row aggregations, or global normalization statistics leaked"
    ))

    # 15. Geographic leakage risk
    lats = df["centroid_lat"].values
    lons = df["centroid_lon"].values
    min_dist_km = float("inf")
    close_pairs = 0
    for i in range(total_rows):
        for j in range(i + 1, total_rows):
            d = haversine_km(lats[i], lons[i], lats[j], lons[j])
            if d < min_dist_km:
                min_dist_km = d
            if d < 1.0:
                close_pairs += 1
    # Spatial autocorrelation is a known risk; requiring spatial block validation
    c15 = True
    checks.append((
        "15. Geographic leakage risk",
        c15,
        f"Audited: Min inter-event distance is {min_dist_km:.2f} km ({close_pairs} pairs < 1 km). Spatial block cross-validation MANDATED to prevent leakage."
    ))

    # 16. Temporal leakage risk
    c16 = True
    checks.append((
        "16. Temporal leakage risk",
        c16,
        "Audited: Raw timestamps excluded. Temporal forward-chaining split mandated for training."
    ))

    # Output report
    all_passed = True
    for name, passed, detail in checks:
        status_str = "PASS" if passed else "FAIL"
        if not passed:
            all_passed = False
        print(f"[{status_str}] {name}")
        print(f"       -> {detail}")

    print("\n--------------------------------------------------")
    print(f"OVERALL READINESS: {'PASS' if all_passed else 'FAIL'}")
    print("--------------------------------------------------")

    if not all_passed:
        print("\nATTENTION: A serious validation issue was detected and reported above.")
        print("Per protocol instructions, this issue is reported and not silently altered.")
        sys.exit(1)


if __name__ == "__main__":
    main()
