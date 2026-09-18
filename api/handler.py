"""ThermoGuard demo API — read-only DynamoDB.

GET /events
GET /events/{id}

Does not recompute risk scores.
"""

from __future__ import annotations

import json
import os
from decimal import Decimal
from typing import Any

import boto3

TABLE_NAME = os.environ.get("TABLE_NAME", "ThermoGuardEvents")
REGION = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "ap-south-1"

_table = None

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "content-type",
    "Access-Control-Allow-Methods": "GET,OPTIONS",
    "Content-Type": "application/json",
}

LIST_FIELDS = (
    "event_id",
    "risk_score",
    "risk_tier",
    "evidence_confidence",
    "confidence_tier",
    "worldcover_class_name",
    "osm_primary_category",
    "primary_driver",
    "investigation_recommendation",
    "lat",
    "lon",
)


class DecimalEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)


def table():
    global _table
    if _table is None:
        _table = boto3.resource("dynamodb", region_name=REGION).Table(TABLE_NAME)
    return _table


def respond(status: int, body: Any) -> dict:
    return {
        "statusCode": status,
        "headers": CORS,
        "body": json.dumps(body, cls=DecimalEncoder, ensure_ascii=True),
    }


def route(event: dict) -> tuple[str, str]:
    http = (event.get("requestContext") or {}).get("http") or {}
    method = http.get("method") or event.get("httpMethod") or "GET"
    path = event.get("rawPath") or event.get("path") or "/"
    params = event.get("pathParameters") or {}
    event_id = params.get("id") or params.get("event_id")
    if event_id:
        return method, f"/events/{event_id}"
    trimmed = path.rstrip("/")
    if trimmed.endswith("/events"):
        return method, "/events"
    parts = [p for p in trimmed.split("/") if p]
    if len(parts) >= 2 and parts[-2] == "events":
        return method, f"/events/{parts[-1]}"
    if parts and parts[-1] == "events":
        return method, "/events"
    return method, trimmed or "/"


def list_events() -> dict:
    items = []
    response = table().scan()
    items.extend(response.get("Items") or [])
    while response.get("LastEvaluatedKey"):
        response = table().scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items") or [])

    summaries = []
    for item in items:
        summaries.append({k: item.get(k) for k in LIST_FIELDS if k in item})
    summaries.sort(key=lambda row: float(row.get("risk_score") or 0), reverse=True)
    return {"count": len(summaries), "events": summaries}


def get_event(event_id: str) -> dict:
    result = table().get_item(Key={"event_id": event_id})
    item = result.get("Item")
    if not item:
        return respond(404, {"error": "event not found", "event_id": event_id})
    expl_raw = item.get("explanation_json")
    if isinstance(expl_raw, str) and expl_raw:
        try:
            item["explanation"] = json.loads(expl_raw)
        except json.JSONDecodeError:
            item["explanation"] = None
    else:
        item["explanation"] = None
    item.pop("explanation_json", None)
    return respond(200, item)


def lambda_handler(event, _context):
    method, path = route(event)
    if method == "OPTIONS":
        return respond(200, {"ok": True})
    if method != "GET":
        return respond(405, {"error": "method not allowed"})
    if path == "/events" or path == "/api/events":
        return respond(200, list_events())
    if path.startswith("/events/") or path.startswith("/api/events/"):
        event_id = path.rsplit("/", 1)[-1]
        return get_event(event_id)
    if path in ("/", "/health", "/api/health"):
        return respond(200, {"ok": True, "service": "thermoguard", "table": TABLE_NAME})
    return respond(404, {"error": "not found", "path": path})
