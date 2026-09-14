# ThermoGuard Evidence Review Protocol

## 1. Purpose

The purpose of this evidence review protocol is to establish defensible, auditable ground-truth labels for the pilot dataset before supervised classification. Supervised machine learning algorithms require rigorous, reliable reference data. This protocol governs the human review methodology necessary to assign trustworthy labels without circular reasoning, automated bias, or label leakage.

## 2. Candidate Labels

Reviewers must assign labels drawn strictly from the approved label vocabulary:

- `industrial_fire`: Active unwanted fire events occurring within industrial premises, factories, warehouses, manufacturing units, or chemical facilities.
- `industrial_thermal_source`: Persistent, authorized operational thermal emissions (such as flares, smelters, blast furnaces, brick kilns, or power plant boilers) that do not represent an uncontrolled accidental fire.
- `agricultural_burning`: Crop residue burning, stubble burning, or post-harvest field clearance.
- `wildfire`: Forest, scrubland, or grassland wildfires occurring outside managed crop or industrial zones.
- `mining_or_persistent_thermal`: Thermal anomalies associated with open-cast mining, coal-seam fires, slag heaps, or quarrying operations.
- `other_uncertain`: Valid designation when available evidence is insufficient, ambiguous, conflicting, or inconclusive.

The label `other_uncertain` is explicitly valid and encouraged whenever evidence does not support a definitive classification. Reviewers must never guess a category.

## 3. Evidence Hierarchy

Human reviewers must examine multi-source information following this structured evidence hierarchy:

1. **Independent external / incident evidence**: Verifiable records external to the automated extraction pipeline (incident registers, emergency service reports, news bulletins, regulator filings).
2. **Satellite visual evidence**: High-resolution optical imagery, true-color/false-color visual inspection, and spatial footprint patterns observed in Sentinel-2 scenes.
3. **Temporal FIRMS behavior**: Multi-day persistence, recurrence frequency, diurnal detection timing, and thermal radiation characteristics (FRP, brightness temperature).
4. **OSM infrastructure context**: Proximity to mapped industrial facilities, boundary containment within industrial polygons, or distance to identified settlements.
5. **WorldCover land-cover context**: Baseline land-cover classification (e.g., Tree cover, Cropland, Built-up, Bare / sparse vegetation).
6. **Sentinel-2 spectral evidence**: Multi-spectral band reflectances (B02–B12) and derived indices (SWIR anomaly ratio, SWIR2/SWIR1 ratio, NDVI, NBR, NBR2, BSI).

This hierarchy serves strictly as a **REVIEW FRAMEWORK** for structured human evaluation, NOT as an automated scoring system or formulaic classifier.

## 4. Independent Evidence

Independent evidence should preferably originate from sources that were not used to construct the feature space of the model. Incorporating independent evidence breaks circular confirmation loops and prevents self-reinforcing labeling errors.

Credible independent evidence examples include:
- Official incident reports from local fire services or disaster management authorities
- Government or public agency documentation (environmental board logs, safety auditor notices)
- Independently documented industrial incidents in verifiable media or safety databases
- Manually reviewed high-resolution optical satellite imagery (e.g., independent aerial or commercial imagery)
- Credible external ground-truth records or on-site survey confirmations

*Note: Reviewers must rely solely on authentic, verifiable sources and must never fabricate sources or URLs.*

## 5. Labeling Principles

Reviewers must strictly adhere to the following scientific principles:

- **Never label from `sampling_stratum` alone**: The sampling stratum reflects initial selection criteria, not physical reality.
- **Never label from WorldCover alone**: Land-cover maps have known pixel resolution and classification uncertainties.
- **Never label from OSM proximity alone**: Proximity to an industrial tag does not guarantee that a thermal event was an industrial fire.
- **Never label from one spectral index alone**: Atmospheric interference, soil moisture, and cloud shadows can distort individual indices.
- **Never label from FIRMS persistence alone**: Persistent fires can occur in coal mines or landfills as well as flare stacks.
- **Multiple pieces of corroborating evidence should be considered** before assigning any definitive label.
- **Contradictory evidence must be explicitly recorded** in `conflicting_evidence` to preserve uncertainty for model evaluation.
- **Insufficient evidence must result in `other_uncertain` or status `needs_more_evidence`**.
- **Do not force a class merely to increase dataset size**: High data quality and label integrity take precedence over class volume.

