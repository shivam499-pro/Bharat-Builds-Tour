import os
from pathlib import Path
import pandas as pd


def get_paths():
    possible_inputs = [
        Path(r"C:\AWS Hackathon\data\satellite\processed\firms_ground_truth_pilot.parquet"),
        Path(__file__).resolve().parent.parent.parent / "data" / "satellite" / "processed" / "firms_ground_truth_pilot.parquet",
        Path(__file__).resolve().parent.parent / "data" / "satellite" / "processed" / "firms_ground_truth_pilot.parquet",
        Path("data/satellite/processed/firms_ground_truth_pilot.parquet"),
    ]
    input_path = None
    for p in possible_inputs:
        if p.exists():
            input_path = p
            break

    if input_path is None:
        raise FileNotFoundError("Could not find input file: firms_ground_truth_pilot.parquet")

    output_dir = input_path.parent
    output_path = output_dir / "firms_ground_truth_pilot_review.csv"
    return input_path, output_dir, output_path


def main():
    input_path, output_dir, output_path = get_paths()

    # 1. Read validated ground-truth parquet
    df = pd.read_parquet(input_path)

    input_event_count = len(df)
    unique_input_ids = df["event_id"].nunique()

    # 2. Preserve exactly one row per event_id
    dedup_df = df.drop_duplicates(subset=["event_id"], keep="first").copy()

    # 3. Construct review dataframe with specified column order
    review_columns = [
        "event_id",
        "sampling_stratum",
        "scene_id",
        "satellite_acquisition_datetime",
        "latitude",
        "longitude",
        "label",
        "label_confidence",
        "label_source",
        "label_reason",
        "evidence_type",
        "evidence_url",
        "evidence_notes",
        "independent_evidence",
        "conflicting_evidence",
        "review_status",
    ]

    review_df = pd.DataFrame()

    # Populate existing reference fields
    for col in ["event_id", "sampling_stratum", "scene_id", "satellite_acquisition_datetime", "latitude", "longitude"]:
        if col in dedup_df.columns:
            review_df[col] = dedup_df[col].values
        else:
            review_df[col] = ""

    # Label fields: MUST be empty/null
    for col in ["label", "label_confidence", "label_source", "label_reason"]:
        review_df[col] = ""

    # Evidence fields: MUST be empty
    for col in ["evidence_type", "evidence_url", "evidence_notes", "independent_evidence", "conflicting_evidence"]:
        review_df[col] = ""

    # Review status: MUST be "pending"
    review_df["review_status"] = "pending"

    # Reorder explicitly
    review_df = review_df[review_columns]

    # Export to CSV
    output_dir.mkdir(parents=True, exist_ok=True)
    review_df.to_csv(output_path, index=False)
    print(f"Exported review template to: {output_path}")

    # Validation after export (reading back from CSV)
    exported_df = pd.read_csv(output_path, keep_default_na=False)

    csv_row_count = len(exported_df)
    unique_event_id_count = exported_df["event_id"].nunique()
    duplicate_count = csv_row_count - unique_event_id_count
    non_empty_labels = (exported_df["label"].str.strip() != "").sum()
    pending_count = (exported_df["review_status"] == "pending").sum()

    print("\n--- Export Validation Summary ---")
    print(f"Input event count      : {input_event_count}")
    print(f"CSV row count          : {csv_row_count}")
    print(f"Unique event_id count  : {unique_event_id_count}")
    print(f"Duplicate count        : {duplicate_count}")
    print(f"Non-empty label count  : {non_empty_labels}")
    print(f"Pending count          : {pending_count}")

    # Enforce rules
    if input_event_count != csv_row_count:
        raise ValueError(f"Input event count ({input_event_count}) != CSV row count ({csv_row_count})")
    if csv_row_count != unique_event_id_count:
        raise ValueError(f"Duplicate events found in CSV: {duplicate_count}")
    if non_empty_labels != 0:
        raise ValueError(f"Non-empty labels found: {non_empty_labels}")
    if pending_count != csv_row_count:
        raise ValueError(f"Pending count ({pending_count}) != CSV row count ({csv_row_count})")


if __name__ == "__main__":
    main()
