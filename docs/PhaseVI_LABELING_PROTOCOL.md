# ThermoGuard Phase VI-B — Formal Human Labeling Protocol

This scientific labeling protocol defines the rigorous operational and evidential standards required for human experts to review and assign ground-truth labels to thermal anomaly events in the ThermoGuard 100-event pilot dataset.

---

## 1. Universal Evidence Check Requirements

For every event evaluated, human reviewers must inspect the complete multi-source evidence bundle before considering any label assignment:
1. **Event Identity & Coordinates**: Unique `event_id`, latitude, longitude, and geographic positioning on high-resolution basemaps.
2. **FIRMS Satellite Detection Profiles**: Clustered detection counts, first/last detection timestamps, temporal duration, day/night pass distribution, FRP statistics, and multi-sensor consistency.
3. **OpenStreetMap (OSM) Infrastructure Context**: Proximity to industrial facilities (`min_distance_m`), spatial containment within facility boundaries, specific facility tag taxonomy (`osm_primary_category`, `osm_sub_category`), and surrounding land-use polygons.
4. **ESA WorldCover 10m Baseline**: Baseline land-cover classification (`worldcover_class_name`), surrounding landscape heterogeneity, and spatial congruence.
5. **Sentinel-2 Multi-Spectral Indices & COG Imagery**: S2 scene availability, cloud/shadow masks (`scl_clear_fraction`, `scl_cloud_fraction`), visible/NIR/SWIR band reflectances (B02–B12), spectral indices (NDVI, NBR, NBR2, BSI), SWIR anomaly ratio, and temporal delta relative to the FIRMS detection.
6. **Independent External Evidence**: Independent incident databases, emergency dispatch logs, regulatory notices, and verifiable local news reports.
7. **Contradictory Signals**: Any discordant evidence between spatial infrastructure, land-cover classification, spectral signatures, or temporal persistence.

---

## 2. FIRMS Evidence Rules

- **Multi-Day Persistence**: Continuous detections spanning multiple consecutive weeks or months strongly indicate fixed, stationary operational heat sources (e.g., flare stacks, kilns, smelters) or persistent coal seam fires, rather than rapid accidental fires or crop residue burns.
- **Single-Day / Ephemeral Detections**: Events lasting < 48 hours with high FRP and localized spatial footprints represent transient fires (crop burning, brief wildfires, or sudden industrial structure fires).
- **Diurnal Signature**: Detections occurring exclusively during mid-day passes in agricultural seasons strongly correlate with open burning; continuous 24-hour detections indicate stationary industrial or mining combustion.
- **Multi-Sensor Corroboration**: Corroboration across multiple sensors (MODIS Terra/Aqua, VIIRS S-NPP/NOAA-20) increases spatial and temporal reliability, ruling out single-pass instrument glint or solar reflection anomalies.

---

## 3. OSM Infrastructure Evidence Rules

- **Proximity Alone is Insufficient**: Proximity to an industrial OSM feature alone **MUST NOT** be sufficient to label an event as industrial. Thermal anomalies located near or adjacent to industrial zones frequently stem from adjacent agricultural clearing, waste burning, or dry grass fires.
- **Spatial Containment**: Centroid containment directly within a verified industrial facility boundary (`min_distance_m = 0` and `osm_containment_fraction > 0`) provides necessary, but not standalone, corroboration.
- **Infrastructure Relevance**: Facility type must be technologically evaluated. A high-heat facility (foundry, kiln, flare, boiler) suggests routine thermal operation, whereas an unheated warehouse indicates an accidental fire if an active fire incident is confirmed.
- **OSM Tagging Latency**: OSM data may be outdated or imprecise; reviewers must cross-verify OSM polygon footprints against optical satellite basemaps.

---

## 4. ESA WorldCover Contextual Evidence Rules

- **Contextual Baseline Only**: WorldCover provides a 10-meter resolution snapshot of baseline land cover, not real-time event status.
- **Cropland vs. Built-up**: While `Cropland` suggests agricultural residue burning, rural kilns and processing sheds are frequently embedded in agricultural fields.
- **Tree Cover vs. Open Land**: Detections in `Tree cover` suggest wildfires, but small-scale charcoal kilns, timber yards, or clearing fires occur within forest boundaries.
- **Resolution Limits**: Sub-pixel industrial sites surrounded by vegetation may be misclassified as cropland or grassland in global land-cover rasters.

