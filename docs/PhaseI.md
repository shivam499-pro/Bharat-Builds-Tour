# Phase I – FIRMS ingestion

- Load FIRMS fire‑hotspot CSVs.
- Filter by geographic bounds (India) and reasonable FRP values.
- Persist as `firms_raw.parquet`.

**Key scripts**: `scripts/ingest_firms.py`
**Outputs**: `data/firms_raw.parquet`
