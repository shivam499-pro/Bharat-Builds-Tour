# ThermoGuard Phase VI — Human Review Checklist

This checklist provides an operational, step-by-step procedure for human experts to inspect and review thermal anomaly events in the 100-event pilot dataset.

---

## Review Steps Checklist

### 1. Event Identity
- [ ] Verify `event_id` matches the tracking manifest.
- [ ] Check geographic coordinates (`latitude`, `longitude`) to locate the event on geographic reference maps.
- [ ] Note the temporal window: start datetime (`first_detection`) and end datetime (`last_detection`).

### 2. FIRMS Behavior
- [ ] **Detection Count**: How many distinct satellite detections form this clustered event?
- [ ] **Persistence**: What is the duration in days (`duration_days`) and distinct detection days (`distinct_detection_days`)? (e.g., single-day ephemeral vs multi-day persistent).
- [ ] **Fire Radiative Power (FRP)**: Evaluate `frp_mean`, `frp_max`, and `brightness_mean`. Are emissions exceptionally intense or modest?
- [ ] **Detection Consistency**: Were detections registered across multiple satellites (`distinct_satellites`) and instruments (`distinct_instruments`)?
- [ ] **Diurnal/Temporal Pattern**: Is the event active predominantly at night, during typical harvest hours, or continuous 24/7?

### 3. OpenStreetMap (OSM) Context
- [ ] **Industrial Infrastructure**: What is the nearest industrial feature category (`osm_primary_category`, `osm_sub_category`)?
- [ ] **Distance to Infrastructure**: Check `distance_to_industrial_m`. Is the event co-located directly inside facility bounds (`min_distance_m = 0` / high containment), adjacent, or distant (> 5 km)?
- [ ] **Infrastructure Type**: Does the facility type involve high-heat industrial processes (e.g., brick kilns, steel mills, flare stacks, petrochemical plants)?
- [ ] **Contextual Support**: Does the infrastructure context support or undermine an industrial attribution?

### 4. WorldCover Context
- [ ] **Land-Cover Class**: What is the baseline ESA WorldCover classification (`worldcover_class_name`) at the centroid (e.g., Tree cover, Cropland, Grassland, Built-up, Bare / sparse vegetation)?
- [ ] **Contextual Consistency**: Does the land-cover class corroborate the thermal observation, or does it present conflicting information?

### 5. Sentinel-2 Spectral Evidence
- [ ] **Image Availability**: Is an acquired scene present (`observation_status == 'enriched'`), or is imagery missing / cloudy?
- [ ] **Cloud & Clear Quality**: Check `scl_clear_fraction`, `scl_cloud_fraction`, and scene cloud percentage (`satellite_cloud_cover_scene`).
- [ ] **Visible & NIR Inspection**: Evaluate optical band reflectances (B02 Blue, B03 Green, B04 Red, B08 NIR) for visual burn scars, smoke plumes, or structural vegetation damage.
- [ ] **Shortwave Infrared (SWIR)**: Check B11 (SWIR1) and B12 (SWIR2) reflectance, SWIR anomaly ratio (`swir2_anomaly_ratio`), and `swir2_swir1_ratio`.
- [ ] **Spectral Indices**: Review normalized indices (`ndvi`, `nbr`, `nbr2`, `bsi`) for indicative post-fire burn severity drops.
- [ ] **Temporal Delta**: Confirm the temporal difference in days (`temporal_delta_days`) between the FIRMS fire cluster and the Sentinel-2 acquisition pass.

> **CRITICAL SCIENTIFIC NOTE**: Sentinel-2 provides optical, near-infrared (NIR), and shortwave infrared (SWIR) reflectance evidence; it is **NOT** a direct thermal measurement. Elevated SWIR reflectances indicate high surface reflectance or sub-pixel high-temperature combustion, but optical bands alone cannot measure radiant temperature.

### 6. Independent Evidence
- [ ] Search for official incident reports from local fire services, municipal agencies, or disaster management authorities.
- [ ] Check government, regulatory, or environmental monitoring agency notices.
- [ ] Review credible external documentation or verified news reports covering major factory fires, warehouse incidents, or industrial accidents.
- [ ] Inspect independent high-resolution manual satellite or aerial imagery where accessible.
- [ ] Record the provenance in `label_source`, `evidence_type`, and `evidence_url`.
- [ ] *Do NOT fabricate evidence, URLs, or external reports.*

### 7. Contradictory Evidence
- [ ] Explicitly identify and document any contradictory signals in `conflicting_evidence` (e.g., "Centroid is adjacent to cropland, but multi-day persistence and zero agricultural seasonality suggest stationary kiln").
- [ ] Determine whether contradictions undermine classification certainty.

### 8. Label Selection
Select strictly one category from the approved vocabulary:
- [ ] `industrial_fire`: Uncontrolled accidental fire inside industrial / commercial / warehouse facility.
- [ ] `industrial_thermal_source`: Stationary operational thermal source (kiln, flare, furnace, boiler).
- [ ] `agricultural_burning`: Field stubble, crop residue, or post-harvest clearance burning.
- [ ] `wildfire`: Forest, scrubland, or wildland fire.
- [ ] `mining_or_persistent_thermal`: Coal-field fire, open-cast mine thermal emission, slag heap.
- [ ] `other_uncertain`: Inconclusive, contradictory, or insufficient evidence.

### 9. Confidence Assessment
Assign evidence confidence level based on documentation strength:
- [ ] `high`: Verified by independent incident report or clear corroboration across independent sources without unresolved contradiction.
- [ ] `medium`: Strong corroborating circumstantial evidence across multiple spatial/temporal datasets, but lacking direct independent incident records.
- [ ] `low`: Plausible interpretation supported by limited data; residual ambiguity remains.

### 10. Review Status
Set the appropriate review state:
- [ ] `pending`: Unreviewed event.
- [ ] `reviewed`: Provisional review completed, pending second-party check.
- [ ] `needs_more_evidence`: Inspected, but cannot be classified without further imagery or records.
- [ ] `final`: Quality-controlled and finalized by reviewer.

---

## Explicit Rules

1. **`sampling_stratum` is NOT ground truth**: It was assigned during candidate stratification and must never be copied or assumed to be the physical class.
2. **Never force a label**: If evidence is ambiguous, assign `other_uncertain` or status `needs_more_evidence`.
3. **Record justification**: Every populated label must have an explicit `label_reason`.
4. **Record contradictions**: Any conflicting evidence must be recorded in `conflicting_evidence`.
5. **Model predictions cannot become ground truth**: Automated classifications, heuristics, or cluster labels must not be entered as human ground truth.
6. **No circular validation**: Do not use classifier outputs to validate or generate the training/evaluation labels.

---

## "Do Not Claim" Section

Reviewers must avoid making unjustified inferential leaps:

- **SWIR ratio alone does NOT prove a gas flare**: Elevated SWIR reflectances can arise from bright soil, bare rocks, metallic rooftops, or dry sand.
- **Forest land cover alone does NOT prove a wildfire**: Forest boundaries often encompass settlements, illegal kilns, campfires, or controlled forestry management burns.
- **OSM proximity alone does NOT prove an industrial fire**: Proximity does not equal causation; agricultural burning frequently occurs in fields adjacent to industrial corridors.
- **Cropland alone does NOT prove agricultural burning**: Crop zones host agricultural processing sheds, diesel generators, and waste dumps that can experience structural fires.
- **Sampling stratum does NOT prove event class**: Sampling stratum is a study-design partitioning variable, not physical ground truth.
