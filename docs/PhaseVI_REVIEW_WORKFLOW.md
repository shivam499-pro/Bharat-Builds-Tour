# ThermoGuard Phase VI — Human Review Operational Workflow

This document details the operational protocol and lifecycle for human experts reviewing and annotating the 100 pilot events in ThermoGuard.

---

## 1. Operational Review Process

Human reviewers must follow this step-by-step workflow for each event:

```text
                  +--------------------------------+
                  |             EVENT              |
                  |     (Identified by event_id)   |
                  +---------------+----------------+
                                  |
                                  v
                  +--------------------------------+
                  |        Evidence Summary        |
                  | (firms_event_evidence_summary) |
                  +---------------+----------------+
                                  |
                                  v
                  +--------------------------------+
                  |  Reviewer Examines Evidence    |
                  +---------------+----------------+
                                  |
                                  v
                  +--------------------------------+
                  |  Check FIRMS Temporal Behavior |
                  |  (Persistence, FRP, Recurrence)|
                  +---------------+----------------+
                                  |
                                  v
                  +--------------------------------+
                  |       Check OSM Context        |
                  |  (Distance, Containment, Type) |
                  +---------------+----------------+
                                  |
                                  v
                  +--------------------------------+
                  |    Check WorldCover Context    |
                  |      (Baseline Land-Cover)     |
                  +---------------+----------------+
                                  |
                                  v
                  +--------------------------------+
                  |    Check Sentinel-2 Evidence   |
                  |  (SWIR reflectances, Indices)  |
                  +---------------+----------------+
                                  |
                                  v
                  +--------------------------------+
                  | Check Independent Evidence     |
                  | (Incident reports, External)   |
                  +---------------+----------------+
                                  |
                                  v
                  +--------------------------------+
                  |  Record Contradictory Evidence |
                  |   (Note any conflicting data)  |
                  +---------------+----------------+
                                  |
                                  v
                  +--------------------------------+
                  |     Assign Label ONLY if       |
                  |       Evidence Supports It     |
                  | (Else assign other_uncertain)  |
                  +---------------+----------------+
                                  |
                                  v
                  +--------------------------------+
                  |    Assign Evidence Confidence  |
                  |      (high, medium, low)       |
                  +---------------+----------------+
                                  |
                                  v
                  +--------------------------------+
                  | Record Label Source and Reason |
                  |    (Full rationale & sources)  |
                  +---------------+----------------+
                                  |
                                  v
                  +--------------------------------+
                  |       Set Review Status        |
                  | (reviewed/needs_more_evidence) |
                  +--------------------------------+
```

---

## 2. Required Record Schema

Each reviewed event record must populate the following standardized fields:

| Field Name | Type | Description & Population Rules |
|---|---|---|
| `event_id` | String | Unique immutable identifier matching the pilot candidate event. |
| `label` | String | Ground-truth class from the approved vocabulary (`industrial_fire`, `industrial_thermal_source`, `agricultural_burning`, `wildfire`, `mining_or_persistent_thermal`, `other_uncertain`). Remains empty if status is `pending` or `needs_more_evidence`. |
| `label_confidence` | String | Evidence strength rating: `high`, `medium`, or `low`. |
| `label_source` | String | Explicit provenance string (e.g., `human_expert:team_a`, `incident_record:state_fire_service`). |
| `label_reason` | String | Comprehensive textual justification explaining why this class was assigned. |
| `evidence_type` | String | Primary evidence category (`incident_report`, `satellite_visual`, `spatial_infrastructure`, `spectral_analysis`). |
| `evidence_url` | String | Verifiable URL, document accession number, or archive reference. |
| `evidence_notes` | String | Contextual qualitative notes (weather conditions, plume characteristics, boundary notes). |
| `independent_evidence` | Boolean/String | Flag indicating whether external independent sources corroborated the event. |
| `conflicting_evidence` | String | Explicit recording of contradictory evidence, discordant tags, or confounding land-cover context. |
| `review_status` | String | Lifecycle state: `pending`, `reviewed`, `needs_more_evidence`, or `final`. |
| `reviewed_at` | Timestamp | UTC timestamp recording when the human review action occurred. |

---

## 3. Guiding Principles & Scientific Discipline

1. **Labels are human/validated evidence decisions**: The automated pipeline does not and will never generate ground truth. All ground-truth records represent deliberate, verified human determinations.
2. **Uncertain events should remain uncertain**: If signals conflict or resolution is insufficient, label the event as `other_uncertain` or set status to `needs_more_evidence`. Never guess or assign a majority class.
3. **Evidence must be traceable**: Every label assignment must document its rationale and source so that decisions can be audited and reproduced by peer reviewers.
4. **Independent evidence is preferred**: Validations backed by independent emergency incident logs, regulatory reports, or verified ground surveys carry the highest evidential weight.
5. **Separation of label sources and model features**: Whenever practical, reviewers should prioritize independent incident sources rather than relying solely on the exact features (OSM distance, SWIR band values) that downstream ML models will use for training, preventing circular reinforcement.

---

## 4. Current State

The Phase VI pilot dataset remains completely unlabelled (`review_status = 'pending'`). No automated predictions or synthetic labels exist. Human review will proceed in accordance with this workflow document.
