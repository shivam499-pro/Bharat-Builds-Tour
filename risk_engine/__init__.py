"""
ThermoGuard Phase IX - Deterministic Risk Engine.

Locked 5-Dimension Additive Model:
- A: Thermal Intensity (30%)
- B: Persistence (25%)
- C: Industrial / Contextual Association (20%)
- D: Spatial Scale (10%)
- E: Spectral / Surface Evidence (15%)
Total: 100%

Evidence Confidence strictly separated (0-100).
WorldCover and OSM Categories/Tiers are context only.
"""

from .normalization import METHODOLOGY_VERSION
from .scoring import score_event, score_dataframe, get_risk_tier
from .confidence import compute_evidence_confidence, get_confidence_tier
from .explanation import (
    generate_audit_explanation,
    format_text_explanation,
    generate_comprehensive_explanation,
    format_analyst_markdown,
    rank_dimension_contributions,
    extract_raw_evidence_trace,
    categorize_missing_stale_evidence,
    extract_confidence_breakdown,
    generate_analyst_interpretations,
    determine_investigation_priority,
)
from .validation import compute_validation_summary

__all__ = [
    "METHODOLOGY_VERSION",
    "score_event",
    "score_dataframe",
    "get_risk_tier",
    "compute_evidence_confidence",
    "get_confidence_tier",
    "generate_audit_explanation",
    "format_text_explanation",
    "generate_comprehensive_explanation",
    "format_analyst_markdown",
    "rank_dimension_contributions",
    "extract_raw_evidence_trace",
    "categorize_missing_stale_evidence",
    "extract_confidence_breakdown",
    "generate_analyst_interpretations",
    "determine_investigation_priority",
    "compute_validation_summary",
]
