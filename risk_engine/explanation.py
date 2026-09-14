"""
ThermoGuard Phase IX - Deterministic Audit and Explanation Generator.

Generates structured JSON audit records and human-readable explanation narratives
providing full mathematical and observational traceability.
Reference: docs/PhaseIX_RISK_METHODOLOGY.md Section 11.
"""

from typing import Dict, Any
import json


def generate_audit_explanation(scored_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a fully traceable deterministic JSON audit explanation.
    Matches Task 25 & 27 specification.
    """
    dims = scored_record["dimensions"]
    conf = scored_record["confidence_details"]

    audit = {
        "event_id": scored_record["event_id"],
        "methodology_version": scored_record["methodology_version"],
        "risk_score": scored_record["risk_score"],
        "risk_score_raw": scored_record["risk_score_raw"],
        "risk_tier": scored_record["risk_tier"],
        "dimensions": {
            "thermal": {
                "dimension_code": "A",
                "weight": dims["thermal"]["weight"],
                "normalized_score": dims["thermal"]["score"],
                "weighted_contribution": dims["thermal"]["weighted_contribution"],
                "raw_inputs": dims["thermal"]["raw_inputs"],
                "normalized_components": dims["thermal"]["normalized_components"],
                "internal_weights": dims["thermal"]["internal_weights"],
                "missing_fields": dims["thermal"]["missing_fields"],
            },
            "persistence": {
                "dimension_code": "B",
                "weight": dims["persistence"]["weight"],
                "normalized_score": dims["persistence"]["score"],
                "weighted_contribution": dims["persistence"]["weighted_contribution"],
                "raw_inputs": dims["persistence"]["raw_inputs"],
                "normalized_components": dims["persistence"]["normalized_components"],
                "internal_weights": dims["persistence"]["internal_weights"],
                "missing_fields": dims["persistence"]["missing_fields"],
            },
            "industrial": {
                "dimension_code": "C",
                "weight": dims["industrial"]["weight"],
                "normalized_score": dims["industrial"]["score"],
                "weighted_contribution": dims["industrial"]["weighted_contribution"],
                "raw_inputs": dims["industrial"]["raw_inputs"],
                "normalized_components": dims["industrial"]["normalized_components"],
                "internal_weights": dims["industrial"]["internal_weights"],
                "missing_fields": dims["industrial"]["missing_fields"],
                "has_mapped_association": dims["industrial"]["has_mapped_association"],
            },
            "spatial": {
                "dimension_code": "D",
                "weight": dims["spatial"]["weight"],
                "normalized_score": dims["spatial"]["score"],
                "weighted_contribution": dims["spatial"]["weighted_contribution"],
                "raw_inputs": dims["spatial"]["raw_inputs"],
                "normalized_components": dims["spatial"]["normalized_components"],
                "internal_weights": dims["spatial"]["internal_weights"],
                "missing_fields": dims["spatial"]["missing_fields"],
            },
            "spectral": {
                "dimension_code": "E",
                "weight": dims["spectral"]["weight"],
                "normalized_score": dims["spectral"]["score"],
                "raw_score_before_reliability": dims["spectral"]["raw_score_before_reliability"],
                "spectral_reliability": dims["spectral"]["spectral_reliability"],
                "temporal_reliability": dims["spectral"]["temporal_reliability"],
                "cloud_reliability": dims["spectral"]["cloud_reliability"],
                "weighted_contribution": dims["spectral"]["weighted_contribution"],
                "raw_inputs": dims["spectral"]["raw_inputs"],
                "normalized_components": dims["spectral"]["normalized_components"],
                "internal_weights": dims["spectral"]["internal_weights"],
                "missing_fields": dims["spectral"]["missing_fields"],
            },
        },
        "confidence": {
            "score": scored_record["evidence_confidence"],
            "tier": scored_record["confidence_tier"],
            "inputs": conf["components"],
        },
        "contextual_annotations": scored_record["contextual_data"],
        "missing_evidence": scored_record["missing_evidence"],
        "scientific_caveats": [
            "Risk score reflects observed physical/contextual evidence strength; NOT ground-truth validated.",
            "Evidence Confidence is observational quality/corroboration; NOT class probability.",
            "Sentinel-2 SWIR bands (B11/B12) measure surface reflectance contrast; NOT temperature or active combustion.",
            "OSM proximity indicates mapped infrastructure co-location; NOT proof of industrial causation.",
            "Larger spatial scale indicates geographic extent; does NOT automatically mean higher industrial hazard.",
            "Missing evidence lowers observed score on fixed scale; must NOT be interpreted as lower real-world danger.",
        ],
    }
    return audit


def format_text_explanation(scored_record: Dict[str, Any]) -> str:
    """
    Format a deterministic human-readable audit record according to Section 11.
    """
    event_id = scored_record["event_id"]
    risk = scored_record["risk_score"]
    tier = scored_record["risk_tier"]
    conf = scored_record["evidence_confidence"]
    c_tier = scored_record["confidence_tier"]

    dims = scored_record["dimensions"]
    ctx = scored_record["contextual_data"]

    lines = [
        f"event_id            : {event_id}",
        f"risk_score          : {risk:.1f} / 100",
        f"risk_tier           : {tier}",
        f"evidence_confidence : {conf:.1f} / 100 ({c_tier})",
        "",
        "--- RISK DIMENSION SCORES (Sum of weights = 100%) ---",
        f"A. Thermal Intensity (30%)              : {dims['thermal']['score'] * 100:.1f} / 100 (contrib: {dims['thermal']['weighted_contribution'] * 100:.1f} pts)",
        f"B. Persistence (25%)                    : {dims['persistence']['score'] * 100:.1f} / 100 (contrib: {dims['persistence']['weighted_contribution'] * 100:.1f} pts)",
        f"C. Industrial Association (20%)         : {dims['industrial']['score'] * 100:.1f} / 100 (contrib: {dims['industrial']['weighted_contribution'] * 100:.1f} pts)",
        f"D. Spatial Scale (10%)                  : {dims['spatial']['score'] * 100:.1f} / 100 (contrib: {dims['spatial']['weighted_contribution'] * 100:.1f} pts)",
        f"E. Spectral / Surface Evidence (15%)    : {dims['spectral']['score'] * 100:.1f} / 100 (contrib: {dims['spectral']['weighted_contribution'] * 100:.1f} pts)",
        f"   Spectral reliability factor          : {dims['spectral']['spectral_reliability']:.3f}",
        "",
        "--- CONTEXTUAL ANNOTATIONS (0% Risk Weight) ---",
        f"- WorldCover baseline landscape         : {ctx.get('worldcover_class_name', 'None')}",
        f"- OSM facility category & tier          : {ctx.get('osm_primary_category', 'None')} / tier={ctx.get('osm_tier', 'None')}",
        "",
        "--- EVIDENCE CONFIDENCE & CORROBORATION ---",
        f"- Multi-satellite platforms observing   : {ctx.get('distinct_satellites', 1)}",
        f"- Evidence Confidence Score             : {conf:.1f} / 100 ({c_tier})",
        "",
        "--- MISSING EVIDENCE & DATA DEGRADATIONS ---",
    ]

    if scored_record["missing_evidence"]:
        for item in scored_record["missing_evidence"]:
            lines.append(f"- {item}")
    else:
        lines.append("- None (all primary observations present)")

    return "\n".join(lines)


# ==============================================================================
# TASK 28: ADVANCED DETERMINISTIC EXPLAINABILITY LAYER
# ==============================================================================

DIMENSION_METADATA = {
    "thermal": {
        "code": "A",
        "name": "Thermal Intensity",
        "weight": 0.30,
        "max_points": 30.0,
    },
    "persistence": {
        "code": "B",
        "name": "Persistence",
        "weight": 0.25,
        "max_points": 25.0,
    },
    "industrial": {
        "code": "C",
        "name": "Industrial Association",
        "weight": 0.20,
        "max_points": 20.0,
    },
    "spatial": {
        "code": "D",
        "name": "Spatial Scale",
        "weight": 0.10,
        "max_points": 10.0,
    },
    "spectral": {
        "code": "E",
        "name": "Spectral / Surface Evidence",
        "weight": 0.15,
        "max_points": 15.0,
    },
}


def rank_dimension_contributions(dimensions: Dict[str, Any]) -> Dict[str, Any]:
    """
    Part B: Rank dimensions by absolute weighted contribution (points on 0–100 scale).
    Identifies primary driver, secondary driver, and weakest/absent evidence.
    """
    ranked_list = []
    for dim_key, meta in DIMENSION_METADATA.items():
        dim_data = dimensions[dim_key]
        raw_contrib = dim_data["weighted_contribution"]
        pts = round(raw_contrib * 100.0, 1)
        norm_score = round(dim_data["score"], 4)
        ranked_list.append({
            "key": dim_key,
            "code": meta["code"],
            "name": meta["name"],
            "weight": meta["weight"],
            "max_points": meta["max_points"],
            "normalized_score": norm_score,
            "weighted_contribution_fraction": raw_contrib,
            "points": pts,
            "formatted": f"{meta['name']} — {pts:.1f} points",
        })

    # Sort descending by points, tie-break by weight
    ranked_list.sort(key=lambda x: (x["points"], x["weight"]), reverse=True)

    primary = ranked_list[0]
    secondary = ranked_list[1]
    weakest = ranked_list[-1]

    return {
        "ranked_dimensions": ranked_list,
        "primary_driver": primary,
        "secondary_driver": secondary,
        "weakest_dimension": weakest,
        "primary_driver_text": f"Primary driver: {primary['name']} — {primary['points']:.1f} points",
        "secondary_driver_text": f"Secondary driver: {secondary['name']} — {secondary['points']:.1f} points",
        "weakest_dimension_text": f"Weakest evidence: {weakest['name']} — {weakest['points']:.1f} points",
    }


def extract_raw_evidence_trace(dimensions: Dict[str, Any]) -> Dict[str, Any]:
    """
    Part C: Expose the raw evidence used by each dimension.
    Only exposes fields actually present in the scoring record; does NOT fabricate values.
    """
    raw_trace = {}

    # Thermal
    thermal_raw = dimensions["thermal"]["raw_inputs"]
    raw_trace["thermal"] = {
        k: thermal_raw.get(k)
        for k in ["frp_mean", "frp_max", "brightness_mean"]
        if k in thermal_raw and thermal_raw[k] is not None
    }

    # Persistence
    pers_raw = dimensions["persistence"]["raw_inputs"]
    raw_trace["persistence"] = {
        k: pers_raw.get(k)
        for k in ["distinct_detection_days", "detection_count"]
        if k in pers_raw and pers_raw[k] is not None
    }

    # Industrial
    ind_raw = dimensions["industrial"]["raw_inputs"]
    raw_trace["industrial"] = {
        k: ind_raw.get(k)
        for k in ["osm_matched_fraction", "osm_containment_fraction", "osm_proximity_fraction", "min_distance_m"]
        if k in ind_raw and ind_raw[k] is not None
    }

    # Spatial
    spat_raw = dimensions["spatial"]["raw_inputs"]
    raw_trace["spatial"] = {
        k: spat_raw.get(k)
        for k in ["spatial_extent_km2"]
        if k in spat_raw and spat_raw[k] is not None
    }

    # Spectral
    spec_raw = dimensions["spectral"]["raw_inputs"]
    raw_trace["spectral"] = {
        k: spec_raw.get(k)
        for k in [
            "swir2_anomaly_ratio",
            "ndvi",
            "swir2_swir1_ratio",
            "bsi",
            "scl_clear_fraction",
            "temporal_delta_days",
        ]
        if k in spec_raw and spec_raw[k] is not None
    }

    return raw_trace


def categorize_missing_stale_evidence(scored_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Part D: Categorize missing, unavailable, extraction-failed, stale, or zero-observed evidence.
    Ensures language such as:
    'Contemporary Sentinel-2 evidence was unavailable/stale, so this dimension contributed 0 points.
     This is an evidence limitation, not evidence of absence.'
    """
    dims = scored_record["dimensions"]
    tags = scored_record.get("missing_evidence", [])

    categorization = {
        "status_by_dimension": {},
        "narratives": [],
        "sentinel2_explanation": "",
        "missing_evidence_tags": tags,
    }

    # Dimension A: Thermal
    if dims["thermal"]["is_completely_missing"]:
        categorization["status_by_dimension"]["thermal"] = "MISSING"
        categorization["narratives"].append(
            "Thermal intensity measurements were completely missing; contributed 0.0 points."
        )
    elif len(dims["thermal"]["missing_fields"]) > 0:
        categorization["status_by_dimension"]["thermal"] = "PARTIAL"
        categorization["narratives"].append(
            f"Thermal intensity features partially missing ({', '.join(dims['thermal']['missing_fields'])})."
        )
    else:
        categorization["status_by_dimension"]["thermal"] = "PRESENT"

    # Dimension B: Persistence
    if dims["persistence"]["is_completely_missing"]:
        categorization["status_by_dimension"]["persistence"] = "MISSING"
        categorization["narratives"].append(
            "Temporal persistence measurements were completely missing; contributed 0.0 points."
        )
    elif len(dims["persistence"]["missing_fields"]) > 0:
        categorization["status_by_dimension"]["persistence"] = "PARTIAL"
        categorization["narratives"].append(
            f"Persistence features partially missing ({', '.join(dims['persistence']['missing_fields'])})."
        )
    else:
        categorization["status_by_dimension"]["persistence"] = "PRESENT"

    # Dimension C: Industrial
    if dims["industrial"]["is_completely_missing"]:
        categorization["status_by_dimension"]["industrial"] = "MISSING"
        categorization["narratives"].append(
            "OSM industrial proximity query data was missing; contributed 0.0 points."
        )
    elif not dims["industrial"]["has_mapped_association"]:
        categorization["status_by_dimension"]["industrial"] = "ZERO_OBSERVED_CONTRIBUTION"
        categorization["narratives"].append(
            "No mapped industrial infrastructure identified within 5,000m buffer (zero observed contribution)."
        )
    else:
        categorization["status_by_dimension"]["industrial"] = "PRESENT"

    # Dimension D: Spatial
    if dims["spatial"]["is_completely_missing"]:
        categorization["status_by_dimension"]["spatial"] = "MISSING"
        categorization["narratives"].append(
            "Convex hull spatial extent measurement was missing; contributed 0.0 points."
        )
    else:
        categorization["status_by_dimension"]["spatial"] = "PRESENT"

    # Dimension E: Spectral
    spec = dims["spectral"]
    spec_raw = spec["raw_inputs"]
    has_scene = spec_raw.get("has_satellite_scene", 0)
    has_features = spec_raw.get("has_spectral_features", 0)
    temporal_rel = spec.get("temporal_reliability", 1.0)
    cloud_rel = spec.get("cloud_reliability", 1.0)
    temp_delta = spec_raw.get("temporal_delta_days")

    if has_scene == 0:
        categorization["status_by_dimension"]["spectral"] = "UNAVAILABLE"
        s2_msg = (
            "Contemporary Sentinel-2 evidence was unavailable (no contemporary scene available), "
            "so this dimension contributed 0 points. This is an evidence limitation, not evidence of absence."
        )
    elif has_features == 0:
        categorization["status_by_dimension"]["spectral"] = "EXTRACTION_FAILURE"
        s2_msg = (
            "Sentinel-2 scene was present but spectral feature extraction failed, "
            "so this dimension contributed 0 points. This is an evidence limitation, not evidence of absence."
        )
    elif temporal_rel == 0.0:
        categorization["status_by_dimension"]["spectral"] = "STALE"
        delta_str = f"{temp_delta:.1f} days" if temp_delta is not None else "exceeding window"
        s2_msg = (
            f"Contemporary Sentinel-2 evidence was stale (temporal offset: {delta_str} > 90 days; temporal reliability = 0.0), "
            "so this dimension contributed 0 points. This is an evidence limitation, not evidence of absence."
        )
    elif temporal_rel < 0.5:
        categorization["status_by_dimension"]["spectral"] = "DEGRADED_TEMPORAL"
        delta_str = f"{temp_delta:.1f} days" if temp_delta is not None else "extended"
        s2_msg = (
            f"Sentinel-2 evidence is temporally degraded (temporal offset: {delta_str}; temporal reliability = {temporal_rel:.2f}). "
            "Spectral contribution is scaled downward accordingly."
        )
    elif cloud_rel < 0.5:
        categorization["status_by_dimension"]["spectral"] = "DEGRADED_CLOUD"
        s2_msg = (
            f"Sentinel-2 scene contains significant cloud obstruction (clear fraction: {cloud_rel:.2f}). "
            "Spectral contribution is scaled downward accordingly."
        )
    elif spec["score"] == 0.0:
        categorization["status_by_dimension"]["spectral"] = "ZERO_OBSERVED_CONTRIBUTION"
        s2_msg = (
            "Clear Sentinel-2 imagery was available, but observed SWIR contrast and surface indices "
            "were at or below background levels (0.0 points observed)."
        )
    else:
        categorization["status_by_dimension"]["spectral"] = "PRESENT"
        s2_msg = "Contemporary Sentinel-2 imagery was clear and temporally aligned."

    categorization["sentinel2_explanation"] = s2_msg
    categorization["narratives"].append(s2_msg)

    return categorization


def extract_confidence_breakdown(scored_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Part E: Expose Evidence Confidence details and reinforce mathematical separation from Risk Score.
    """
    conf = scored_record["evidence_confidence"]
    c_tier = scored_record["confidence_tier"]
    conf_details = scored_record.get("confidence_details", {})
    components = conf_details.get("components", {})
    ctx = scored_record.get("contextual_data", {})
    distinct_sats = ctx.get("distinct_satellites", 1)

    return {
        "evidence_confidence_score": conf,
        "confidence_tier": c_tier,
        "distinct_satellites": distinct_sats,
        "contributing_factors": {
            "temporal_reliability": components.get("temporal_reliability", 1.0),
            "cloud_reliability": components.get("cloud_reliability", 1.0),
            "spectral_reliability": components.get("spectral_reliability", 1.0),
            "satellite_corroboration": components.get("satellite_corroboration", 0.7 if distinct_sats == 1 else 1.0),
            "osm_completeness": components.get("osm_completeness", 1.0),
            "has_spectral_features": components.get("has_spectral_features", 1),
        },
        "separation_statement": (
            "Evidence Confidence measures observational corroboration and sensor reliability on a 0–100 scale. "
            "It does NOT multiply, cap, boost, or alter the numerical Risk Score. "
            "A low risk score combined with low confidence indicates missing/degraded data, NOT verified safety."
        ),
    }


def generate_analyst_interpretations(scored_record: Dict[str, Any], ranked_dims: Dict[str, Any]) -> Dict[str, str]:
    """
    Part F: Generate deterministic descriptive templates for each dimension and an overall synthesis.
    Strictly descriptive: NO claims of confirmed fire, dangerous fire, or probability of fire.
    """
    dims = scored_record["dimensions"]

    # Thermal
    t_score = dims["thermal"]["score"]
    if dims["thermal"]["is_completely_missing"]:
        t_text = "Thermal intensity measurements were unavailable."
    elif t_score >= 0.5:
        t_text = "Substantial thermal energy output observed with elevated fire radiative power and elevated brightness temperatures."
    elif t_score >= 0.2:
        t_text = "Moderate thermal energy output observed within typical industrial/combustion baseline ranges."
    elif t_score > 0.0:
        t_text = "Low thermal energy output observed near sensor detection thresholds."
    else:
        t_text = "Thermal measurements are at or below sensor background thresholds."

    # Persistence
    p_score = dims["persistence"]["score"]
    p_raw = dims["persistence"]["raw_inputs"]
    p_days = p_raw.get("distinct_detection_days", 0)
    p_cnt = p_raw.get("detection_count", 0)
    if dims["persistence"]["is_completely_missing"]:
        p_text = "Persistence observations were unavailable."
    elif p_score >= 0.6:
        p_text = f"Chronic thermal activity persisted across {p_days} distinct detection days ({p_cnt:,} total detections)."
    elif p_score >= 0.2:
        p_text = f"Recurrent thermal activity observed across multiple detection cycles ({p_days} days, {p_cnt:,} detections)."
    elif p_score > 0.0:
        p_text = f"The event was observed over a short temporal window ({p_days} days, {p_cnt:,} detections)."
    else:
        p_text = "Single-detection thermal event with minimal temporal duration."

    # Industrial
    i_score = dims["industrial"]["score"]
    i_raw = dims["industrial"]["raw_inputs"]
    i_dist = i_raw.get("min_distance_m")
    if dims["industrial"]["is_completely_missing"]:
        i_text = "Industrial context data was unavailable."
    elif i_score >= 0.6:
        i_text = "The event is strongly associated with mapped industrial infrastructure (high polygon containment / direct co-location)."
    elif i_score >= 0.2:
        dist_str = f"{i_dist:.0f}m" if i_dist is not None else "< 5,000m"
        i_text = f"The event is located in moderate proximity to mapped industrial infrastructure (minimum distance: {dist_str})."
    elif dims["industrial"]["has_mapped_association"]:
        dist_str = f"{i_dist:.0f}m" if i_dist is not None else "within 5,000m"
        i_text = f"Weak industrial association (peripheral proximity: {dist_str})."
    else:
        i_text = "No mapped industrial infrastructure was identified within the methodology-defined 5,000m spatial context."

    # Spatial
    s_score = dims["spatial"]["score"]
    s_raw = dims["spatial"]["raw_inputs"]
    s_area = s_raw.get("spatial_extent_km2")
    area_str = f"{s_area:.2f} km²" if s_area is not None else "unknown area"
    if dims["spatial"]["is_completely_missing"]:
        s_text = "Spatial extent measurement was unavailable."
    elif s_score >= 0.6:
        s_text = f"Extensive spatial footprint encompassing a large contiguous thermal cluster area ({area_str})."
    elif s_score >= 0.2:
        s_text = f"Moderate cluster geographic extent spanning {area_str}."
    else:
        s_text = f"Compact, localized geographic footprint ({area_str})."

    # Spectral
    spec = dims["spectral"]
    spec_score = spec["score"]
    spec_raw = spec["raw_inputs"]
    temp_rel = spec.get("temporal_reliability", 1.0)
    has_scene = spec_raw.get("has_satellite_scene", 0)
    if has_scene == 0:
        sp_text = "No usable Sentinel-2 evidence was available for this event."
    elif temp_rel == 0.0:
        sp_text = "Available Sentinel-2 evidence is temporally stale relative to the FIRMS observation (>90 days offset)."
    elif spec_score >= 0.6:
        sp_text = "Elevated Sentinel-2 SWIR band surface reflectance contrast observed under clear sky conditions."
    elif spec_score >= 0.2:
        sp_text = "Moderate surface reflectance contrast or surface disturbance detected in contemporary satellite imagery."
    elif spec_score > 0.0:
        sp_text = "Minor SWIR contrast detected above background reflectance levels."
    else:
        sp_text = "Surface reflectance indices show no distinct contrast relative to local background in available imagery."

    # Overall synthesis
    pri = ranked_dims["primary_driver"]
    sec = ranked_dims["secondary_driver"]
    r_score = scored_record["risk_score"]
    r_tier = scored_record["risk_tier"]

    synthesis = (
        f"Event received an investigation priority score of {r_score:.1f}/100 ({r_tier}). "
        f"The primary risk driver is {pri['name']} ({pri['points']:.1f} pts), "
        f"followed by {sec['name']} ({sec['points']:.1f} pts)."
    )

    return {
        "thermal_statement": t_text,
        "persistence_statement": p_text,
        "industrial_statement": i_text,
        "spatial_statement": s_text,
        "spectral_statement": sp_text,
        "overall_synthesis": synthesis,
    }


def determine_investigation_priority(scored_record: Dict[str, Any], ranked_dims: Dict[str, Any]) -> Dict[str, Any]:
    """
    Part G: Create deterministic investigation-priority recommendation based on:
    - risk tier
    - evidence confidence
    - missing evidence
    - dominant risk dimensions
    Does NOT create a new numerical score.
    """
    risk_tier = scored_record["risk_tier"]
    conf_tier = scored_record["confidence_tier"]
    missing_evidence = scored_record.get("missing_evidence", [])
    primary = ranked_dims["primary_driver"]

    # Evaluate specific recommendation category
    if risk_tier in ("CRITICAL", "HIGH"):
        if conf_tier == "HIGH":
            rec = "Priority investigation target"
            rationale = (
                f"Elevated risk score ({scored_record['risk_score']:.1f}/100, {risk_tier}) "
                f"corroborated by high observational confidence ({scored_record['evidence_confidence']:.1f}/100). "
                f"Driven primarily by {primary['name']} ({primary['points']:.1f} pts)."
            )
            actions = [
                "Conduct immediate spatial and boundary review of the thermal cluster against OSM infrastructure.",
                "Review active operational status of the co-located facility.",
                "Verify multi-sensor thermal persistence with upcoming satellite overpasses.",
            ]
        else:
            rec = "Priority target — needs corroborating verification"
            rationale = (
                f"Elevated risk score ({scored_record['risk_score']:.1f}/100, {risk_tier}), but observational "
                f"confidence is constrained ({scored_record['evidence_confidence']:.1f}/100, {conf_tier}) "
                f"due to degraded/missing optical verification or single-satellite observation."
            )
            actions = [
                "Prioritize fresh high-resolution optical imagery acquisition.",
                "Corroborate thermal persistence across additional satellite constellations.",
                "Inspect facility boundaries to confirm infrastructure co-location.",
            ]
    elif risk_tier == "MODERATE":
        if conf_tier == "HIGH":
            rec = "Routine monitoring target"
            rationale = (
                f"Moderate risk score ({scored_record['risk_score']:.1f}/100) supported by confident multi-sensor "
                f"corroboration ({scored_record['evidence_confidence']:.1f}/100). "
                f"Activity is observed but below priority thresholds."
            )
            actions = [
                "Include in scheduled weekly thermal audit queue.",
                "Monitor for unexpected spikes in fire radiative power or spatial cluster expansion.",
            ]
        else:
            rec = "Needs additional satellite verification"
            rationale = (
                f"Moderate risk score ({scored_record['risk_score']:.1f}/100) with limited observational "
                f"confidence ({scored_record['evidence_confidence']:.1f}/100, {conf_tier}). "
                f"Gaps in optical or corroborating data prevent definitive characterization."
            )
            actions = [
                "Task contemporary optical satellite verification pass.",
                "Verify whether thermal cluster is persistent or transient.",
            ]
    else:  # LOW
        if conf_tier == "HIGH":
            rec = "Confident low-risk event"
            rationale = (
                f"Low risk score ({scored_record['risk_score']:.1f}/100) with high observational confidence "
                f"({scored_record['evidence_confidence']:.1f}/100). Robust multi-satellite data confirms "
                f"localized, low-persistence, or non-industrial thermal signature."
            )
            actions = [
                "Archive as low-priority background/transient thermal observation.",
                "No active investigation required unless new persistent detections occur.",
            ]
        elif conf_tier == "LOW":
            rec = "Low observed risk but insufficient evidence"
            rationale = (
                f"Low numerical score ({scored_record['risk_score']:.1f}/100) coincides with low evidence confidence "
                f"({scored_record['evidence_confidence']:.1f}/100). Key observational dimensions were unavailable "
                f"or unobserved; low score reflects absence of data rather than confirmed absence of hazard."
            )
            actions = [
                "Do NOT conclude real-world safety based on numerical score alone.",
                "Check for upcoming satellite coverage to fill evidence gaps.",
                "Review multi-day FIRMS history to confirm if thermal activity was truly transient.",
            ]
        else:  # Medium confidence
            rec = "Routine low-priority monitoring"
            rationale = (
                f"Low risk score ({scored_record['risk_score']:.1f}/100) with moderate confidence "
                f"({scored_record['evidence_confidence']:.1f}/100). Minimal industrial or persistent characteristics."
            )
            actions = [
                "Standard archive logging.",
                "Flag for automated re-evaluation if repeat detections arise.",
            ]

    # Additional optical recommendation if Sentinel-2 is missing/stale
    if any("spectral" in tag or "temporal_relevance:stale" in tag for tag in missing_evidence):
        actions.append("Acquire fresh cloud-free Sentinel-2/Landsat optical pass to resolve surface context.")

    return {
        "recommendation": rec,
        "rationale": rationale,
        "recommended_next_actions": actions,
    }


def generate_comprehensive_explanation(scored_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Part A–G Orchestration: Generate complete, fully traceable deterministic explanation dictionary.
    """
    dims = scored_record["dimensions"]
    risk_score = scored_record["risk_score"]
    risk_tier = scored_record["risk_tier"]

    # Part A: Score Breakdown
    score_breakdown = {}
    for dim_key, meta in DIMENSION_METADATA.items():
        d_info = dims[dim_key]
        pts = round(d_info["weighted_contribution"] * 100.0, 1)
        score_breakdown[dim_key] = {
            "dimension_code": meta["code"],
            "dimension_name": meta["name"],
            "weight": meta["weight"],
            "max_possible_points": meta["max_points"],
            "normalized_score": round(d_info["score"], 4),
            "weighted_contribution_fraction": round(d_info["weighted_contribution"], 4),
            "weighted_contribution_points": pts,
            "explanation": f"{meta['name']} (weight {int(meta['weight']*100)}%): normalized score {d_info['score']:.3f} contributes {pts:.1f} points to the 0–100 risk score.",
        }

    # Part B: Contribution Ranking
    ranking = rank_dimension_contributions(dims)

    # Part C: Raw Evidence Trace
    raw_trace = extract_raw_evidence_trace(dims)

    # Part D: Missing / Stale Evidence Categorization
    missing_stale = categorize_missing_stale_evidence(scored_record)

    # Part E: Evidence Confidence Breakdown
    confidence_breakdown = extract_confidence_breakdown(scored_record)

    # Part F: Analyst Interpretations
    interpretations = generate_analyst_interpretations(scored_record, ranking)

    # Part G: Investigation Priority Recommendation
    investigation_priority = determine_investigation_priority(scored_record, ranking)

    # Contextual annotations (0% risk weight)
    ctx = scored_record.get("contextual_data", {})

    return {
        "event_id": scored_record["event_id"],
        "methodology_version": scored_record.get("methodology_version", "PhaseIX-2026-09-14"),
        "final_risk_score": risk_score,
        "risk_tier": risk_tier,
        "evidence_confidence": confidence_breakdown["evidence_confidence_score"],
        "confidence_tier": confidence_breakdown["confidence_tier"],
        "score_breakdown": score_breakdown,
        "contribution_ranking": ranking,
        "raw_evidence_trace": raw_trace,
        "missing_and_stale_evidence": missing_stale,
        "evidence_confidence_breakdown": confidence_breakdown,
        "analyst_interpretations": interpretations,
        "investigation_priority": investigation_priority,
        "contextual_annotations": {
            "worldcover_class": ctx.get("worldcover_class"),
            "worldcover_class_name": ctx.get("worldcover_class_name"),
            "osm_primary_category": ctx.get("osm_primary_category"),
            "osm_sub_category": ctx.get("osm_sub_category"),
            "osm_tier": ctx.get("osm_tier"),
            "distinct_satellites": ctx.get("distinct_satellites", 1),
            "note": "Contextual metadata has 0% direct risk weight per locked Phase IX methodology.",
        },
        "traceability": {
            "formula": "Risk Score = 0.30 * A + 0.25 * B + 0.20 * C + 0.10 * D + 0.15 * E",
            "sum_of_weights": 1.00,
            "scale": "0.0 to 100.0 (fixed scale, zero redistribution)",
        },
        "scientific_caveats": [
            "Risk score reflects observed physical/contextual evidence strength; NOT ground-truth validated.",
            "Evidence Confidence is observational quality/corroboration; NOT class probability.",
            "Sentinel-2 SWIR bands (B11/B12) measure surface reflectance contrast; NOT temperature or active combustion.",
            "OSM proximity indicates mapped infrastructure co-location; NOT proof of industrial causation.",
            "Larger spatial scale indicates geographic extent; does NOT automatically mean higher industrial hazard.",
            "Missing evidence lowers observed score on fixed scale; must NOT be interpreted as lower real-world danger.",
        ],
    }


def format_analyst_markdown(explanation: Dict[str, Any]) -> str:
    """
    Format a clean, analyst-readable Markdown section for an event.
    """
    eid = explanation["event_id"]
    r_score = explanation["final_risk_score"]
    r_tier = explanation["risk_tier"]
    c_score = explanation["evidence_confidence"]
    c_tier = explanation["confidence_tier"]
    ranking = explanation["contribution_ranking"]
    pri = ranking["primary_driver"]
    sec = ranking["secondary_driver"]
    weak = ranking["weakest_dimension"]
    breakdown = explanation["score_breakdown"]
    raw = explanation["raw_evidence_trace"]
    missing = explanation["missing_and_stale_evidence"]
    interp = explanation["analyst_interpretations"]
    priority = explanation["investigation_priority"]
    ctx = explanation["contextual_annotations"]

    lines = [
        f"### Event `{eid}`",
        "",
        f"| Metric | Value | Tier |",
        f"| :--- | :---: | :---: |",
        f"| **Risk Score** | **{r_score:.1f} / 100** | **{r_tier}** |",
        f"| **Evidence Confidence** | **{c_score:.1f} / 100** | **{c_tier}** |",
        f"| **Investigation Priority** | **{priority['recommendation']}** | — |",
        "",
        f"**Summary**: {interp['overall_synthesis']}",
        "",
        "#### 1. Dimension Score Breakdown",
        "",
        "| Dimension | Code | Weight | Normalized [0, 1] | Weighted Points [0–100] | Status |",
        "| :--- | :---: | :---: | :---: | :---: | :---: |",
    ]

    for k in ["thermal", "persistence", "industrial", "spatial", "spectral"]:
        b = breakdown[k]
        status = missing["status_by_dimension"].get(k, "PRESENT")
        lines.append(
            f"| {b['dimension_name']} | `{b['dimension_code']}` | {int(b['weight']*100)}% | {b['normalized_score']:.3f} | **{b['weighted_contribution_points']:.1f}** | `{status}` |"
        )

    lines.extend([
        "",
        "#### 2. Key Contribution Drivers",
        f"- **{ranking['primary_driver_text']}**",
        f"- **{ranking['secondary_driver_text']}**",
        f"- **{ranking['weakest_dimension_text']}**",
        "",
        "#### 3. Raw Evidence Trace",
        f"- **Thermal**: FRP mean = {raw['thermal'].get('frp_mean', 'N/A')}, FRP max = {raw['thermal'].get('frp_max', 'N/A')}, Brightness mean = {raw['thermal'].get('brightness_mean', 'N/A')} K",
        f"- **Persistence**: Distinct detection days = {raw['persistence'].get('distinct_detection_days', 'N/A')}, Total detection count = {raw['persistence'].get('detection_count', 'N/A')}",
        f"- **Industrial**: OSM match fraction = {raw['industrial'].get('osm_matched_fraction', 'N/A')}, Containment = {raw['industrial'].get('osm_containment_fraction', 'N/A')}, Proximity = {raw['industrial'].get('osm_proximity_fraction', 'N/A')}, Min distance = {raw['industrial'].get('min_distance_m', 'N/A')} m",
        f"- **Spatial**: Convex hull area = {raw['spatial'].get('spatial_extent_km2', 'N/A')} km²",
        f"- **Spectral**: SWIR anomaly ratio = {raw['spectral'].get('swir2_anomaly_ratio', 'N/A')}, NDVI = {raw['spectral'].get('ndvi', 'N/A')}, SWIR2/SWIR1 ratio = {raw['spectral'].get('swir2_swir1_ratio', 'N/A')}, BSI = {raw['spectral'].get('bsi', 'N/A')}, SCL clear fraction = {raw['spectral'].get('scl_clear_fraction', 'N/A')}, Temporal delta = {raw['spectral'].get('temporal_delta_days', 'N/A')} days",
        "",
        "#### 4. Evidence Availability & Limitations",
        f"- **Sentinel-2 Status**: {missing['sentinel2_explanation']}",
    ])

    if missing["missing_evidence_tags"]:
        lines.append(f"- **Missing Tags**: `{', '.join(missing['missing_evidence_tags'])}`")
    else:
        lines.append("- **Missing Tags**: None (all primary observational inputs present)")

    lines.extend([
        "",
        "#### 5. Deterministic Interpretations",
        f"- **Thermal**: {interp['thermal_statement']}",
        f"- **Persistence**: {interp['persistence_statement']}",
        f"- **Industrial**: {interp['industrial_statement']}",
        f"- **Spatial**: {interp['spatial_statement']}",
        f"- **Spectral**: {interp['spectral_statement']}",
        "",
        "#### 6. Investigation Recommendation & Next Actions",
        f"**Recommendation**: `{priority['recommendation']}`",
        f"**Rationale**: {priority['rationale']}",
        "**Recommended Next Steps**:",
    ])

    for act in priority["recommended_next_actions"]:
        lines.append(f"  - [ ] {act}")

    lines.extend([
        "",
        f"*Context: WorldCover = {ctx.get('worldcover_class_name', 'None')} | OSM Category = {ctx.get('osm_primary_category', 'None')} ({ctx.get('osm_tier', 'None')}) | Observing Satellites = {ctx.get('distinct_satellites', 1)}*",
        "---",
    ])

    return "\n".join(lines)
