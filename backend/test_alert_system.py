import sys
import unittest
import uuid
from pathlib import Path

# Ensure backend directory is in python path
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from database import DatabaseManager
from alert_manager import AlertManager


class TestAlertSystem(unittest.TestCase):
    """
    Unit test suite for AgentShield AI Alert & Incident Management System.
    """

    def setUp(self):
        """Initialize temp database and AlertManager."""
        self.db_path = current_dir.parent / "data" / f"test_agentshield_{uuid.uuid4().hex[:6]}.db"
        self.db = DatabaseManager(db_path=str(self.db_path))
        self.manager = AlertManager(db=self.db, cooldown_seconds=5.0)

    def tearDown(self):
        """Clean up temporary test database file."""
        if self.db_path.exists():
            try:
                self.db_path.unlink()
            except OSError:
                pass

    def test_alert_creation_and_lifecycle(self):
        """Test alert ingestion, inspection, authorization, and incident creation."""
        alert_event = {
            "alert_id": "ALERT-TEST-001",
            "camera_id": "AGENT-07",
            "agent_id": "AGENT-07",
            "tool_name": "execute_sql_query",
            "target_resource": "db.users",
            "action_payload": "DROP TABLE users;",
            "timestamp_seconds": 12.0,
            "risk_score": 85,
            "classification": "CRITICAL_VIOLATION",
            "decision": "BLOCK",
            "reasons": ["Destructive command payload pattern"],
        }

        # 1. Create Alert
        created = self.manager.create_alert(alert_event)
        self.assertIsNotNone(created)
        self.assertEqual(created["status"], "NEW")

        # 2. Inspect Alert (NEW -> UNDER_REVIEW)
        reviewed = self.manager.start_review("ALERT-TEST-001")
        self.assertEqual(reviewed["status"], "UNDER_REVIEW")

        # 3. Confirm Alert (UNDER_REVIEW -> CONFIRMED & Incident logged)
        confirmed = self.manager.confirm_alert("ALERT-TEST-001", reviewer_action="Confirmed Policy Violation")
        self.assertEqual(confirmed["status"], "CONFIRMED")
        self.assertIn("incident", confirmed)

        # 4. Verify Incidents Table Record
        incidents = self.manager.incident_manager.list_incidents()
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0]["alert_id"], "ALERT-TEST-001")

    def test_alert_dismissal_blocks_action(self):
        """Test alert dismissal (BLOCK / DENY action) does not create incident."""
        alert_event = {
            "alert_id": "ALERT-TEST-002",
            "camera_id": "AGENT-07",
            "agent_id": "AGENT-07",
            "tool_name": "export_data",
            "target_resource": "s3://exports",
            "timestamp_seconds": 15.0,
            "risk_score": 60,
            "classification": "EVALUATE",
            "decision": "HUMAN APPROVAL",
            "reasons": ["Sensitive resource export"],
        }

        created = self.manager.create_alert(alert_event)
        self.assertIsNotNone(created)

        dismissed = self.manager.dismiss_alert("ALERT-TEST-002", reviewer_action="Blocked Action")
        self.assertEqual(dismissed["status"], "DISMISSED")

        incidents = self.manager.incident_manager.list_incidents()
        self.assertEqual(len(incidents), 0)


if __name__ == "__main__":
    unittest.main()
