import os
from pathlib import Path
import pandas as pd


def get_paths():
    import sys
    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from repo_paths import require_processed_file

    gt_path = require_processed_file("firms_ground_truth_pilot.parquet")
    enriched_path = require_processed_file("firms_satellite_enriched_pilot.parquet")
    output_dir = gt_path.parent
    output_path = output_dir / "firms_evidence_review_pilot.parquet"
    return gt_path, enriched_path, output_dir, output_path


def main():
    gt_path, enriched_path, output_dir, output_path = get_paths()

    print(f"Reading ground truth from: {gt_path}")
    print(f"Reading enriched data from: {enriched_path}")

    gt_df = pd.read_parquet(gt_path)
    enriched_df = pd.read_parquet(enriched_path)

    input_event_count = len(gt_df)
    unique_input_ids = gt_df["event_id"].nunique()

    # Deduplicate input if needed, ensuring exactly one row per event_id
    gt_dedup = gt_df.drop_duplicates(subset=["event_id"], keep="first").copy()
    enriched_dedup = enriched_df.drop_duplicates(subset=["event_id"], keep="first").copy()

    # Merge enriched features onto ground truth template on event_id
    # We select enriched columns that are not already in gt_dedup (or avoid column collision)
    collision_cols = [c for c in enriched_dedup.columns if c in gt_dedup.columns and c != "event_id"]
    enriched_features = enriched_dedup.drop(columns=collision_cols)

    evidence_df = pd.merge(gt_dedup, enriched_features, on="event_id", how="left")

    # Ensure evidence review fields are present and empty/null
    manual_review_fields = [
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

    for field in manual_review_fields:
        if field not in evidence_df.columns:
            evidence_df[field] = pd.NA

    # Keep review_status as "pending"
    evidence_df["review_status"] = "pending"

    # Enforce label fields are NULL
    for field in ["label", "label_confidence", "label_source", "label_reason",
                  "evidence_type", "evidence_url", "evidence_notes",
                  "independent_evidence", "conflicting_evidence"]:
        evidence_df[field] = pd.NA

    # Output validation metrics
    output_event_count = len(evidence_df)
    unique_output_ids = evidence_df["event_id"].nunique()
    duplicate_count = output_event_count - unique_output_ids

    gt_id_set = set(gt_dedup["event_id"])
    out_id_set = set(evidence_df["event_id"])
    missing_ids = list(gt_id_set - out_id_set)

    non_null_labels = int(evidence_df["label"].notna().sum())
    pending_count = int((evidence_df["review_status"] == "pending").sum())

    print("\n--- Evidence Review Dataset Validation ---")
    print(f"Input event count     : {input_event_count}")
    print(f"Output event count    : {output_event_count}")
    print(f"Unique event_id count : {unique_output_ids}")
    print(f"Duplicate event count : {duplicate_count}")
    print(f"Missing event IDs     : {len(missing_ids)}")
    print(f"Non-null label count  : {non_null_labels}")
    print(f"Pending review count  : {pending_count}")

    # Assertions
    assert input_event_count == output_event_count, f"Count mismatch: {input_event_count} != {output_event_count}"
    assert duplicate_count == 0, f"Found {duplicate_count} duplicate events"
    assert len(missing_ids) == 0, f"Found {len(missing_ids)} missing event IDs"
    assert non_null_labels == 0, f"Found {non_null_labels} non-null labels"
    assert pending_count == output_event_count, f"Pending count ({pending_count}) != Output count ({output_event_count})"

    # Write output Parquet
    output_dir.mkdir(parents=True, exist_ok=True)
    evidence_df.to_parquet(output_path, index=False)
    print(f"\nEvidence review dataset written to: {output_path}")

    # Verification read back
    verify_df = pd.read_parquet(output_path)
    assert len(verify_df) == output_event_count
    assert verify_df["label"].notna().sum() == 0
    assert (verify_df["review_status"] == "pending").sum() == output_event_count


if __name__ == "__main__":
    main()