---

## 5. Sentinel-2 Spectral & Visual Evidence Rules

- **Optical/SWIR vs. Direct Thermal**: Sentinel-2 provides multi-spectral reflectance (visible, NIR, SWIR), **NOT** direct radiant temperature measurements.
- **SWIR Anomaly Signatures**: High B11/B12 reflectances, elevated SWIR2/SWIR1 ratio, and SWIR anomaly ratios (> 1.5) indicate sub-pixel high-temperature combustion or highly reflective dry surfaces.
- **Burn Scar Indicators**: Reductions in post-event NBR (Normalized Burn Ratio) and NDVI paired with increases in BSI (Bare Soil Index) provide physical evidence of surface scar formation.
- **Cloud Mask Verification**: Always verify `scl_clear_fraction` and `scl_cloud_fraction`. Cloud cover or cloud shadows completely invalidate optical spectral indices.
- **Temporal Alignment**: Ensure `temporal_delta_days` between the FIRMS cluster and the Sentinel-2 acquisition pass is small (ideally within 1–5 days) to ensure spectral observations reflect the thermal event.

---

## 6. Independent Evidence Requirements

- **External Origin**: Independent evidence should originate from sources outside the model feature set (e.g., local fire service emergency response logs, official industrial safety audit registers, state disaster management bulletins, or verified ground surveys).
- **Strict Verifiability**: Every referenced source must have a concrete accession record, URL, or formal document identifier recorded in `evidence_url` and `label_source`.
- **Zero Fabrication**: Reviewers must **NEVER** invent sources, fabricate citations, or assume hypothetical news coverage.

---

## 7. Contradictory Evidence Handling

- **Mandatory Documentation**: Reviewers must explicitly detail all discordant signals in the `conflicting_evidence` field.
- **Examples of Conflicts**:
  - Event centroid is within 50m of an industrial facility, but ESA WorldCover indicates dense cropland and temporal pattern aligns exactly with regional paddy harvesting dates.
  - S2 SWIR anomaly is elevated, but optical bands indicate dry barren white limestone quarries rather than combustion smoke plumes.
- **Impact on Classification**: If conflicting evidence cannot be reconciled through independent verification, the reviewer must assign `other_uncertain` or leave the status as `needs_more_evidence`.

---

## 8. Distinguishing `industrial_fire` vs. `industrial_thermal_source`

- `industrial_fire`: Uncontrolled, unintended, accidental structural or chemical fires occurring within industrial, commercial, manufacturing, or warehousing properties. Characterized by sudden onset, transient duration (hours to days), severe localized damage or smoke plume, and documented emergency response.
- `industrial_thermal_source`: Routine, permitted operational thermal emissions. Characterized by multi-week or year-round recurrence, stationary chimney/flare/kiln structures, stable FRP signatures, and absence of emergency response.

---

## 9. Distinguishing `wildfire` vs. `agricultural_burning`

- `wildfire`: Uncontrolled wildland fire consuming natural vegetation (forest canopy, scrubland, natural grassland) across unmanaged terrain. Characterized by irregular, topography-driven spreading perimeters, elevated duration, and absence of agricultural plot boundaries.
- `agricultural_burning`: Deliberate post-harvest crop residue or stubble burning. Characterized by rectilinear plot boundaries, strict alignment with harvest seasonal calendars (e.g., Punjab/Haryana paddy burning windows), and rapid single-day burn duration.

---

## 10. When `mining_or_persistent_thermal` is Appropriate

- Applicable to continuous or recurring thermal anomalies occurring within open-cast coal mines, subsurface coal seam fires (e.g., Jharia coalfield), burning mine tailings, slag heaps, or active rock quarry processing plants.
- Evidenced by long-term spatial persistence directly co-located with open-pit mining excavations on satellite basemaps.

---

## 11. When to Use `other_uncertain`

