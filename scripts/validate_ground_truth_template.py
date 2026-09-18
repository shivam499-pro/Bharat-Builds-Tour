import sys
from pathlib import Path
import pandas as pd

# Allowed vocabularies as per specification
ALLOWED_LABELS = {
    "industrial_fire",
    "industrial_thermal_source",
    "agricultural_burning",
    "wildfire",
    "mining_or_persistent_thermal",
    "other_uncertain",
}

ALLOWED_CONFIDENCES = {
    "high",
    "medium",
    "low",
}

ALLOWED_REVIEW_STATUSES = {
    "pending",
    "reviewed",
    "needs_more_evidence",
    "final",
}


def get_paths():
    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from repo_paths import require_processed_file

    input_path = require_processed_file("firms_satellite_enriched_pilot.parquet")
    output_path = require_processed_file("firms_ground_truth_pilot.parquet")
    return input_path, output_path


def validate():
    input_path, output_path = get_paths()
    print(f"Reading input dataset from : {input_path}")
    print(f"Reading output dataset from: {output_path}")

    input_df = pd.read_parquet(input_path)
    output_df = pd.read_parquet(output_path)

    results = []

    # 1. Structural integrity: event_id exists
    cond_id_exists = "event_id" in output_df.columns
    results.append(("event_id exists", cond_id_exists, f"Columns: {output_df.columns.tolist()}"))
    if not cond_id_exists:
        raise AssertionError("Check failed: 'event_id' column is missing from output dataset.")

    # 2. Structural integrity: event_id is unique (Duplicate event_id must FAIL validation)
    total_output_rows = len(output_df)
    unique_output_ids = output_df["event_id"].nunique()
    duplicate_count = total_output_rows - unique_output_ids
    cond_id_unique = (duplicate_count == 0)
    results.append(("event_id is unique (no duplicate event records)", cond_id_unique, f"Unique IDs: {unique_output_ids}, Total rows: {total_output_rows}"))
    if not cond_id_unique:
        raise AssertionError(f"Check failed: {duplicate_count} duplicate event_ids found.")

    # 3. Structural integrity: Event count must remain unchanged
    input_event_count = input_df["event_id"].nunique()
    cond_count_equal = (input_event_count == total_output_rows)
    results.append(("Event count remains unchanged", cond_count_equal, f"Input events: {input_event_count}, Output events: {total_output_rows}"))
    if not cond_count_equal:
        raise AssertionError(f"Check failed: Input event count ({input_event_count}) != Output event count ({total_output_rows}).")

    # 4. No input event_id lost and no new event_id created
    input_ids_set = set(input_df["event_id"])
    output_ids_set = set(output_df["event_id"])
    lost_ids = input_ids_set - output_ids_set
    new_ids = output_ids_set - input_ids_set
    cond_id_consistency = (len(lost_ids) == 0 and len(new_ids) == 0)
    results.append(("Event ID consistency (no lost or new event_ids)", cond_id_consistency, f"Lost: {len(lost_ids)}, New: {len(new_ids)}"))
    if not cond_id_consistency:
        raise AssertionError(f"Check failed: {len(lost_ids)} lost IDs, {len(new_ids)} new IDs.")

    # Helper masks for populated vs null values
    label_series = output_df["label"] if "label" in output_df.columns else pd.Series([None] * total_output_rows)
    is_label_populated = label_series.notna() & (label_series.astype(str).str.strip() != "") & (label_series.astype(str).str.lower() != "<na>") & (label_series.astype(str).str.lower() != "none")
    is_label_null = ~is_label_populated
    populated_label_count = int(is_label_populated.sum())

    conf_series = output_df["label_confidence"] if "label_confidence" in output_df.columns else pd.Series([None] * total_output_rows)
    is_conf_populated = conf_series.notna() & (conf_series.astype(str).str.strip() != "") & (conf_series.astype(str).str.lower() != "<na>") & (conf_series.astype(str).str.lower() != "none")

    source_series = output_df["label_source"] if "label_source" in output_df.columns else pd.Series([None] * total_output_rows)
    is_source_populated = source_series.notna() & (source_series.astype(str).str.strip() != "") & (source_series.astype(str).str.lower() != "<na>") & (source_series.astype(str).str.lower() != "none")

    reason_series = output_df["label_reason"] if "label_reason" in output_df.columns else pd.Series([None] * total_output_rows)
    is_reason_populated = reason_series.notna() & (reason_series.astype(str).str.strip() != "") & (reason_series.astype(str).str.lower() != "<na>") & (reason_series.astype(str).str.lower() != "none")

    # Rule 9: Invalid review_status values must FAIL validation
    invalid_status_mask = ~output_df["review_status"].isin(ALLOWED_REVIEW_STATUSES)
    invalid_status_count = int(invalid_status_mask.sum())
    cond_valid_status = (invalid_status_count == 0)
    results.append(("review_status contains ONLY allowed values", cond_valid_status, f"Allowed: {sorted(ALLOWED_REVIEW_STATUSES)}, Violations: {invalid_status_count}"))
    if not cond_valid_status:
        invalid_statuses = output_df.loc[invalid_status_mask, "review_status"].unique().tolist()
        raise AssertionError(f"Rule 9 failed: Invalid review_status values found: {invalid_statuses}")

    # Rule 1: label may be NULL only when review_status = 'pending' or 'needs_more_evidence'
    invalid_null_label_mask = is_label_null & (~output_df["review_status"].isin(["pending", "needs_more_evidence"]))
    invalid_null_label_count = int(invalid_null_label_mask.sum())
    cond_rule1 = (invalid_null_label_count == 0)
    results.append(("label NULL only when status is 'pending' or 'needs_more_evidence'", cond_rule1, f"Violations: {invalid_null_label_count}"))
    if not cond_rule1:
        raise AssertionError(f"Rule 1 failed: {invalid_null_label_count} records have NULL label with invalid status.")

    # Rule 2: A populated label MUST belong to the allowed label vocabulary
    invalid_labels = output_df.loc[is_label_populated & (~label_series.isin(ALLOWED_LABELS)), "label"].unique().tolist()
    cond_rule2 = (len(invalid_labels) == 0)
    results.append(("Populated labels belong to allowed vocabulary", cond_rule2, f"Allowed: {sorted(ALLOWED_LABELS)}, Invalid found: {invalid_labels}"))
    if not cond_rule2:
        raise AssertionError(f"Rule 2 failed: Unrecognized labels found: {invalid_labels}")

    # Rule 3: A populated label MUST have label_confidence
    missing_conf_for_label = int((is_label_populated & (~is_conf_populated)).sum())
    cond_rule3 = (missing_conf_for_label == 0)
    results.append(("Populated label MUST have label_confidence", cond_rule3, f"Missing confidence count: {missing_conf_for_label}"))
    if not cond_rule3:
        raise AssertionError(f"Rule 3 failed: {missing_conf_for_label} records have populated label but missing label_confidence.")

    # Rule 4: A populated label MUST have label_source
    missing_source_for_label = int((is_label_populated & (~is_source_populated)).sum())
    cond_rule4 = (missing_source_for_label == 0)
    results.append(("Populated label MUST have label_source", cond_rule4, f"Missing source count: {missing_source_for_label}"))
    if not cond_rule4:
        raise AssertionError(f"Rule 4 failed: {missing_source_for_label} records have populated label but missing label_source.")

    # Rule 5: A populated label MUST have label_reason
    missing_reason_for_label = int((is_label_populated & (~is_reason_populated)).sum())
    cond_rule5 = (missing_reason_for_label == 0)
    results.append(("Populated label MUST have label_reason", cond_rule5, f"Missing reason count: {missing_reason_for_label}"))
    if not cond_rule5:
        raise AssertionError(f"Rule 5 failed: {missing_reason_for_label} records have populated label but missing label_reason.")

    # Rule 6: 'reviewed' or 'final' records MUST have a populated label
    reviewed_or_final_mask = output_df["review_status"].isin(["reviewed", "final"])
    reviewed_missing_label = int((reviewed_or_final_mask & is_label_null).sum())
    cond_rule6 = (reviewed_missing_label == 0)
    results.append(("'reviewed' or 'final' records MUST have a populated label", cond_rule6, f"Missing label count: {reviewed_missing_label}"))
    if not cond_rule6:
        raise AssertionError(f"Rule 6 failed: {reviewed_missing_label} 'reviewed'/'final' records lack a populated label.")

    # Rule 7: 'final' records MUST have label_confidence, label_source, and label_reason
    final_mask = output_df["review_status"] == "final"
    final_missing_metadata = int((final_mask & ((~is_conf_populated) | (~is_source_populated) | (~is_reason_populated))).sum())
    cond_rule7 = (final_missing_metadata == 0)
    results.append(("'final' records MUST have label_confidence, label_source, and label_reason", cond_rule7, f"Missing metadata count: {final_missing_metadata}"))
    if not cond_rule7:
        raise AssertionError(f"Rule 7 failed: {final_missing_metadata} 'final' records missing required metadata.")

    # Rule 8: Invalid confidence values must FAIL validation
    invalid_confs = output_df.loc[is_conf_populated & (~conf_series.isin(ALLOWED_CONFIDENCES)), "label_confidence"].unique().tolist()
    cond_rule8 = (len(invalid_confs) == 0)
    results.append(("Confidence values belong to allowed set", cond_rule8, f"Allowed: {sorted(ALLOWED_CONFIDENCES)}, Invalid found: {invalid_confs}"))
    if not cond_rule8:
        raise AssertionError(f"Rule 8 failed: Invalid confidence values found: {invalid_confs}")

    # Rule 12: sampling_stratum MUST NEVER be used as label automatically
    if "sampling_stratum" in output_df.columns:
        stratum_as_label_mask = is_label_populated & (output_df["label"].astype(str) == output_df["sampling_stratum"].astype(str))
        stratum_as_label_count = int(stratum_as_label_mask.sum())
    else:
        stratum_as_label_count = 0
    cond_rule12 = (stratum_as_label_count == 0)
    results.append(("sampling_stratum NEVER copied into label", cond_rule12, f"Direct copies detected: {stratum_as_label_count}"))
    if not cond_rule12:
        raise AssertionError(f"Rule 12 failed: sampling_stratum copied into label for {stratum_as_label_count} records.")

    pending_count = int((output_df["review_status"] == "pending").sum())

    print("\n--- Validation Check Results ---")
    for name, passed, detail in results:
        status_str = "PASS" if passed else "FAIL"
        print(f"[{status_str}] {name} ({detail})")

    print("\n--- Summary Metrics ---")
    print(f"Total events               : {total_output_rows}")
    print(f"Duplicate count            : {duplicate_count}")
    print(f"Current populated labels   : {populated_label_count}")
    print(f"Current pending count      : {pending_count}")
    print("\nVALIDATION PASSED SUCCESSFULLY.")

    return results, populated_label_count, pending_count


if __name__ == "__main__":
    try:
        validate()
    except Exception as e:
        print(f"\nVALIDATION ERROR: {e}", file=sys.stderr)
        sys.exit(1)
