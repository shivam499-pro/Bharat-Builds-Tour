import os
from pathlib import Path
import pandas as pd


def get_paths():
    import sys
    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from repo_paths import require_processed_file

    input_path = require_processed_file("firms_satellite_enriched_pilot.parquet")
    output_dir = input_path.parent
    output_path = output_dir / "firms_ground_truth_pilot.parquet"
    return input_path, output_dir, output_path


def main():
    input_path, output_dir, output_path = get_paths()

    # 1. Read existing Phase V dataset
    df = pd.read_parquet(input_path)

    # Input statistics
    input_row_count = len(df)
    unique_input_event_count = df["event_id"].nunique()
    duplicate_event_count = input_row_count - unique_input_event_count

    # 2. Create exactly ONE row per unique event_id
    dedup_df = df.drop_duplicates(subset=["event_id"], keep="first").copy()

    # 3. Build ground-truth template DataFrame
    gt_df = pd.DataFrame({
        "event_id": dedup_df["event_id"].values,
        "label": pd.NA,
        "label_confidence": pd.NA,
        "label_source": pd.NA,
        "label_reason": pd.NA,
        "review_status": "pending",
        "reviewed_at": pd.NaT,
    })

    # Preserve reference fields if they exist in source dataset
    reference_fields_mapping = {
        "sampling_stratum": ["sampling_stratum"],
        "scene_id": ["scene_id", "satellite_scene_id"],
        "satellite_acquisition_datetime": ["satellite_acquisition_datetime", "satellite_acq_datetime"],
        "latitude": ["latitude", "centroid_lat"],
        "longitude": ["longitude", "centroid_lon"],
    }

    for target_col, candidate_cols in reference_fields_mapping.items():
        for src_col in candidate_cols:
            if src_col in dedup_df.columns:
                gt_df[target_col] = dedup_df[src_col].values
                break

    # Validation inside script
    output_row_count = len(gt_df)
    unique_output_event_count = gt_df["event_id"].nunique()
    non_null_labels = int(gt_df["label"].notna().sum())
    pending_count = int((gt_df["review_status"] == "pending").sum())

    print("--- Ground-Truth Template Validation ---")
    print(f"Input row count           : {input_row_count}")
    print(f"Unique input event count  : {unique_input_event_count}")
    print(f"Output row count          : {output_row_count}")
    print(f"Unique output event count : {unique_output_event_count}")
    print(f"Duplicate event count     : {duplicate_event_count}")
    print(f"Non-null label count      : {non_null_labels}")
    print(f"Pending count             : {pending_count}")

    # Enforce expected validation
    if non_null_labels != 0:
        raise ValueError(f"Validation failed: expected 0 non-null labels, got {non_null_labels}")
    if pending_count != output_row_count:
        raise ValueError(f"Validation failed: pending count ({pending_count}) != output row count ({output_row_count})")
    if output_row_count != unique_output_event_count:
        raise ValueError(f"Validation failed: output row count ({output_row_count}) != unique output events ({unique_output_event_count})")

    # 4. Output to parquet
    output_dir.mkdir(parents=True, exist_ok=True)
    gt_df.to_parquet(output_path, index=False)
    print(f"Ground-truth template successfully written to: {output_path}")

    # Read back validation
    verify_df = pd.read_parquet(output_path)
    assert len(verify_df) == output_row_count
    assert verify_df["label"].notna().sum() == 0
    assert (verify_df["review_status"] == "pending").sum() == output_row_count


if __name__ == "__main__":
    main()
