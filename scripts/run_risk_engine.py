#!/usr/bin/env python3
"""
scripts/run_risk_engine.py

Execution script for Task 25:
Runs the deterministic ThermoGuard risk-scoring engine against the N=100 pilot dataset,
generates output tables and audit explanations, and prints validation metrics.
"""

from pathlib import Path
import json
import pandas as pd
import sys

# Ensure repository root is in python path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from repo_paths import require_processed_file
from risk_engine.scoring import score_event, score_dataframe, METHODOLOGY_VERSION
from risk_engine.explanation import generate_audit_explanation
from risk_engine.validation import validate_pilot_results, format_validation_report

def main():
    print(f"=== ThermoGuard Risk Engine Task 25 Execution ===")
    print(f"Methodology Version: {METHODOLOGY_VERSION}")

    data_path = require_processed_file("firms_satellite_enriched_pilot.parquet")

    print(f"Loading pilot dataset from: {data_path}")
    df_raw = pd.read_parquet(data_path)
    print(f"Loaded {len(df_raw)} records with columns: {list(df_raw.columns)[:10]}...")

    # Score all events and generate audits
    print("Executing deterministic scoring across pilot events...")
    audits = []
    for _, row in df_raw.iterrows():
        res = score_event(row.to_dict())
        audits.append(generate_audit_explanation(res))

    scored_df = score_dataframe(df_raw)
    print(f"Successfully scored {len(scored_df)} events.")

    # Validation summary
    val_metrics = validate_pilot_results(scored_df)
    report_text = format_validation_report(val_metrics)
    print("\n" + report_text + "\n")

    # Destination directories
    reports_dir = REPO_ROOT / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Save scored dataset
    parquet_out = reports_dir / "pilot_risk_scores.parquet"
    csv_out = reports_dir / "pilot_risk_scores.csv"
    scored_df.to_parquet(parquet_out, index=False)
    scored_df.to_csv(csv_out, index=False)
    print(f"Saved scored parquet to: {parquet_out}")
    print(f"Saved scored CSV to: {csv_out}")

    # Save audit explanations JSON
    audits_out = reports_dir / "pilot_risk_audit_explanations.json"
    with open(audits_out, "w", encoding="utf-8") as f:
        json.dump(audits, f, indent=2)
    print(f"Saved {len(audits)} audit records to: {audits_out}")

    # Save validation metrics JSON
    metrics_out = reports_dir / "pilot_risk_summary.json"
    with open(metrics_out, "w", encoding="utf-8") as f:
        json.dump(val_metrics, f, indent=2)
    print(f"Saved validation summary to: {metrics_out}")

    print("\nTask 25 pilot execution completed successfully.")

if __name__ == "__main__":
    main()