## 6. Confidence

Reviewers must record their confidence level using one of three standardized tiers:

- `high`: Multiple corroborating evidence sources confirm the label (e.g., independent report plus consistent visual and spectral anomaly), with zero unresolved contradictions.
- `medium`: Substantial circumstantial evidence supports the label (e.g., strong OSM containment, typical temporal profile, and consistent spectral signature), but lacking independent external confirmation.
- `low`: Plausible classification supported by limited evidence, or where minor ambiguity exists without completely invalidating the assignment.

*Confidence reflects the strength and corroboration of evidence supporting the human-reviewed label, NOT an automated model probability or classifier confidence score.*

## 7. Review Fields

The human-review workflow records the following attributes per event:

- `label`: Assigned ground-truth category from the controlled vocabulary (or NULL if unreviewed).
- `label_confidence`: Assigned confidence level (`high`, `medium`, `low`, or NULL).
- `label_source`: Provenance of the label assignment (e.g., `"human_review:expert_team"`, `"human_review:field_report"`).
- `label_reason`: Detailed textual explanation justifying the classification decision based on observed evidence.
- `evidence_type`: Primary category of evidence consulted (`"incident_report"`, `"satellite_visual"`, `"spatial_context"`, `"spectral_analysis"`).
- `evidence_url`: Verifiable URL or document reference identifying the evidence source (blank if unverified).
- `evidence_notes`: Contextual observation notes detailing scene characteristics, smoke plumes, cloud constraints, or specific feature patterns.
- `independent_evidence`: Boolean or descriptor indicating whether evidence external to the automated satellite pipeline was identified.
- `conflicting_evidence`: Explicit description of contradictory signals (e.g., `"OSM indicates agricultural zone but persistent high FRP indicates flare"`).
- `review_status`: State in the human review lifecycle (`pending`, `reviewed`, `needs_more_evidence`, `final`).

## 8. Review Status Lifecycle

The workflow transitions through four explicit review statuses:

- `pending`: The event is queued for inspection; no human review has yet occurred. All label and confidence fields must remain NULL.
- `reviewed`: Initial human inspection has been completed and a provisional label assigned, awaiting peer verification or secondary sign-off.
- `needs_more_evidence`: The event was inspected, but available information was insufficient or conflicting; requires additional imagery or external records before final determination.
- `final`: The event has undergone full evaluation, corroboration, and quality control; label, confidence, source, and reason are finalized.

## 9. Important Scientific Restrictions

> **"sampling_stratum is a sampling design variable and must never be treated as ground truth."**

> **"No labels are automatically generated by the Phase VI pipeline."**

Any automated copying, heuristic mapping, or rule-based conversion of `sampling_stratum` into `label` constitutes invalid data tampering and violates scientific validity.

## 10. No Leakage & Sound Validation Strategy

- **Feature Leakage Prevention**: Future model training must strictly avoid using features derived from, informed by, or proxying the final ground-truth label (e.g., `label_reason`, `evidence_notes`, or reviewer comments).
- **Validation Split Strategy**: Downstream models must be evaluated using **geographic holdout** (spatially separated regions/clusters) and **temporal holdout** (subsequent time periods) rather than purely random train/test splitting. Random splitting risks spatial and temporal autocorrelation, creating overly optimistic performance estimates.

## 11. Current Status

> **"The pilot labeling dataset is initially unlabeled. Supervised classification remains deferred until trustworthy labels are available."**

The pilot dataset of 100 events remains unassigned to labels (`review_status = "pending"`). No automated classification, accuracy scoring, or model metric calculation is performed until expert human review is complete under this protocol.
