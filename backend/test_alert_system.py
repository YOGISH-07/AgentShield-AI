import os
import sys
import uuid
import unittest
from pathlib import Path

# Ensure backend directory is in python path
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from database import DatabaseManager
from alert_manager import AlertManager


class TestAlertSystem(unittest.TestCase):
    """
    Unit test suite for CineGuard AI Phase 4 Alert & Incident Management.
    Tests all 13 requirements using an isolated temporary SQLite database.
    """

    @classmethod
    def setUpClass(cls):
        """Use unique temp database path for test suite run."""
        cls.TEST_DB_PATH = f"data/test_cineguard_{uuid.uuid4().hex[:6]}.db"

    def setUp(self):
        """Initialize database for test run."""
        self.db = DatabaseManager(db_path=self.TEST_DB_PATH)
        self.alert_manager = AlertManager(db=self.db, cooldown_seconds=5.0)

        # Unique sample alert payload per test method
        self.sample_alert = {
            "alert_id": f"ALERT-TEST-{uuid.uuid4().hex[:8]}",
            "camera_id": "CAM-01",
            "timestamp_seconds": 1.5,
            "person_track_id": 4,
            "phone_track_id": 1,
            "risk_score": 82,
            "classification": "SUSPECTED_RECORDING",
            "reasons": [
                "Mobile device detected",
                "Device associated with tracked Person #4",
                "Device located within configured screen region",
            ],
            "human_verification_required": True,
        }

    @classmethod
    def tearDownClass(cls):
        """Cleanup temporary SQLite test database file after all tests finish."""
        if os.path.exists(cls.TEST_DB_PATH):
            try:
                os.remove(cls.TEST_DB_PATH)
            except Exception:
                pass

    def test_1_alert_creation(self):
        """Test 1: Alert creation inserts record into database with status NEW."""
        aid = self.sample_alert["alert_id"]
        created = self.alert_manager.create_alert(self.sample_alert)
        self.assertIsNotNone(created)
        self.assertEqual(created["alert_id"], aid)
        self.assertEqual(created["status"], "NEW")

    def test_2_alert_retrieval(self):
        """Test 2: Alert retrieval by alert_id returns exact inserted record."""
        aid = self.sample_alert["alert_id"]
        self.alert_manager.create_alert(self.sample_alert)
        retrieved = self.alert_manager.get_alert(aid)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["risk_score"], 82)

    def test_3_alert_listing(self):
        """Test 3: Alert listing retrieves inserted alerts."""
        initial_count = len(self.alert_manager.list_alerts())
        self.alert_manager.create_alert(self.sample_alert)
        alerts = self.alert_manager.list_alerts()
        self.assertEqual(len(alerts), initial_count + 1)

    def test_4_new_to_under_review(self):
        """Test 4: Status transition NEW -> UNDER_REVIEW succeeds."""
        aid = self.sample_alert["alert_id"]
        self.alert_manager.create_alert(self.sample_alert)
        updated = self.alert_manager.start_review(aid)
        self.assertEqual(updated["status"], "UNDER_REVIEW")
        self.assertIsNotNone(updated["reviewed_at"])

    def test_5_under_review_to_confirmed(self):
        """Test 5: Status transition UNDER_REVIEW -> CONFIRMED succeeds and generates Incident."""
        aid = self.sample_alert["alert_id"]
        self.alert_manager.create_alert(self.sample_alert)
        self.alert_manager.start_review(aid)
        confirmed = self.alert_manager.confirm_alert(aid)
        
        self.assertEqual(confirmed["status"], "CONFIRMED")
        self.assertIsNotNone(confirmed.get("incident"))
        self.assertTrue(confirmed["incident"]["incident_id"].startswith("INC-CAM-01-"))

    def test_6_under_review_to_dismissed(self):
        """Test 6: Status transition UNDER_REVIEW -> DISMISSED succeeds."""
        aid = self.sample_alert["alert_id"]
        self.alert_manager.create_alert(self.sample_alert)
        self.alert_manager.start_review(aid)
        dismissed = self.alert_manager.dismiss_alert(aid)
        self.assertEqual(dismissed["status"], "DISMISSED")

    def test_7_invalid_state_transitions_rejected(self):
        """Test 7: Invalid status transitions raise ValueError."""
        aid = self.sample_alert["alert_id"]
        self.alert_manager.create_alert(self.sample_alert)
        
        # Direct NEW -> CONFIRMED is invalid (must go through UNDER_REVIEW)
        with self.assertRaises(ValueError):
            self.alert_manager.confirm_alert(aid)

        # Advance to CONFIRMED
        self.alert_manager.start_review(aid)
        self.alert_manager.confirm_alert(aid)

        # CONFIRMED -> NEW is invalid
        with self.assertRaises(ValueError):
            self.alert_manager.start_review(aid)

    def test_8_incident_created_after_confirmation(self):
        """Test 8: Incident record is created and queryable after alert confirmation."""
        aid = self.sample_alert["alert_id"]
        self.alert_manager.create_alert(self.sample_alert)
        self.alert_manager.start_review(aid)
        self.alert_manager.confirm_alert(aid)

        incidents = self.alert_manager.incident_manager.list_incidents()
        matching = [inc for inc in incidents if inc["alert_id"] == aid]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["verification_status"], "CONFIRMED_OBSERVED_BEHAVIOR")

    def test_9_duplicate_alert_prevention(self):
        """Test 9: Deduplication cooldown suppresses creating duplicate alerts for same target within cooldown."""
        a1 = self.alert_manager.create_alert(self.sample_alert)
        self.assertIsNotNone(a1)

        # Immediate duplicate within cooldown (1.5s timestamp -> 2.0s timestamp for same CAM-01 + Person #4 + Phone #1)
        sample2 = self.sample_alert.copy()
        sample2["alert_id"] = f"ALERT-TEST-{uuid.uuid4().hex[:8]}"
        sample2["timestamp_seconds"] = 2.0
        a2 = self.alert_manager.create_alert(sample2)
        self.assertIsNone(a2)  # Suppressed by deduplication

    def test_10_statistics_calculated_from_actual_records(self):
        """Test 10: Operational stats are accurately calculated from SQLite database."""
        # Create unique DB for stats test
        stats_db_path = f"data/test_stats_{uuid.uuid4().hex[:6]}.db"
        stats_db = DatabaseManager(db_path=stats_db_path)
        stats_am = AlertManager(db=stats_db, cooldown_seconds=0.0)

        # Alert 1 -> Confirm
        a1_id = f"ALERT-STAT-1-{uuid.uuid4().hex[:4]}"
        stats_am.create_alert({
            "alert_id": a1_id, "camera_id": "CAM-01", "timestamp_seconds": 1.0,
            "person_track_id": 1, "phone_track_id": 1, "risk_score": 80,
            "classification": "SUSPECTED_RECORDING", "reasons": ["test"], "human_verification_required": True
        })
        stats_am.start_review(a1_id)
        stats_am.confirm_alert(a1_id)

        # Alert 2 -> Dismiss
        a2_id = f"ALERT-STAT-2-{uuid.uuid4().hex[:4]}"
        stats_am.create_alert({
            "alert_id": a2_id, "camera_id": "CAM-01", "timestamp_seconds": 10.0,
            "person_track_id": 2, "phone_track_id": 2, "risk_score": 75,
            "classification": "SUSPECTED_RECORDING", "reasons": ["test"], "human_verification_required": True
        })
        stats_am.dismiss_alert(a2_id)

        stats = stats_am.get_operational_stats()
        self.assertEqual(stats["total_alerts"], 2)
        self.assertEqual(stats["active_alerts"], 0)
        self.assertEqual(stats["confirmed_incidents"], 1)
        self.assertEqual(stats["dismissed_alerts"], 1)
        self.assertEqual(stats["false_alarm_rate"], 0.5)

        if os.path.exists(stats_db_path):
            try:
                os.remove(stats_db_path)
            except Exception:
                pass

    def test_11_human_verification_flag_remains_true(self):
        """Test 11: human_verification_required flag remains True on all alerts and incidents."""
        aid = self.sample_alert["alert_id"]
        self.alert_manager.create_alert(self.sample_alert)
        self.alert_manager.start_review(aid)
        confirmed = self.alert_manager.confirm_alert(aid)

        self.assertTrue(confirmed["human_verification_required"])
        self.assertTrue(confirmed["incident"]["human_verification_required"])

    def test_12_anonymous_track_ids_only(self):
        """Test 12: Database records store anonymous integer track IDs with zero PII."""
        aid = self.sample_alert["alert_id"]
        self.alert_manager.create_alert(self.sample_alert)
        alert = self.alert_manager.get_alert(aid)
        self.assertIsInstance(alert["person_track_id"], int)
        self.assertIsInstance(alert["phone_track_id"], int)

    def test_13_database_persists_records_correctly(self):
        """Test 13: Reopening SQLite database connection verifies persistent storage."""
        aid = self.sample_alert["alert_id"]
        self.alert_manager.create_alert(self.sample_alert)
        
        # New database connection instance targeting same file
        new_db = DatabaseManager(db_path=self.TEST_DB_PATH)
        persisted = new_db.get_alert_by_id(aid)
        self.assertIsNotNone(persisted)
        self.assertEqual(persisted["alert_id"], aid)


if __name__ == "__main__":
    unittest.main(verbosity=2)
