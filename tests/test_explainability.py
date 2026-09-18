"""
tests/test_explainability.py

Task 28 Test Suite: Verifies the Deterministic Explainability Layer.

Covers all 12 requirements specified in Task 28 Part J:
1. Correct contribution calculation (normalized [0,1] -> points on [0,100] scale)
2. Dimension ranking (primary, secondary, weakest/absent)
3. Missing evidence categorization & transparent narratives
4. Stale Sentinel-2 handling ("evidence limitation, not evidence of absence")
5. Low confidence handling (identifies insufficient evidence)
6. High confidence handling (corroborates active evidence)
7. Risk / confidence separation (no scaling, capping, or multiplication)
8. No fabricated evidence (only real fields exposed)
9. No hidden numerical scores (recommendations based only on existing tiers)
10. Exact reproducibility (bit-for-bit identical across runs)
11. Methodology version traceability (PhaseIX-2026-09-14 present everywhere)
12. Top/bottom pilot events validation
"""

import unittest
import math
import copy
from pathlib import Path
import pandas as pd

from risk_engine.scoring import score_event, METHODOLOGY_VERSION
from risk_engine.explanation import (
    generate_comprehensive_explanation,
    rank_dimension_contributions,
    extract_raw_evidence_trace,
    categorize_missing_stale_evidence,
    extract_confidence_breakdown,
    generate_analyst_interpretations,
    determine_investigation_priority,
    format_analyst_markdown,
)


