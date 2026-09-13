# Phase I – FIRMS ingestion

- Load FIRMS fire‑hotspot CSVs.
- Filter by geographic bounds (India) and reasonable FRP.
- Persist as `firms_raw.parquet`.

**Key scripts**: `scripts/ingest_firms.py`

**Outputs**: `data/firms_raw.parquet`

---

# Phase II – WorldCover enrichment

- Join FIRMS points to ESA WorldCover raster.
- Assign land‑cover class (`worldcover_class`, `worldcover_class_name`).
- Compute simple spatial statistics (e.g., pixel count per class).

**Key scripts**: `scripts/join_worldcover.py`

**Outputs**: `data/firms_worldcover_enriched.parquet`

---

# Phase III – OSM contextualisation

- Load OSM extracts (building, road, land‑use layers).
- For each FIRMS point compute:
  - `osm_matched_fraction`
  - `osm_containment_fraction`
  - `osm_proximity_fraction`
  - `min_distance_m`
- Tag primary OSM category and tier.

**Key scripts**: `scripts/join_osm.py`

**Outputs**: `data/firms_osm_enriched.parquet`

---

# Phase IV – Persistence & quality checks

- Consolidate all previous joins into a single Parquet table.
- Perform sanity checks (duplicate removal, temporal consistency).
- Store as `firms_persistent_events_worldcover.parquet`.

**Key scripts**: `scripts/persist_events.py`

**Outputs**: `data/firms_persistent_events_worldcover.parquet`

---

# Phase V – Sentinel‑2 / Landsat feature extraction (pilot)

- **Pilot design**: 100 stratified events (40 industrial, 30 agricultural, 30 forest).
- Query AWS Element84 STAC for Sentinel‑2 L2A COGs within a 7‑day window.
- Extract band means (B02‑B12) and compute spectral indices:
  - NDVI, NBR, NBR2, BSI, SWIR₂ / SWIR₁ ratio.
- Record ancillary metadata:
  - `satellite_scene_id`, `satellite_acq_datetime`, `satellite_cloud_cover_scene`
  - Temporal delta, SCL clear/cloud fractions.
- **Result**: `firms_satellite_enriched_pilot.parquet`
  - **89 events** have all required spectral features.
  - **11 events** lack a clear scene and are excluded from feature‑based analysis.
- **Ground‑truth labels** are not yet available; supervised classification is deferred.

**Key scripts**:
- `scripts/target_satellite_candidates.py`
- `scripts/enrich_satellite_features.py`
- `analysis/baseline_feature_analysis.py`

**Outputs**: `data/satellite/processed/firms_satellite_enriched_pilot.parquet`
