"""
Unit tests for ThermoGuard Phase IX Deterministic Risk Engine.

Verifies:
1. Normal valid event (matches hypothetical documented example in Section 12).
2. Minimum/maximum normalization boundaries.
3. Missing thermal evidence.
4. Missing persistence evidence.
5. Missing industrial evidence.
6. Missing spatial evidence.
7. Missing spectral evidence.
8. Missing multiple dimensions.
9. No OSM match.
10. Zero-distance edge case.
11. Zero/near-zero thermal values.
12. Extreme thermal values.
13. Single-detection event.
14. Multiple-detection event.
15. Missing Sentinel-2 evidence (no scene / extraction error).
16. distinct_satellites confidence behavior.
17. WorldCover does not alter risk score.
18. OSM category/tier does not introduce an undocumented risk bonus.
19. Final score remains within methodology-defined range [0, 100].
20. Determinism: identical input produces identical output.
21. Monotonicity checks across all positive risk features.
"""

import unittest
import numpy as np

from risk_engine.scoring import score_event, get_risk_tier
from risk_engine.confidence import get_confidence_tier
from risk_engine.normalization import (
    normalize_frp_mean,
    normalize_frp_max,
    normalize_brightness,
    normalize_persistence_days,
    normalize_detection_count,
    normalize_osm_proximity,
    normalize_spatial_extent,
    normalize_swir_anomaly,
    normalize_ndvi,
    normalize_bsi,
    normalize_swir_ratio,
)


