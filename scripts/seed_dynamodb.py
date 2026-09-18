#!/usr/bin/env python3
"""Seed ThermoGuardEvents (ap-south-1) from frozen pilot reports.

Table must already exist: partition key event_id (S).
Run from AWS CloudShell (signed-in) — only boto3 is required (preinstalled).
"""

from __future__ import annotations

import csv
import json
import os
from decimal import Decimal
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

REPO_ROOT = Path(__file__).resolve().parent.parent
TABLE_NAME = os.environ.get("THERMOGUARD_DDB_TABLE", "ThermoGuardEvents")
REGION = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "ap-south-1"

FLOAT_FIELDS = {
    "risk_score",
    "evidence_confidence",
    "thermal_dimension_score",
    "persistence_dimension_score",
    "industrial_dimension_score",
    "spatial_dimension_score",
    "spectral_dimension_score",
}


def to_num(raw: str) -> Decimal:
    return Decimal(str(round(float(raw), 6)))


def main() -> int:
    csv_path = REPO_ROOT / "reports" / "pilot_risk_scores.csv"
    expl_path = REPO_ROOT / "reports" / "task28_explanations.json"
    if not csv_path.is_file() or not expl_path.is_file():
        print("Missing reports/pilot_risk_scores.csv or reports/task28_explanations.json")
        return 1

    with expl_path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    explanations = {row["event_id"]: row for row in payload.get("explanations", [])}

    ddb = boto3.resource("dynamodb", region_name=REGION)
    table = ddb.Table(TABLE_NAME)
    table.load()
    print(f"Table {TABLE_NAME} status={table.table_status} region={REGION}")

    written = 0
    with csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        with table.batch_writer() as batch:
            for row in reader:
                event_id = (row.get("event_id") or "").strip()
                if not event_id:
                    continue
                expl = explanations.get(event_id, {})
                primary = ((expl.get("contribution_ranking") or {}).get("primary_driver") or {})
                priority = expl.get("investigation_priority") or {}
                item = {
                    "event_id": event_id,
                    "risk_score": to_num(row["risk_score"]),
                    "risk_tier": row.get("risk_tier") or None,
                    "evidence_confidence": to_num(row["evidence_confidence"]),
                    "confidence_tier": row.get("confidence_tier") or None,
                    "thermal_dimension_score": to_num(row["thermal_dimension_score"]),
                    "persistence_dimension_score": to_num(row["persistence_dimension_score"]),
                    "industrial_dimension_score": to_num(row["industrial_dimension_score"]),
                    "spatial_dimension_score": to_num(row["spatial_dimension_score"]),
                    "spectral_dimension_score": to_num(row["spectral_dimension_score"]),
                    "worldcover_class_name": row.get("worldcover_class_name") or None,
                    "osm_primary_category": row.get("osm_primary_category") or None,
                    "missing_evidence": row.get("missing_evidence") or None,
                    "methodology_version": row.get("methodology_version") or None,
                    "primary_driver": primary.get("name"),
                    "investigation_recommendation": priority.get("recommendation"),
                    "explanation_json": json.dumps(expl, ensure_ascii=True),
                }
                item = {k: v for k, v in item.items() if v not in (None, "")}
                batch.put_item(Item=item)
                written += 1

    count = table.item_count
    print(f"Wrote {written} items.")
    print(f"Table item_count (may lag a few seconds): {count}")
    print("DynamoDB → Tables → ThermoGuardEvents → Explore table items → Scan → Run")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ClientError as exc:
        print("AWS error:", exc)
        print("Open CloudShell while signed in, region ap-south-1.")
        raise SystemExit(1)