Reviewers must assign `other_uncertain` whenever:
- Evidence is contradictory and cannot be reconciled.
- Available satellite scenes are entirely obscured by clouds or missing.
- Spatial context is ambiguous (e.g., edge of village, mixed scrap heap, roadside burning).
- The reviewer cannot reach high or medium certainty based on existing facts.
- **Reviewers must never guess or force a category to inflate dataset volume.**

---

## 12. Confidence Rating Rules

- **`high`**: Supported by verified independent documentation (fire report, news bulletin, government register) OR definitive visual corroboration across multiple independent satellite sources without contradictory signals.
- **`medium`**: Strong, consistent circumstantial alignment across multiple independent datasets (e.g., clear OSM containment within known brick kiln + high multi-week persistence + consistent SWIR anomaly), but lacking an external incident report.
- **`low`**: Supported by plausible but sparse evidence, or where minor unresolved spatial/temporal ambiguities persist.

---

## 13. Review Status Lifecycle Rules

- `pending`: Unreviewed event; all label fields must remain strictly NULL.
- `reviewed`: Preliminary evaluation complete by first reviewer; provisional label assigned, pending second-party quality check.
- `needs_more_evidence`: Evaluated, but current evidence is inadequate or cloudy; queued for higher-resolution imagery or archival records.
- `final`: Fully corroborated, independently validated, and signed off; ready for model evaluation reference.

---

## 14. Rules Preventing Confirmation Bias

- Reviewers must not start with an assumed label based on the candidate pool or sample group.
- Reviewers must systematically review evidence in order from external facts to context, actively seeking counter-evidence.
- Confirmation bias is strictly prevented by mandating the completion of `conflicting_evidence` for every non-trivial event.

---

## 15. Rules Preventing Data Leakage

- **Label Independence**: The ground-truth label must never be informed by automated predictions, model scores, or cluster outputs.
- **Feature Separation**: Review comments, notes, and rationales must never be exposed as input features to machine learning algorithms.
- **Validation Holdout**: Future model validation must apply strict spatial and temporal holdouts to prevent spatial autocorrelation leakage.

---

## 16. Minimum Evidence Required Before Assigning a Final Label

A label may transition to `final` **ONLY** if:
1. At least two independent, corroborating evidence sources are documented.
2. Contradictory evidence has been actively assessed and recorded as resolved or non-existent.
3. Both `label_reason` and `label_source` are fully articulated.
4. Confidence is determined to be at least `medium` or `high`. (Events with persistent low confidence or unreconciled conflicts must remain `other_uncertain` or `needs_more_evidence`).

---

## 17. Explicit Examples of Evidence Insufficient By Itself

The following single observations **MUST NEVER** be used in isolation to assign a label:
- *OSM distance = 0 m alone* does not prove an industrial fire.
- *ESA WorldCover = Cropland alone* does not prove agricultural residue burning.
- *ESA WorldCover = Tree cover alone* does not prove a wildfire.
- *High SWIR2/SWIR1 ratio alone* does not prove a flare stack.
- *Multi-day FIRMS persistence alone* does not prove an industrial source.
- *`sampling_stratum` alone* MUST NEVER be used as a ground-truth label.

---

## Important Scientific Directives

> **"Proximity to an industrial OSM feature alone MUST NOT be sufficient to label an event as industrial."**

> **"sampling_stratum is a sampling design field only and MUST NEVER be used as a ground-truth label."**

---

## Do Not Claim

Reviewers and downstream authors must adhere strictly to these scientific reporting boundaries:
- **NO ACCURACY CLAIMS**: Do not report model accuracy prior to completing human ground-truth validation.
- **NO PRECISION / RECALL CLAIMS**: Precision, recall, and F1 metrics are invalid without finalized, verified ground truth.
- **NO MODEL PERFORMANCE CLAIMS**: No baseline or classifier performance may be claimed on unvalidated data.
- **NO PREMATURE QUALITY CLAIMS**: Do not claim the 100-event pilot is "ground-truth verified" before human reviews are executed and finalized.
- **NO CAUSAL CLAIMS FROM CORRELATION ALONE**: Spatial co-location or statistical correlation does not establish physical causation.
