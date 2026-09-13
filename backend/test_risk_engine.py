import sys
import unittest
from pathlib import Path

# Ensure backend directory is in python path
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from risk_engine import RiskEngine


class TestRiskEngine(unittest.TestCase):
    """
    Unit test suite for CineGuard AI Phase 6 Calibrated Risk Engine.
    Tests all 10 required behavioral scoring, progressive escalation,
    hysteresis alerting, score drop after behavior ends, and safety rules.
    """

    def setUp(self):
        """Initialize fresh RiskEngine instance before each test."""
        self.engine = RiskEngine(
            camera_id="CAM-TEST",
            alert_threshold=70,
            state_timeout_seconds=3.0,
        )

    def test_1_no_phone_low_risk(self):
        """Test 1: No phone detected results in 0 risk score and NORMAL state."""
        record = {
            "timestamp_seconds": 1.0,
            "phone_track_id": None,
            "person_track_id": 1,
            "phone_detected": False,
            "person_detected": True,
            "phone_near_person": False,
            "phone_in_screen_region": False,
            "duration_seconds": 0.0,
        }
        assessment = self.engine.evaluate_record(record)
        self.assertEqual(assessment["risk_score"], 0)
        self.assertEqual(assessment["classification"], "NORMAL")
        self.assertIsNone(assessment["alert_event"])
        self.assertTrue(assessment["human_verification_required"])

    def test_2_phone_detected_briefly(self):
        """Test 2: Brief phone detection (<2s, no screen match) yields low risk (15) and NORMAL state."""
        record = {
            "timestamp_seconds": 1.0,
            "phone_track_id": 1,
            "person_track_id": None,
            "phone_detected": True,
            "person_detected": False,
            "phone_near_person": False,
            "phone_in_screen_region": False,
            "duration_seconds": 0.5,
        }
        assessment = self.engine.evaluate_record(record)
        self.assertEqual(assessment["risk_score"], 15)
        self.assertEqual(assessment["classification"], "NORMAL")
        self.assertIn("Mobile device detected", assessment["reasons"])

    def test_3_person_phone_association(self):
        """Test 3: Phone + Person association increases risk score to 30 (NORMAL)."""
        record = {
            "timestamp_seconds": 1.0,
            "phone_track_id": 1,
            "person_track_id": 2,
            "phone_detected": True,
            "person_detected": True,
            "phone_near_person": True,
            "phone_in_screen_region": False,
            "duration_seconds": 1.0,
        }
        assessment = self.engine.evaluate_record(record)
        # Expected: +15 (phone) +15 (association) = 30
        self.assertEqual(assessment["risk_score"], 30)
        self.assertEqual(assessment["classification"], "NORMAL")

    def test_4_sustained_screen_region_behavior(self):
        """Test 4: Sustained screen region behavior (>5s) yields high risk score (75) & SUSPECTED_RECORDING state."""
        record = {
            "timestamp_seconds": 6.0,
            "phone_track_id": 1,
            "person_track_id": 2,
            "phone_detected": True,
            "person_detected": True,
            "phone_near_person": True,
            "phone_in_screen_region": True,
            "duration_seconds": 6.0,
        }
        assessment = self.engine.evaluate_record(record)
        # Expected: +15 (phone) +15 (assoc) +20 (screen) +25 (sustained full) = 75
        self.assertEqual(assessment["risk_score"], 75)
        self.assertEqual(assessment["classification"], "SUSPECTED_RECORDING")
        self.assertIn("Device located within configured screen region", assessment["reasons"])

    def test_5_risk_threshold_crossing_single_alert(self):
        """Test 5: Crossing alert threshold (30 -> 75) generates exactly one alert event."""
        rec_low = {
            "timestamp_seconds": 1.0,
            "phone_track_id": 1,
            "person_track_id": 2,
            "phone_detected": True,
            "person_detected": True,
            "phone_near_person": True,
            "phone_in_screen_region": False,
            "duration_seconds": 1.0,
        }
        ass_low = self.engine.evaluate_record(rec_low)
        self.assertIsNone(ass_low["alert_event"])

        rec_high = {
            "timestamp_seconds": 6.0,
            "phone_track_id": 1,
            "person_track_id": 2,
            "phone_detected": True,
            "person_detected": True,
            "phone_near_person": True,
            "phone_in_screen_region": True,
            "duration_seconds": 6.0,
        }
        ass_high = self.engine.evaluate_record(rec_high)
        alert = ass_high["alert_event"]
        self.assertIsNotNone(alert)
        self.assertTrue(alert["alert_id"].startswith("ALERT-CAM-TEST-"))
        self.assertEqual(alert["risk_score"], ass_high["risk_score"])
        self.assertTrue(alert["human_verification_required"])

    def test_6_continued_high_risk_no_duplicate_alerts(self):
        """Test 6: Consecutive high-risk frames after threshold crossing do NOT emit duplicate alerts."""
        rec_high = {
            "timestamp_seconds": 6.0,
            "phone_track_id": 1,
            "person_track_id": 2,
            "phone_detected": True,
            "person_detected": True,
            "phone_near_person": True,
            "phone_in_screen_region": True,
            "duration_seconds": 6.0,
        }
        ass1 = self.engine.evaluate_record(rec_high)
        self.assertIsNotNone(ass1["alert_event"])

        # Frame 2 at same high risk
        rec_high2 = rec_high.copy()
        rec_high2["timestamp_seconds"] = 6.1
        ass2 = self.engine.evaluate_record(rec_high2)
        # Should be None to avoid alert flooding
        self.assertIsNone(ass2["alert_event"])

    def test_7_risk_decreases_after_behavior_stops(self):
        """Test 7: Risk score decreases immediately when phone/behavior stops."""
        rec_high = {
            "timestamp_seconds": 6.0,
            "phone_track_id": 1,
            "person_track_id": 2,
            "phone_detected": True,
            "person_detected": True,
            "phone_near_person": True,
            "phone_in_screen_region": True,
            "duration_seconds": 6.0,
        }
        ass1 = self.engine.evaluate_record(rec_high)
        self.assertEqual(ass1["risk_score"], 75)

        # Phone removed/hidden
        rec_stopped = {
            "timestamp_seconds": 21.0,
            "phone_track_id": None,
            "person_track_id": 2,
            "phone_detected": False,
            "person_detected": True,
            "phone_near_person": False,
            "duration_seconds": 0.0,
        }
        ass2 = self.engine.evaluate_record(rec_stopped)
        self.assertEqual(ass2["risk_score"], 0)
        self.assertEqual(ass2["classification"], "NORMAL")

    def test_8_scores_never_exceed_100(self):
        """Test 8: Combined maximum weights cap strictly at 100."""
        rec_max = {
            "timestamp_seconds": 10.0,
            "phone_track_id": 1,
            "person_track_id": 2,
            "phone_detected": True,
            "person_detected": True,
            "phone_near_person": True,
            "phone_in_screen_region": True,
            "phone_moving_toward_screen_region": True,
            "duration_seconds": 10.0,
        }
        for i in range(25):
            rec_max["timestamp_seconds"] = 10.0 + i * 0.1
            assessment = self.engine.evaluate_record(rec_max)
            self.assertLessEqual(assessment["risk_score"], 100)

    def test_9_human_verification_always_true(self):
        """Test 9: Human verification flag is unconditionally True on all assessments and alerts."""
        rec = {
            "timestamp_seconds": 1.0,
            "phone_track_id": 1,
            "person_track_id": 2,
            "phone_detected": True,
            "phone_in_screen_region": True,
            "duration_seconds": 6.0,
        }
        assessment = self.engine.evaluate_record(rec)
        self.assertTrue(assessment["human_verification_required"])
        if assessment["alert_event"]:
            self.assertTrue(assessment["alert_event"]["human_verification_required"])

    def test_10_progressive_risk_escalation(self):
        """Test 10: Risk score escalates progressively through 4 stage tiers (0 -> 30 -> 50 -> 60 -> 75)."""
        # Tier 0: Person only
        r0 = {"timestamp_seconds": 1.0, "phone_track_id": None, "person_track_id": 1, "phone_detected": False}
        a0 = self.engine.evaluate_record(r0)
        self.assertEqual(a0["risk_score"], 0)

        # Tier 1: Person + Phone outside screen
        r1 = {"timestamp_seconds": 6.0, "phone_track_id": 1, "person_track_id": 1, "phone_detected": True, "phone_near_person": True, "phone_in_screen_region": False, "duration_seconds": 0.5}
        a1 = self.engine.evaluate_record(r1)
        self.assertEqual(a1["risk_score"], 30)

        # Tier 2: Phone in screen (<2s)
        r2 = {"timestamp_seconds": 11.0, "phone_track_id": 1, "person_track_id": 1, "phone_detected": True, "phone_near_person": True, "phone_in_screen_region": True, "duration_seconds": 1.0}
        a2 = self.engine.evaluate_record(r2)
        self.assertEqual(a2["risk_score"], 50)

        # Tier 3: Phone in screen (2-5s)
        r3 = {"timestamp_seconds": 13.5, "phone_track_id": 1, "person_track_id": 1, "phone_detected": True, "phone_near_person": True, "phone_in_screen_region": True, "duration_seconds": 3.5}
        a3 = self.engine.evaluate_record(r3)
        self.assertEqual(a3["risk_score"], 60)

        # Tier 4: Phone in screen (>=5s) -> Threshold crossed!
        r4 = {"timestamp_seconds": 16.0, "phone_track_id": 1, "person_track_id": 1, "phone_detected": True, "phone_near_person": True, "phone_in_screen_region": True, "duration_seconds": 6.0}
        a4 = self.engine.evaluate_record(r4)
        self.assertEqual(a4["risk_score"], 75)
        self.assertIsNotNone(a4["alert_event"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
