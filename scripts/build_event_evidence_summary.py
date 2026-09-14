import os
from pathlib import Path
import pandas as pd


def get_paths():
    possible_inputs = [
        Path(r"C:\AWS Hackathon\data\satellite\processed\firms_evidence_review_pilot.parquet"),
        Path(__file__).resolve().parent.parent.parent / "data" / "satellite" / "processed" / "firms_evidence_review_pilot.parquet",
        Path(__file__).resolve().parent.parent / "data" / "satellite" / "processed" / "firms_evidence_review_pilot.parquet",
        Path("data/satellite/processed/firms_evidence_review_pilot.parquet"),
    ]
    input_path = None
    for p in possible_inputs:
        if p.exists():
            input_path = p
            break
    if input_path is None:
        raise FileNotFoundError("Could not find firms_evidence_review_pilot.parquet")

    output_dir = input_path.parent
    output_path = output_dir / "firms_event_evidence_summary_pilot.csv"
    return input_path, output_dir, output_path


def main():
    input_path, output_dir, output_path = get_paths()
    print(f"Reading evidence review dataset from: {input_path}")

    df = pd.read_parquet(input_path)
    input_count = len(df)
    unique_input_ids = df["event_id"].nunique()

    # Deduplicate to guarantee exactly one row per event_id
    dedup_df = df.drop_duplicates(subset=["event_id"], keep="first").copy()

    # Data Quality flags based on existing data
    missing_satellite = dedup_df["b02_blue_mean"].isna() | dedup_df["scene_id"].isna() | (dedup_df["observation_status"] != "enriched")
    cloud_warning = (dedup_df["scl_cloud_fraction"] > 0.20) | (dedup_df["satellite_cloud_cover_scene"] > 50.0)
    missing_osm = dedup_df["min_distance_m"].isna()
    missing_worldcover = dedup_df["worldcover_class"].isna()
    missing_acq_dt = dedup_df["satellite_acquisition_datetime"].isna()

    # Compile data quality summary notes
    dq_notes = []
    for idx, row in dedup_df.iterrows():
        issues = []
        if missing_satellite.loc[idx]:
            issues.append("missing_satellite_features")
        if cloud_warning.loc[idx]:
            issues.append(f"high_cloud(scl_cloud={row.get('scl_cloud_fraction'):.2f})" if pd.notna(row.get('scl_cloud_fraction')) else "high_cloud")
        if missing_osm.loc[idx]:
            issues.append("missing_osm_distance")
        if missing_worldcover.loc[idx]:
            issues.append("missing_worldcover")
        if missing_acq_dt.loc[idx]:
            issues.append("missing_acq_datetime")
        dq_notes.append("; ".join(issues) if issues else "clean")

    # Build the compact evidence summary table
    summary_cols = {
        # EVENT
        "event_id": dedup_df["event_id"],
        "sampling_stratum": dedup_df["sampling_stratum"],
        "latitude": dedup_df["latitude"],
        "longitude": dedup_df["longitude"],
        "first_detection": dedup_df["first_detection"],
        "last_detection": dedup_df["last_detection"],
        # FIRMS
        "duration_days": dedup_df["duration_days"],
        "detection_count": dedup_df["detection_count"],
        "distinct_detection_days": dedup_df["distinct_detection_days"],
        "distinct_satellites": dedup_df["distinct_satellites"],
        "distinct_instruments": dedup_df["distinct_instruments"],
        "frp_mean": dedup_df["frp_mean"],
        "frp_max": dedup_df["frp_max"],
        "brightness_mean": dedup_df["brightness_mean"],
        "spatial_extent_km2": dedup_df["spatial_extent_km2"],
        # OSM
        "nearest_industrial_feature": dedup_df["osm_primary_category"],
        "osm_sub_category": dedup_df["osm_sub_category"],
        "osm_tier": dedup_df["osm_tier"],
        "distance_to_industrial_m": dedup_df["min_distance_m"],
        "osm_matched_fraction": dedup_df["osm_matched_fraction"],
        "osm_containment_fraction": dedup_df["osm_containment_fraction"],
        "osm_proximity_fraction": dedup_df["osm_proximity_fraction"],
        # WORLDCOVER
        "worldcover_class": dedup_df["worldcover_class"],
        "worldcover_class_name": dedup_df["worldcover_class_name"],
        "worldcover_status": dedup_df["worldcover_status"],
        # SENTINEL-2
        "scene_id": dedup_df["scene_id"],
        "satellite_acquisition_datetime": dedup_df["satellite_acquisition_datetime"],
        "temporal_delta_days": dedup_df["temporal_delta_days"],
        "observation_status": dedup_df["observation_status"],
        "scl_clear_fraction": dedup_df["scl_clear_fraction"],
        "scl_cloud_fraction": dedup_df["scl_cloud_fraction"],
        "satellite_cloud_cover_scene": dedup_df["satellite_cloud_cover_scene"],
        "b02_blue_mean": dedup_df["b02_blue_mean"],
        "b03_green_mean": dedup_df["b03_green_mean"],
        "b04_red_mean": dedup_df["b04_red_mean"],
        "b08_nir_mean": dedup_df["b08_nir_mean"],
        "b11_swir1_mean": dedup_df["b11_swir1_mean"],
        "b12_swir2_mean": dedup_df["b12_swir2_mean"],
        "ndvi": dedup_df["ndvi"],
        "nbr": dedup_df["nbr"],
        "nbr2": dedup_df["nbr2"],
        "bsi": dedup_df["bsi"],
        "swir2_swir1_ratio": dedup_df["swir2_swir1_ratio"],
        # DATA QUALITY
        "missing_satellite_evidence": missing_satellite.values,
        "cloud_quality_warning": cloud_warning.values,
        "missing_osm_context": missing_osm.values,
        "missing_worldcover": missing_worldcover.values,
        "missing_acquisition_datetime": missing_acq_dt.values,
        "data_quality_notes": dq_notes,
        # MANUAL REVIEW PLACEHOLDERS (must remain null/empty)
        "label": "",
        "label_confidence": "",
        "label_source": "",
        "label_reason": "",
        "evidence_type": "",
        "evidence_url": "",
        "evidence_notes": "",
        "independent_evidence": "",
        "conflicting_evidence": "",
        "review_status": "pending",
    }

    summary_df = pd.DataFrame(summary_cols)

    # Export to CSV
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(output_path, index=False)
    print(f"Evidence summary CSV written to: {output_path}")

    # Read back and validate
    val_df = pd.read_csv(output_path, keep_default_na=False)
    output_count = len(val_df)
    unique_event_count = val_df["event_id"].nunique()
    duplicate_count = output_count - unique_event_count
    missing_ids = len(set(dedup_df["event_id"]) - set(val_df["event_id"]))
    non_null_labels = (val_df["label"].str.strip() != "").sum()
    pending_count = (val_df["review_status"] == "pending").sum()

    print("\n--- Event Evidence Summary Validation ---")
    print(f"Input event count     : {input_count}")
    print(f"Output count          : {output_count}")
    print(f"Unique event count    : {unique_event_count}")
    print(f"Duplicate count       : {duplicate_count}")
    print(f"Missing event IDs     : {missing_ids}")
    print(f"Non-null label count  : {non_null_labels}")
    print(f"Pending review count  : {pending_count}")

    assert input_count == output_count, f"Count mismatch: {input_count} != {output_count}"
    assert duplicate_count == 0, f"Duplicate events detected: {duplicate_count}"
    assert missing_ids == 0, f"Missing IDs detected: {missing_ids}"
    assert non_null_labels == 0, f"Non-null labels found: {non_null_labels}"
    assert pending_count == output_count, f"Pending count ({pending_count}) != Output count ({output_count})"


if __name__ == "__main__":
    main()
