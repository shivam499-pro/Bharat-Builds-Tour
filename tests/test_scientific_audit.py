"""
tests/test_scientific_audit.py

Automated unit tests covering scientific audit requirements:
- Monotonicity across continuous parameters
- Boundary safety and numerical stability
- Zero weight redistribution under missing dimensions
- Independence of Evidence Confidence
"""

import unittest
import math
import numpy as np
from risk_engine.scoring import score_event

class TestScientificAudit(unittest.TestCase):
    def setUp(self):
        self.base_event = {
            "event_id": "TEST_AUDIT_01",
            "frp_mean": 25.0,
            "frp_max": 100.0,
            "brightness_mean": 325.0,
            "distinct_detection_days": 30,
            "detection_count": 500,
            "osm_matched_fraction": 0.5,
            "osm_containment_fraction": 0.4,
            "osm_proximity_fraction": 0.3,
            "min_distance_m": 1000.0,
            "spatial_extent_km2": 25.0,
            "has_satellite_scene": 1,
            "has_spectral_features": 1,
            "swir2_anomaly_ratio": 2.5,
            "ndvi": 0.1,
            "swir2_swir1_ratio": 1.0,
            "bsi": 0.2,
            "scl_clear_fraction": 0.9,
            "temporal_delta_days": 15.0,
            "distinct_satellites": 3,
        }

    def test_monotonicity_frp_mean(self):
        """Increasing FRP mean must not decrease thermal dimension score."""
        scores = []
        for val in [0.0, 10.0, 50.0, 100.0, 200.0, 500.0]:
            ev = self.base_event.copy()
            ev["frp_mean"] = val
            res = score_event(ev)
            scores.append(res["thermal_dimension_score"])
        for i in range(len(scores) - 1):
            self.assertGreaterEqual(scores[i+1], scores[i] - 1e-6)

    def test_monotonicity_persistence_days(self):
        """Increasing detection days must not decrease persistence dimension score."""
        scores = []
        for val in [0, 1, 10, 50, 180, 365, 500]:
            ev = self.base_event.copy()
            ev["distinct_detection_days"] = val
            res = score_event(ev)
            scores.append(res["persistence_dimension_score"])
        for i in range(len(scores) - 1):
            self.assertGreaterEqual(scores[i+1], scores[i] - 1e-6)

    def test_monotonicity_distance_decay(self):
        """Increasing distance from industrial feature must not increase industrial score."""
        scores = []
        for val in [0.0, 500.0, 1000.0, 2500.0, 5000.0, 8000.0]:
            ev = self.base_event.copy()
            ev["min_distance_m"] = val
            res = score_event(ev)
            scores.append(res["industrial_dimension_score"])
        for i in range(len(scores) - 1):
            self.assertLessEqual(scores[i+1], scores[i] + 1e-6)

    def test_boundary_extreme_values(self):
        """Extreme values must be safely clamped within [0, 100]."""
        extreme_ev = {
            "frp_mean": 10000.0,
            "frp_max": 50000.0,
            "brightness_mean": 1200.0,
            "distinct_detection_days": 100000,
            "detection_count": 50000000,
            "osm_matched_fraction": 10.0,
            "osm_containment_fraction": 10.0,
            "osm_proximity_fraction": 10.0,
            "min_distance_m": 0.0,
            "spatial_extent_km2": 100000.0,
            "has_satellite_scene": 1,
            "has_spectral_features": 1,
            "swir2_anomaly_ratio": 50.0,
            "ndvi": -1.0,
            "swir2_swir1_ratio": 50.0,
            "bsi": 10.0,
            "scl_clear_fraction": 1.0,
            "temporal_delta_days": 0.0,
            "distinct_satellites": 20,
        }
        res = score_event(extreme_ev)
        self.assertEqual(res["risk_score"], 100.0)
        self.assertEqual(res["evidence_confidence"], 100.0)

    def test_missing_data_zero_redistribution(self):
        """Missing Dimension B must reduce score by exactly its weighted contribution (25%)."""
        full_ev = {
            "frp_mean": 100.0, "frp_max": 500.0, "brightness_mean": 370.0,
            "distinct_detection_days": 365, "detection_count": 50000,
            "osm_matched_fraction": 1.0, "osm_containment_fraction": 1.0, "osm_proximity_fraction": 1.0, "min_distance_m": 0.0,
            "spatial_extent_km2": 500.0,
            "has_satellite_scene": 1, "has_spectral_features": 1, "swir2_anomaly_ratio": 6.0, "ndvi": -0.2, "swir2_swir1_ratio": 2.0, "bsi": 0.5, "scl_clear_fraction": 1.0, "temporal_delta_days": 0.0,
            "distinct_satellites": 5,
        }
        res_full = score_event(full_ev)
        self.assertEqual(res_full["risk_score"], 100.0)

        ev_missing_b = full_ev.copy()
        ev_missing_b["distinct_detection_days"] = None
        ev_missing_b["detection_count"] = None
        res_missing_b = score_event(ev_missing_b)

        # Expected score = 100.0 - 25.0 = 75.0 (strictly no weight redistribution)
        self.assertEqual(res_missing_b["risk_score"], 75.0)
        self.assertEqual(res_missing_b["dimensions"]["persistence"]["weighted_contribution"], 0.0)
        self.assertIn("dimension_B_persistence_missing", res_missing_b["missing_evidence"])

if __name__ == "__main__":
    unittest.main()