class TestExplainabilityLayer(unittest.TestCase):

    def setUp(self):
        # Full reference event
        self.sample_event = {
            "event_id": "TEST_EXP_001",
            "frp_mean": 40.0,
            "frp_max": 200.0,
            "brightness_mean": 340.0,
            "distinct_detection_days": 150,
            "detection_count": 12000,
            "osm_matched_fraction": 0.85,
            "osm_containment_fraction": 0.60,
            "osm_proximity_fraction": 0.75,
            "min_distance_m": 50.0,
            "spatial_extent_km2": 60.0,
            "has_satellite_scene": 1,
            "has_spectral_features": 1,
            "swir2_anomaly_ratio": 3.0,
            "ndvi": 0.15,
            "swir2_swir1_ratio": 1.1,
            "bsi": 0.10,
            "scl_clear_fraction": 0.90,
            "temporal_delta_days": 5.0,
            "distinct_satellites": 3,
            "worldcover_class_name": "Built-up",
            "osm_primary_category": "industrial",
            "osm_tier": 1,
        }
        self.scored_sample = score_event(self.sample_event)
        self.explanation = generate_comprehensive_explanation(self.scored_sample)

    def test_1_correct_contribution_calculation(self):
        """1. Verify weighted contribution points match normalized score * weight * 100."""
        breakdown = self.explanation["score_breakdown"]
        weights = {"thermal": 0.30, "persistence": 0.25, "industrial": 0.20, "spatial": 0.10, "spectral": 0.15}
        total_points = 0.0

        for dim_key, expected_weight in weights.items():
            b = breakdown[dim_key]
            self.assertEqual(b["weight"], expected_weight)
            expected_points = round(b["normalized_score"] * expected_weight * 100.0, 1)
            self.assertAlmostEqual(b["weighted_contribution_points"], expected_points, delta=0.2)
            total_points += b["weighted_contribution_points"]

        # Sum of weighted contribution points should match final risk score within rounding
        self.assertAlmostEqual(total_points, self.explanation["final_risk_score"], delta=0.5)

    def test_2_dimension_ranking(self):
        """2. Verify dimension ranking orders correctly and identifies primary/secondary/weakest."""
        ranking = self.explanation["contribution_ranking"]
        ranked_dims = ranking["ranked_dimensions"]

        # Ensure sorted descending
        for i in range(len(ranked_dims) - 1):
            self.assertGreaterEqual(ranked_dims[i]["points"], ranked_dims[i+1]["points"])

        primary = ranking["primary_driver"]
        secondary = ranking["secondary_driver"]
        weakest = ranking["weakest_dimension"]

        self.assertEqual(primary["code"], ranked_dims[0]["code"])
        self.assertEqual(secondary["code"], ranked_dims[1]["code"])
        self.assertEqual(weakest["code"], ranked_dims[-1]["code"])

        self.assertIn("points", primary["formatted"])
        self.assertIn(str(primary["points"]), primary["formatted"])

    def test_3_missing_evidence(self):
        """3. Verify missing evidence lists missing tags and doesn't redistribute weights."""
        event_missing_c = copy.deepcopy(self.sample_event)
        event_missing_c["osm_matched_fraction"] = None
        event_missing_c["osm_containment_fraction"] = None
        event_missing_c["osm_proximity_fraction"] = None
        event_missing_c["min_distance_m"] = None

        scored_no_c = score_event(event_missing_c)
        exp_no_c = generate_comprehensive_explanation(scored_no_c)

        missing_info = exp_no_c["missing_and_stale_evidence"]
        self.assertEqual(missing_info["status_by_dimension"]["industrial"], "MISSING")
        self.assertEqual(exp_no_c["score_breakdown"]["industrial"]["weighted_contribution_points"], 0.0)

        # Remaining dimensions must retain their original weights
        self.assertEqual(exp_no_c["score_breakdown"]["thermal"]["weight"], 0.30)
        self.assertEqual(exp_no_c["score_breakdown"]["persistence"]["weight"], 0.25)
        self.assertEqual(exp_no_c["score_breakdown"]["spatial"]["weight"], 0.10)
        self.assertEqual(exp_no_c["score_breakdown"]["spectral"]["weight"], 0.15)

    def test_4_stale_sentinel2(self):
        """4. Verify stale Sentinel-2 (>90 days) produces exact limitation message, NOT 'no fire'."""
        event_stale = copy.deepcopy(self.sample_event)
        event_stale["temporal_delta_days"] = 120.0  # > 90 days = stale, rel = 0.0

        scored_stale = score_event(event_stale)
        exp_stale = generate_comprehensive_explanation(scored_stale)

        s2_exp = exp_stale["missing_and_stale_evidence"]["sentinel2_explanation"]
        self.assertIn("evidence limitation, not evidence of absence", s2_exp)
        self.assertNotIn("found no evidence of fire", s2_exp)
        self.assertEqual(exp_stale["score_breakdown"]["spectral"]["weighted_contribution_points"], 0.0)

    def test_5_low_confidence(self):
        """5. Verify Low Risk + Low Confidence is recognized as insufficient evidence, NOT verified safety."""
        sparse_event = {
            "event_id": "SPARSE_001",
            "frp_mean": 2.0,
            "frp_max": 5.0,
            "brightness_mean": 305.0,
            "distinct_detection_days": 1,
            "detection_count": 1,
            "distinct_satellites": 1,
            "has_satellite_scene": 0,
            "has_spectral_features": 0,
        }
        scored_sparse = score_event(sparse_event)
        exp_sparse = generate_comprehensive_explanation(scored_sparse)

        rec = exp_sparse["investigation_priority"]["recommendation"]
        self.assertEqual(rec, "Low observed risk but insufficient evidence")
        rationale = exp_sparse["investigation_priority"]["rationale"]
        self.assertIn("absence of data rather than confirmed absence of hazard", rationale)

    def test_6_high_confidence(self):
        """6. Verify High Risk + High Confidence produces 'Priority investigation target'."""
        strong_event = copy.deepcopy(self.sample_event)
        strong_event["frp_mean"] = 80.0
        strong_event["frp_max"] = 400.0
        strong_event["distinct_detection_days"] = 300
        strong_event["detection_count"] = 40000
        strong_event["min_distance_m"] = 0.0
        strong_event["osm_matched_fraction"] = 1.0
        strong_event["osm_containment_fraction"] = 1.0
        strong_event["osm_proximity_fraction"] = 1.0
        strong_event["distinct_satellites"] = 4
        strong_event["temporal_delta_days"] = 1.0

        scored_strong = score_event(strong_event)
        exp_strong = generate_comprehensive_explanation(scored_strong)

        self.assertIn(exp_strong["risk_tier"], ("HIGH", "CRITICAL"))
        self.assertEqual(exp_strong["confidence_tier"], "HIGH")
        rec = exp_strong["investigation_priority"]["recommendation"]
        self.assertEqual(rec, "Priority investigation target")

    def test_7_risk_confidence_separation(self):
        """7. Verify Risk Score and Evidence Confidence are mathematically independent."""
        sep = self.explanation["evidence_confidence_breakdown"]["separation_statement"]
        self.assertIn("does NOT multiply, cap, boost, or alter the numerical Risk Score", sep)

        # Perturbing distinct_satellites alters confidence but NOT risk score
        ev1 = copy.deepcopy(self.sample_event)
        ev1["distinct_satellites"] = 1
        ev2 = copy.deepcopy(self.sample_event)
        ev2["distinct_satellites"] = 5

        res1 = score_event(ev1)
        res2 = score_event(ev2)
        exp1 = generate_comprehensive_explanation(res1)
        exp2 = generate_comprehensive_explanation(res2)

        self.assertEqual(exp1["final_risk_score"], exp2["final_risk_score"])
        self.assertNotEqual(exp1["evidence_confidence"], exp2["evidence_confidence"])

    def test_8_no_fabricated_evidence(self):
        """8. Verify raw evidence trace only exposes present fields and does not fabricate data."""
        partial_ev = {
            "event_id": "PARTIAL_001",
            "frp_mean": 25.0,
            # frp_max, brightness_mean omitted
            "distinct_detection_days": 10,
            # detection_count omitted
            "min_distance_m": 500.0,
            # osm fractions omitted
        }
        scored_p = score_event(partial_ev)
        trace = extract_raw_evidence_trace(scored_p["dimensions"])

        self.assertIn("frp_mean", trace["thermal"])
        self.assertNotIn("frp_max", trace["thermal"])
        self.assertNotIn("brightness_mean", trace["thermal"])
        self.assertIn("distinct_detection_days", trace["persistence"])
        self.assertNotIn("detection_count", trace["persistence"])
        self.assertIn("min_distance_m", trace["industrial"])
        self.assertNotIn("osm_containment_fraction", trace["industrial"])

    def test_9_no_hidden_numerical_score(self):
        """9. Verify recommendation is rule-based and contains no hidden second numerical score."""
        prio = self.explanation["investigation_priority"]
        rec = prio["recommendation"]
        allowed_recommendations = [
            "Priority investigation target",
            "Priority target — needs corroborating verification",
            "Routine monitoring target",
            "Needs additional satellite verification",
            "Confident low-risk event",
            "Low observed risk but insufficient evidence",
            "Routine low-priority monitoring",
        ]
        self.assertIn(rec, allowed_recommendations)
        self.assertNotIn("score", prio)
        self.assertNotIn("composite_score", prio)

    def test_10_exact_reproducibility(self):
        """10. Verify identical events produce bit-for-bit identical explanation dictionaries."""
        exp_a = generate_comprehensive_explanation(score_event(self.sample_event))
        exp_b = generate_comprehensive_explanation(score_event(self.sample_event))
        self.assertEqual(exp_a, exp_b)

    def test_11_methodology_version_traceability(self):
        """11. Verify methodology version is explicitly traced across explanation structure."""
        self.assertEqual(self.explanation["methodology_version"], METHODOLOGY_VERSION)
        self.assertEqual(self.explanation["methodology_version"], "PhaseIX-2026-09-14")

    def test_12_top_bottom_pilot_events(self):
        """12. Verify explanations for actual top and bottom pilot events."""
        from repo_paths import find_processed_file

        pilot_path = find_processed_file("firms_satellite_enriched_pilot.parquet")
        if pilot_path is None:
            self.skipTest("Pilot parquet not found (set THERMOGUARD_DATA_ROOT or add data/satellite/processed)")

        df = pd.read_parquet(pilot_path)
        top_row = df[df["event_id"] == "EVT_00963466"].iloc[0].to_dict()
        low_row = df[df["event_id"] == "EVT_01035117"].iloc[0].to_dict()

        top_exp = generate_comprehensive_explanation(score_event(top_row))
        low_exp = generate_comprehensive_explanation(score_event(low_row))

        # Top event verification
        self.assertEqual(top_exp["final_risk_score"], 49.0)
        self.assertEqual(top_exp["contribution_ranking"]["primary_driver"]["code"], "B")
        self.assertIn("Persistence", top_exp["contribution_ranking"]["primary_driver"]["name"])
        self.assertGreaterEqual(top_exp["contribution_ranking"]["primary_driver"]["points"], 24.0)

        # Low event verification
        self.assertLess(low_exp["final_risk_score"], 20.0)
        self.assertIn(low_exp["risk_tier"], ("LOW", "MODERATE"))


if __name__ == "__main__":
    unittest.main()
