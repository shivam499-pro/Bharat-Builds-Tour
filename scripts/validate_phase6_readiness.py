import sys
from pathlib import Path
import pandas as pd


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


def find_file(filename):
    import sys
    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from repo_paths import find_processed_file

    return find_processed_file(filename)


def main():
    print("==================================================")
    print("THERMOGUARD - PHASE VI READINESS VALIDATION")
    print("==================================================\n")

    results = []

    # Check 1: Ground-truth template exists
    gt_path = find_file("firms_ground_truth_pilot.parquet")
    cond1 = gt_path is not None and gt_path.exists()
    results.append(("1. Ground-truth template exists", cond1, str(gt_path) if cond1 else "File missing"))

    # Check 2: Evidence-review dataset exists
    ev_path = find_file("firms_evidence_review_pilot.parquet")
    cond2 = ev_path is not None and ev_path.exists()
    results.append(("2. Evidence-review dataset exists", cond2, str(ev_path) if cond2 else "File missing"))

    # Check 3: Evidence-summary CSV exists
    sum_path = find_file("firms_event_evidence_summary_pilot.csv")
    cond3 = sum_path is not None and sum_path.exists()
    results.append(("3. Evidence-summary CSV exists", cond3, str(sum_path) if cond3 else "File missing"))

    if not (cond1 and cond2 and cond3):
        print("CRITICAL: One or more prerequisite files are missing.")
        for name, passed, detail in results:
            print(f"[{'PASS' if passed else 'FAIL'}] {name}: {detail}")
        sys.exit(1)

    # Load datasets
    gt_df = pd.read_parquet(gt_path)
    ev_df = pd.read_parquet(ev_path)
    sum_df = pd.read_csv(sum_path, keep_default_na=False)

    # Check 4: Required review columns exist
    required_review_cols = [
        "event_id",
        "label",
        "label_confidence",
        "label_source",
        "label_reason",
        "review_status",
    ]
    missing_gt_cols = [c for c in required_review_cols if c not in gt_df.columns]
    missing_ev_cols = [c for c in required_review_cols if c not in ev_df.columns]
    missing_sum_cols = [c for c in required_review_cols if c not in sum_df.columns]
    cond4 = len(missing_gt_cols) == 0 and len(missing_ev_cols) == 0 and len(missing_sum_cols) == 0
    results.append(("4. Required review columns exist across datasets", cond4, f"GT missing: {missing_gt_cols}, EV missing: {missing_ev_cols}, Summary missing: {missing_sum_cols}"))

    # Check 5: event_id is unique
    gt_unique = gt_df["event_id"].nunique() == len(gt_df)
    ev_unique = ev_df["event_id"].nunique() == len(ev_df)
    sum_unique = sum_df["event_id"].nunique() == len(sum_df)
    cond5 = gt_unique and ev_unique and sum_unique
    results.append(("5. event_id is unique across all datasets", cond5, f"GT: {gt_unique}, EV: {ev_unique}, Summary: {sum_unique}"))

    # Check 6: Event count is preserved
    expected_count = 100
    cond6 = (len(gt_df) == expected_count) and (len(ev_df) == expected_count) and (len(sum_df) == expected_count)
    results.append(("6. Event count is preserved (exactly 100 events)", cond6, f"GT: {len(gt_df)}, EV: {len(ev_df)}, Summary: {len(sum_df)}"))

    # Check 7: Current label count is zero
    gt_non_null_label = int(gt_df["label"].notna().sum())
    ev_non_null_label = int(ev_df["label"].notna().sum())
    sum_non_null_label = int((sum_df["label"].astype(str).str.strip() != "").sum())
    cond7 = (gt_non_null_label == 0) and (ev_non_null_label == 0) and (sum_non_null_label == 0)
    results.append(("7. Current label count is zero", cond7, f"GT: {gt_non_null_label}, EV: {ev_non_null_label}, Summary: {sum_non_null_label}"))

    # Check 8: Current review_status values are only "pending"
    gt_pending = (gt_df["review_status"] == "pending").sum() == len(gt_df)
    ev_pending = (ev_df["review_status"] == "pending").sum() == len(ev_df)
    sum_pending = (sum_df["review_status"] == "pending").sum() == len(sum_df)
    cond8 = gt_pending and ev_pending and sum_pending
    results.append(("8. Current review_status values are ONLY 'pending'", cond8, f"GT: {gt_pending}, EV: {ev_pending}, Summary: {sum_pending}"))

    # Check 9: No invalid label values exist
    populated_labels = []
    for d in [gt_df, ev_df]:
        s = d["label"].dropna()
        populated_labels.extend([v for v in s if str(v).strip() != "" and str(v).lower() != "none" and str(v).lower() != "<na>"])
    populated_labels.extend([v for v in sum_df["label"] if str(v).strip() != ""])
    invalid_labels = [l for l in populated_labels if l not in ALLOWED_LABELS]
    cond9 = len(invalid_labels) == 0
    results.append(("9. No invalid label values exist", cond9, f"Invalid labels found: {invalid_labels}"))

    # Check 10: No invalid confidence values exist
    populated_confs = []
    for d in [gt_df, ev_df]:
        s = d["label_confidence"].dropna()
        populated_confs.extend([v for v in s if str(v).strip() != "" and str(v).lower() != "none" and str(v).lower() != "<na>"])
    populated_confs.extend([v for v in sum_df["label_confidence"] if str(v).strip() != ""])
    invalid_confs = [c for c in populated_confs if c not in ALLOWED_CONFIDENCES]
    cond10 = len(invalid_confs) == 0
    results.append(("10. No invalid confidence values exist", cond10, f"Invalid confidence found: {invalid_confs}"))

    # Check 11: sampling_stratum has not been copied into label
    stratum_copied = 0
    for d in [gt_df, ev_df]:
        if "sampling_stratum" in d.columns and "label" in d.columns:
            stratum_copied += int((d["label"].notna() & (d["label"] == d["sampling_stratum"])).sum())
    if "sampling_stratum" in sum_df.columns and "label" in sum_df.columns:
        stratum_copied += int(((sum_df["label"].str.strip() != "") & (sum_df["label"] == sum_df["sampling_stratum"])).sum())
    cond11 = (stratum_copied == 0) and cond7
    results.append(("11. sampling_stratum has NOT been copied into label", cond11, f"Direct matches detected: {stratum_copied}"))

    # Check 12: No duplicate event IDs exist
    gt_dup = len(gt_df) - gt_df["event_id"].nunique()
    ev_dup = len(ev_df) - ev_df["event_id"].nunique()
    sum_dup = len(sum_df) - sum_df["event_id"].nunique()
    cond12 = (gt_dup == 0) and (ev_dup == 0) and (sum_dup == 0)
    results.append(("12. No duplicate event IDs exist", cond12, f"Duplicates: GT={gt_dup}, EV={ev_dup}, Summary={sum_dup}"))

    # Print results
    print("--- Detailed Check Results ---")
    all_passed = True
    for name, passed, detail in results:
        status_str = "PASS" if passed else "FAIL"
        if not passed:
            all_passed = False
        print(f"[{status_str}] {name} ({detail})")

    print("\n--------------------------------------------------")
    print(f"OVERALL READINESS RESULT: {'PASS' if all_passed else 'FAIL'}")
    print("--------------------------------------------------")

    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