class TestRiskEngine(unittest.TestCase):

    def setUp(self):
        # Base event from Section 12 (hypothetical example)
        self.base_event = {
            "event_id": "EVT_TEST_BASE",
            "frp_mean": 18.0,
            "frp_max": 45.0,
            "brightness_mean": 340.0,
            "distinct_detection_days": 210,
            "detection_count": 5000,
            "spatial_extent_km2": 12.0,
            "distinct_satellites": 3,
            "has_osm_industrial_match": 1,
            "osm_matched_fraction": 0.85,
            "osm_containment_fraction": 0.70,
            "osm_proximity_fraction": 0.90,
            "min_distance_m": 0.0,
            "osm_tier": 2,
            "osm_primary_category": "mine_quarry",
            "worldcover_class": 60,
            "worldcover_class_name": "Bare / sparse vegetation",
            "swir2_anomaly_ratio": 2.8,
            "ndvi": 0.12,
            "bsi": 0.15,
            "swir2_swir1_ratio": 1.3,
            "has_spectral_features": 1,
            "has_satellite_scene": 1,
            "scl_clear_fraction": 0.88,
            "temporal_delta_days": 25.0,
        }

    # 1. Normal valid event matching Section 12
    def test_01_normal_valid_event(self):
        res = score_event(self.base_event)
        self.assertEqual(res["risk_score"], 54.4)
        self.assertEqual(res["risk_tier"], "HIGH")
        self.assertEqual(res["evidence_confidence"], 77.1)
        self.assertEqual(res["confidence_tier"], "HIGH")

    # 2. Minimum/maximum normalization boundaries
    def test_02_normalization_boundaries(self):
        # Minimum boundaries
        val, miss = normalize_frp_mean(0.0)
        self.assertEqual(val, 0.0)
        val, miss = normalize_frp_max(0.0)
        self.assertEqual(val, 0.0)
        val, miss = normalize_brightness(300.0)
        self.assertEqual(val, 0.0)
        val, miss = normalize_persistence_days(0)
        self.assertEqual(val, 0.0)
        val, miss = normalize_detection_count(0)
        self.assertEqual(val, 0.0)
        val, miss = normalize_spatial_extent(0.0)
        self.assertEqual(val, 0.0)
        val, miss = normalize_swir_anomaly(0.5)
        self.assertEqual(val, 0.0)

        # Maximum boundaries
        val, miss = normalize_frp_mean(150.0)  # > 100
        self.assertEqual(val, 1.0)
        val, miss = normalize_frp_max(600.0)   # > 500
        self.assertEqual(val, 1.0)
        val, miss = normalize_brightness(380.0) # > 370
        self.assertEqual(val, 1.0)
        val, miss = normalize_persistence_days(400) # > 365
        self.assertEqual(val, 1.0)
        val, miss = normalize_detection_count(60000) # > 50000
        self.assertEqual(val, 1.0)
        val, miss = normalize_spatial_extent(600.0) # > 500
        self.assertEqual(val, 1.0)
        val, miss = normalize_swir_anomaly(7.0) # > 6.0
        self.assertEqual(val, 1.0)

    # 3. Missing thermal evidence
    def test_03_missing_thermal_evidence(self):
        ev = self.base_event.copy()
        ev["frp_mean"] = None
        ev["frp_max"] = None
        ev["brightness_mean"] = None
        res = score_event(ev)
        self.assertEqual(res["thermal_dimension_score"], 0.0)
        self.assertEqual(res["dimensions"]["thermal"]["weighted_contribution"], 0.0)
        self.assertIn("dimension_A_thermal_missing", res["missing_evidence"])

    # 4. Missing persistence evidence
    def test_04_missing_persistence_evidence(self):
        ev = self.base_event.copy()
        ev["distinct_detection_days"] = None
        ev["detection_count"] = None
        res = score_event(ev)
        self.assertEqual(res["persistence_dimension_score"], 0.0)
        self.assertEqual(res["dimensions"]["persistence"]["weighted_contribution"], 0.0)
        self.assertIn("dimension_B_persistence_missing", res["missing_evidence"])

    # 5. Missing industrial evidence
    def test_05_missing_industrial_evidence(self):
        ev = self.base_event.copy()
        ev["osm_matched_fraction"] = None
        ev["osm_containment_fraction"] = None
        ev["osm_proximity_fraction"] = None
        ev["min_distance_m"] = None
        ev["has_osm_industrial_match"] = 0
        res = score_event(ev)
        self.assertEqual(res["industrial_dimension_score"], 0.0)
        self.assertEqual(res["dimensions"]["industrial"]["weighted_contribution"], 0.0)

    # 6. Missing spatial evidence
    def test_06_missing_spatial_evidence(self):
        ev = self.base_event.copy()
        ev["spatial_extent_km2"] = None
        res = score_event(ev)
        self.assertEqual(res["spatial_dimension_score"], 0.0)
        self.assertEqual(res["dimensions"]["spatial"]["weighted_contribution"], 0.0)
        self.assertIn("dimension_D_spatial_missing", res["missing_evidence"])

    # 7. Missing spectral evidence
    def test_07_missing_spectral_evidence(self):
        ev = self.base_event.copy()
        ev["has_spectral_features"] = 0
        res = score_event(ev)
        self.assertEqual(res["spectral_dimension_score"], 0.0)
        self.assertEqual(res["dimensions"]["spectral"]["weighted_contribution"], 0.0)

    # 8. Missing multiple dimensions
    def test_08_missing_multiple_dimensions(self):
        ev = self.base_event.copy()
        ev["frp_mean"] = None
        ev["frp_max"] = None
        ev["brightness_mean"] = None
        ev["has_spectral_features"] = 0
        res = score_event(ev)
        self.assertEqual(res["thermal_dimension_score"], 0.0)
        self.assertEqual(res["spectral_dimension_score"], 0.0)
        # Verify persistence, industrial, and spatial still use their exact locked weights
        expected_raw = (
            0.25 * res["persistence_dimension_score"]
            + 0.20 * res["industrial_dimension_score"]
            + 0.10 * res["spatial_dimension_score"]
        )
        self.assertAlmostEqual(res["risk_score_raw"], expected_raw, places=4)

    # 9. No OSM match (distance is NULL or > 5000)
    def test_09_no_osm_match(self):
        ev = self.base_event.copy()
        ev["has_osm_industrial_match"] = 0
        ev["min_distance_m"] = None
        ev["osm_matched_fraction"] = 0.0
        ev["osm_containment_fraction"] = 0.0
        ev["osm_proximity_fraction"] = 0.0
        res = score_event(ev)
        self.assertEqual(res["industrial_dimension_score"], 0.0)
        self.assertIn("osm_context:no_mapped_association", res["missing_evidence"])

    # 10. Zero-distance edge case
    def test_10_zero_distance_edge_case(self):
        score, miss = normalize_osm_proximity(0.0)
        self.assertEqual(score, 1.0)
        score_neg, miss_neg = normalize_osm_proximity(-10.0)
        self.assertEqual(score_neg, 1.0)

    # 11. Zero/near-zero thermal values
    def test_11_zero_thermal_values(self):
        ev = self.base_event.copy()
        ev["frp_mean"] = 0.0
        ev["frp_max"] = 0.0
        ev["brightness_mean"] = 280.0  # < 300 K floor
        res = score_event(ev)
        self.assertEqual(res["thermal_dimension_score"], 0.0)

    # 12. Extreme thermal values
    def test_12_extreme_thermal_values(self):
        ev = self.base_event.copy()
        ev["frp_mean"] = 1500.0  # Well above 100 MW ceiling
        ev["frp_max"] = 3000.0   # Well above 500 MW ceiling
        ev["brightness_mean"] = 500.0 # Well above 370 K ceiling
        res = score_event(ev)
        self.assertEqual(res["thermal_dimension_score"], 1.0)
        self.assertEqual(res["dimensions"]["thermal"]["weighted_contribution"], 0.30)

    # 13. Single-detection event
    def test_13_single_detection_event(self):
        ev = self.base_event.copy()
        ev["distinct_detection_days"] = 1
        ev["detection_count"] = 1
        res = score_event(ev)
        self.assertGreater(res["persistence_dimension_score"], 0.0)
        self.assertLess(res["persistence_dimension_score"], 0.20)

    # 14. Multiple-detection event (high persistence)
    def test_14_multiple_detection_event(self):
        ev = self.base_event.copy()
        ev["distinct_detection_days"] = 365
        ev["detection_count"] = 50000
        res = score_event(ev)
        self.assertEqual(res["persistence_dimension_score"], 1.0)
        self.assertEqual(res["dimensions"]["persistence"]["weighted_contribution"], 0.25)

    # 15. Missing Sentinel-2 evidence (scene missing vs extraction failure)
    def test_15_missing_sentinel2_evidence(self):
        ev_no_scene = self.base_event.copy()
        ev_no_scene["has_satellite_scene"] = 0
        ev_no_scene["has_spectral_features"] = 0
        res_no_scene = score_event(ev_no_scene)
        self.assertEqual(res_no_scene["spectral_dimension_score"], 0.0)
        self.assertIn("spectral_coverage:no_scene", res_no_scene["missing_evidence"])

        ev_fail = self.base_event.copy()
        ev_fail["has_satellite_scene"] = 1
        ev_fail["has_spectral_features"] = 0
        res_fail = score_event(ev_fail)
        self.assertEqual(res_fail["spectral_dimension_score"], 0.0)
        self.assertIn("spectral_coverage:extraction_failed", res_fail["missing_evidence"])

    # 16. distinct_satellites confidence behavior
    def test_16_distinct_satellites_confidence(self):
        # 1 platform -> 0.20 corroboration
        ev1 = self.base_event.copy()
        ev1["distinct_satellites"] = 1
        res1 = score_event(ev1)

        # 5 platforms -> 1.00 corroboration
        ev5 = self.base_event.copy()
        ev5["distinct_satellites"] = 5
        res5 = score_event(ev5)

        # Risk score must NOT change based on distinct_satellites
        self.assertEqual(res1["risk_score"], res5["risk_score"])
        # Evidence confidence MUST increase with distinct_satellites
        self.assertGreater(res5["evidence_confidence"], res1["evidence_confidence"])
        # Exactly 0.30 * (1.0 - 0.2) = 0.24 raw diff = 24.0 confidence points
        diff = round(res5["confidence_details"]["score_raw"] - res1["confidence_details"]["score_raw"], 3)
        self.assertEqual(diff, 0.24)

    # 17. WorldCover does not alter risk score
    def test_17_worldcover_does_not_alter_risk(self):
        ev_bare = self.base_event.copy()
        ev_bare["worldcover_class_name"] = "Bare / sparse vegetation"
        ev_bare["worldcover_class"] = 60

        ev_tree = self.base_event.copy()
        ev_tree["worldcover_class_name"] = "Tree cover"
        ev_tree["worldcover_class"] = 10

        ev_built = self.base_event.copy()
        ev_built["worldcover_class_name"] = "Built-up"
        ev_built["worldcover_class"] = 50

        res_bare = score_event(ev_bare)
        res_tree = score_event(ev_tree)
        res_built = score_event(ev_built)

        self.assertEqual(res_bare["risk_score"], res_tree["risk_score"])
        self.assertEqual(res_bare["risk_score"], res_built["risk_score"])

    # 18. OSM category/tier does not introduce an undocumented risk bonus
    def test_18_osm_category_tier_does_not_alter_risk(self):
        ev_mine = self.base_event.copy()
        ev_mine["osm_primary_category"] = "mine_quarry"
        ev_mine["osm_tier"] = 1

        ev_sub = self.base_event.copy()
        ev_sub["osm_primary_category"] = "substation"
        ev_sub["osm_tier"] = 2

        ev_none = self.base_event.copy()
        ev_none["osm_primary_category"] = "unknown"
        ev_none["osm_tier"] = None

        res_mine = score_event(ev_mine)
        res_sub = score_event(ev_sub)
        res_none = score_event(ev_none)

        self.assertEqual(res_mine["risk_score"], res_sub["risk_score"])
        self.assertEqual(res_mine["risk_score"], res_none["risk_score"])

    # 19. Final score remains within the methodology-defined range [0, 100]
    def test_19_final_score_range(self):
        # Absolute zero event
        ev_zero = {k: 0.0 for k in self.base_event}
        ev_zero["event_id"] = "EVT_ZERO"
        res_zero = score_event(ev_zero)
        self.assertGreaterEqual(res_zero["risk_score"], 0.0)
        self.assertLessEqual(res_zero["risk_score"], 100.0)

        # Extreme maximum event
        ev_max = {
            "event_id": "EVT_MAX",
            "frp_mean": 500.0,
            "frp_max": 2000.0,
            "brightness_mean": 450.0,
            "distinct_detection_days": 500,
            "detection_count": 100000,
            "spatial_extent_km2": 1000.0,
            "distinct_satellites": 5,
            "has_osm_industrial_match": 1,
            "osm_matched_fraction": 1.0,
            "osm_containment_fraction": 1.0,
            "osm_proximity_fraction": 1.0,
            "min_distance_m": 0.0,
            "swir2_anomaly_ratio": 10.0,
            "ndvi": -0.5,
            "bsi": 0.8,
            "swir2_swir1_ratio": 3.0,
            "has_spectral_features": 1,
            "has_satellite_scene": 1,
            "scl_clear_fraction": 1.0,
            "temporal_delta_days": 0.0,
        }
        res_max = score_event(ev_max)
        self.assertGreaterEqual(res_max["risk_score"], 0.0)
        self.assertLessEqual(res_max["risk_score"], 100.0)
        self.assertEqual(res_max["risk_score"], 100.0)
        self.assertEqual(res_max["risk_tier"], "CRITICAL")
        self.assertEqual(res_max["evidence_confidence"], 100.0)
        self.assertEqual(res_max["confidence_tier"], "HIGH")

    # 20. Determinism: identical input produces identical output
    def test_20_determinism(self):
        res1 = score_event(self.base_event)
        res2 = score_event(self.base_event)
        self.assertEqual(res1["risk_score"], res2["risk_score"])
        self.assertEqual(res1["risk_score_raw"], res2["risk_score_raw"])
        self.assertEqual(res1["evidence_confidence"], res2["evidence_confidence"])
        self.assertEqual(res1["dimensions"], res2["dimensions"])

    # 21. Monotonicity checks
    def test_21_monotonicity_checks(self):
        # FRP mean monotonicity
        ev_low_frp = self.base_event.copy()
        ev_low_frp["frp_mean"] = 10.0
        ev_high_frp = self.base_event.copy()
        ev_high_frp["frp_mean"] = 50.0
        self.assertLessEqual(
            score_event(ev_low_frp)["thermal_dimension_score"],
            score_event(ev_high_frp)["thermal_dimension_score"]
        )

        # Persistence days monotonicity
        ev_low_days = self.base_event.copy()
        ev_low_days["distinct_detection_days"] = 10
        ev_high_days = self.base_event.copy()
        ev_high_days["distinct_detection_days"] = 100
        self.assertLessEqual(
            score_event(ev_low_days)["persistence_dimension_score"],
            score_event(ev_high_days)["persistence_dimension_score"]
        )

        # Distance monotonicity: increasing distance must decrease proximity score
        ev_near = self.base_event.copy()
        ev_near["min_distance_m"] = 500.0
        ev_far = self.base_event.copy()
        ev_far["min_distance_m"] = 3000.0
        self.assertGreaterEqual(
            score_event(ev_near)["industrial_dimension_score"],
            score_event(ev_far)["industrial_dimension_score"]
        )

        # SWIR anomaly contrast monotonicity
        ev_low_swir = self.base_event.copy()
        ev_low_swir["swir2_anomaly_ratio"] = 1.5
        ev_high_swir = self.base_event.copy()
        ev_high_swir["swir2_anomaly_ratio"] = 4.0
        self.assertLessEqual(
            score_event(ev_low_swir)["spectral_dimension_score"],
            score_event(ev_high_swir)["spectral_dimension_score"]
        )


if __name__ == "__main__":
    unittest.main()
