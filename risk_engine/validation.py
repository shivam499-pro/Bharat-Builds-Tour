"""
ThermoGuard Phase IX - Risk Engine Validation and Statistics.

Computes coverage, distribution statistics, risk tier breakdowns,
confidence profiles, and top/lowest risk rankings across scored cohorts.
Reference: Task 25 Validation Requirements.
"""

from typing import Dict, Any, List
import numpy as np
import pandas as pd


def compute_validation_summary(df_scores: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate comprehensive statistical and coverage summary for scored cohort.
    """
    n_total = len(df_scores)
    n_scored = int(df_scores["risk_score"].notna().sum())
    n_failures = n_total - n_scored

    # Missing dimension tracking
    missing_thermal = int((df_scores["thermal_dimension_score"] == 0.0).sum())
    missing_persistence = int((df_scores["persistence_dimension_score"] == 0.0).sum())
    no_industrial_match = int((df_scores["industrial_dimension_score"] == 0.0).sum())
    missing_spatial = int((df_scores["spatial_dimension_score"] == 0.0).sum())
    missing_spectral = int((df_scores["spectral_dimension_score"] == 0.0).sum())

    # Score distribution statistics
    scores = df_scores["risk_score"].values
    score_min = float(np.min(scores)) if n_scored > 0 else 0.0
    score_max = float(np.max(scores)) if n_scored > 0 else 0.0
    score_mean = float(np.mean(scores)) if n_scored > 0 else 0.0
    score_median = float(np.median(scores)) if n_scored > 0 else 0.0
    score_std = float(np.std(scores)) if n_scored > 0 else 0.0
    score_percentiles = {
        "p10": float(np.percentile(scores, 10)) if n_scored > 0 else 0.0,
        "p25": float(np.percentile(scores, 25)) if n_scored > 0 else 0.0,
        "p50": float(np.percentile(scores, 50)) if n_scored > 0 else 0.0,
        "p75": float(np.percentile(scores, 75)) if n_scored > 0 else 0.0,
        "p90": float(np.percentile(scores, 90)) if n_scored > 0 else 0.0,
    }

    # Risk tier counts and percentages
    tier_order = ["LOW", "MODERATE", "HIGH", "CRITICAL"]
    tier_counts = {}
    tier_pcts = {}
    for t in tier_order:
        cnt = int((df_scores["risk_tier"] == t).sum())
        tier_counts[t] = cnt
        tier_pcts[t] = round((cnt / n_total) * 100.0, 1) if n_total > 0 else 0.0

    # Confidence distribution
    confs = df_scores["evidence_confidence"].values
    conf_min = float(np.min(confs)) if n_scored > 0 else 0.0
    conf_max = float(np.max(confs)) if n_scored > 0 else 0.0
    conf_mean = float(np.mean(confs)) if n_scored > 0 else 0.0
    conf_median = float(np.median(confs)) if n_scored > 0 else 0.0
    conf_std = float(np.std(confs)) if n_scored > 0 else 0.0

    conf_tier_order = ["LOW", "MEDIUM", "HIGH"]
    conf_tier_counts = {}
    conf_tier_pcts = {}
    for ct in conf_tier_order:
        cnt = int((df_scores["confidence_tier"] == ct).sum())
        conf_tier_counts[ct] = cnt
        conf_tier_pcts[ct] = round((cnt / n_total) * 100.0, 1) if n_total > 0 else 0.0

    # Top-5 and Lowest-5 events
    cols_rank = [
        "event_id", "risk_score", "risk_tier", "evidence_confidence", "confidence_tier",
        "weighted_thermal", "weighted_persistence", "weighted_industrial", "weighted_spatial", "weighted_spectral",
        "worldcover_class_name", "osm_primary_category"
    ]
    avail_cols = [c for c in cols_rank if c in df_scores.columns]
    top_5 = df_scores.sort_values(by=["risk_score", "evidence_confidence"], ascending=[False, False]).head(5)[avail_cols].to_dict(orient="records")
    lowest_5 = df_scores.sort_values(by=["risk_score", "evidence_confidence"], ascending=[True, True]).head(5)[avail_cols].to_dict(orient="records")

    return {
        "coverage": {
            "total_events": n_total,
            "successfully_scored": n_scored,
            "failures": n_failures,
            "zero_thermal_events": missing_thermal,
            "zero_persistence_events": missing_persistence,
            "no_industrial_match_events": no_industrial_match,
            "zero_spatial_events": missing_spatial,
            "missing_or_zero_spectral_events": missing_spectral,
        },
        "score_distribution": {
            "min": round(score_min, 2),
            "max": round(score_max, 2),
            "mean": round(score_mean, 2),
            "median": round(score_median, 2),
            "std": round(score_std, 2),
            "percentiles": score_percentiles,
        },
        "risk_tiers": {
            "counts": tier_counts,
            "percentages": tier_pcts,
        },
        "confidence_distribution": {
            "min": round(conf_min, 2),
            "max": round(conf_max, 2),
            "mean": round(conf_mean, 2),
            "median": round(conf_median, 2),
            "std": round(conf_std, 2),
            "tier_counts": conf_tier_counts,
            "tier_percentages": conf_tier_pcts,
        },
        "top_5_events": top_5,
        "lowest_5_events": lowest_5,
    }


# Alias for execution convenience
validate_pilot_results = compute_validation_summary


def format_validation_report(summary: Dict[str, Any]) -> str:
    """Format the validation summary dictionary into a clean markdown/text report."""
    cov = summary["coverage"]
    sc = summary["score_distribution"]
    rt = summary["risk_tiers"]
    cd = summary["confidence_distribution"]

    lines = [
        "==================================================================",
        "          THERMOGUARD DETERMINISTIC RISK ENGINE VALIDATION        ",
        "==================================================================",
        f"1. COVERAGE:",
        f"   - Total Events Processed:        {cov['total_events']}",
        f"   - Successfully Scored:          {cov['successfully_scored']}",
        f"   - Failures:                     {cov['failures']}",
        f"   - Zero/Missing Thermal:         {cov['zero_thermal_events']}",
        f"   - Zero/Missing Persistence:     {cov['zero_persistence_events']}",
        f"   - No Industrial OSM Match:      {cov['no_industrial_match_events']}",
        f"   - Zero/Missing Spatial:         {cov['zero_spatial_events']}",
        f"   - Missing/Zero Spectral (S2):   {cov['missing_or_zero_spectral_events']}",
        "",
        f"2. RISK SCORE DISTRIBUTION (Scale 0-100):",
        f"   - Min:       {sc['min']:.1f}",
        f"   - Max:       {sc['max']:.1f}",
        f"   - Mean:      {sc['mean']:.1f}",
        f"   - Median:    {sc['median']:.1f}",
        f"   - Std Dev:   {sc['std']:.1f}",
        f"   - P10: {sc['percentiles']['p10']:.1f} | P25: {sc['percentiles']['p25']:.1f} | P50: {sc['percentiles']['p50']:.1f} | P75: {sc['percentiles']['p75']:.1f} | P90: {sc['percentiles']['p90']:.1f}",
        "",
        f"3. RISK TIERS (Methodology Defined):",
    ]
    for tier, count in rt["counts"].items():
        pct = rt["percentages"][tier]
        lines.append(f"   - {tier:<9}: {count:>3} ({pct:>5.1f}%)")

    lines.extend([
        "",
        f"4. EVIDENCE CONFIDENCE DISTRIBUTION (Scale 0-100):",
        f"   - Min:       {cd['min']:.1f}",
        f"   - Max:       {cd['max']:.1f}",
        f"   - Mean:      {cd['mean']:.1f}",
        f"   - Median:    {cd['median']:.1f}",
        f"   - Std Dev:   {cd['std']:.1f}",
        "   - Tiers:",
    ])
    for tier, count in cd["tier_counts"].items():
        pct = cd["tier_percentages"][tier]
        lines.append(f"     * {tier:<6}: {count:>3} ({pct:>5.1f}%)")

    lines.extend([
        "",
        f"5. TOP 5 RISK EVENTS:",
    ])
    for ev in summary["top_5_events"]:
        lines.append(
            f"   - ID: {ev.get('event_id')} | Score: {ev.get('risk_score')} ({ev.get('risk_tier')}) | "
            f"Conf: {ev.get('evidence_confidence')} ({ev.get('confidence_tier')}) | "
            f"Weights: [Th: {ev.get('weighted_thermal',0):.2f}, Pe: {ev.get('weighted_persistence',0):.2f}, "
            f"In: {ev.get('weighted_industrial',0):.2f}, Sp: {ev.get('weighted_spatial',0):.2f}, "
            f"Sc: {ev.get('weighted_spectral',0):.2f}] | OSM: {ev.get('osm_primary_category')}"
        )

    lines.extend([
        "",
        f"6. LOWEST 5 RISK EVENTS:",
    ])
    for ev in summary["lowest_5_events"]:
        lines.append(
            f"   - ID: {ev.get('event_id')} | Score: {ev.get('risk_score')} ({ev.get('risk_tier')}) | "
            f"Conf: {ev.get('evidence_confidence')} ({ev.get('confidence_tier')}) | "
            f"Weights: [Th: {ev.get('weighted_thermal',0):.2f}, Pe: {ev.get('weighted_persistence',0):.2f}, "
            f"In: {ev.get('weighted_industrial',0):.2f}, Sp: {ev.get('weighted_spatial',0):.2f}, "
            f"Sc: {ev.get('weighted_spectral',0):.2f}] | OSM: {ev.get('osm_primary_category')}"
        )

    lines.append("==================================================================")
    return "\n".join(lines)
