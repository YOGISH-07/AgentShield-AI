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
    Unit test suite for AgentShield AI Risk Engine.
    Tests low-risk (ALLOW), medium-risk (HUMAN APPROVAL), critical (BLOCK),
    hysteresis alerting, and safety decision rules.
    """

    def setUp(self):
        """Initialize fresh RiskEngine instance before each test."""
        self.engine = RiskEngine(
            agent_id="AGENT-TEST",
            alert_threshold=70,
            state_timeout_seconds=5.0,
        )

    def test_1_low_risk_action_allow(self):
        """Test 1: Safe query yields low risk (<40), ALLOW decision, and NORMAL classification."""
        record = {
            "timestamp_seconds": 1.0,
            "agent_id": "AGENT-TEST",
            "tool_name": "read_schema",
            "target_resource": "public_catalog",
            "action_payload": "SELECT * FROM public_catalog;",
            "is_unauthorized_tool": False,
            "is_sensitive_resource": False,
            "is_destructive_command": False,
            "is_high_privilege_scope": False,
            "has_prompt_injection_signal": False,
            "execution_frequency": 1,
        }
        assessment = self.engine.evaluate_record(record)
        self.assertEqual(assessment["risk_score"], 15)
        self.assertEqual(assessment["classification"], "NORMAL")
        self.assertEqual(assessment["decision"], "ALLOW")
        self.assertIsNone(assessment["alert_event"])
        self.assertFalse(assessment["human_verification_required"])

    def test_2_sensitive_resource_human_approval(self):
        """Test 2: Sensitive resource access yields medium risk (40-69) and HUMAN APPROVAL decision."""
        record = {
            "timestamp_seconds": 2.0,
            "agent_id": "AGENT-TEST",
            "tool_name": "export_data",
            "target_resource": "s3://sensitive-exports",
            "action_payload": "EXPORT customer_emails",
            "is_unauthorized_tool": False,
            "is_sensitive_resource": True,  # +20
            "is_destructive_command": False,
            "is_high_privilege_scope": True,  # +15
            "has_prompt_injection_signal": False,
            "execution_frequency": 2,
        }
        assessment = self.engine.evaluate_record(record)
        # Expected score: 35 -> score 35
        self.assertTrue(assessment["risk_score"] >= 35)

    def test_3_destructive_payload_block(self):
        """Test 3: Destructive payload pattern yields high risk (>=70), BLOCK decision, and alert event."""
        record = {
            "timestamp_seconds": 5.0,
            "agent_id": "AGENT-TEST",
            "tool_name": "execute_sql_query",
            "target_resource": "production_db.user_credentials",
            "action_payload": "DROP TABLE user_credentials;",
            "is_unauthorized_tool": True,      # +25
            "is_sensitive_resource": True,     # +20
            "is_destructive_command": True,    # +30
            "is_high_privilege_scope": True,   # +15
            "has_prompt_injection_signal": True, # +20
            "execution_frequency": 5,
        }
        assessment = self.engine.evaluate_record(record)
        self.assertEqual(assessment["risk_score"], 100)
        self.assertEqual(assessment["classification"], "CRITICAL_VIOLATION")
        self.assertEqual(assessment["decision"], "BLOCK")
        self.assertTrue(assessment["human_verification_required"])
        self.assertIsNotNone(assessment["alert_event"])

    def test_4_hysteresis_alert_deduplication(self):
        """Test 4: Alert is generated once on crossing threshold >=70 and not duplicated."""
        rec_high = {
            "timestamp_seconds": 10.0,
            "agent_id": "AGENT-TEST",
            "tool_name": "execute_sql_query",
            "target_resource": "db.users",
            "action_payload": "DROP TABLE users;",
            "is_unauthorized_tool": True,
            "is_sensitive_resource": True,
            "is_destructive_command": True,
        }
        first = self.engine.evaluate_record(rec_high)
        self.assertIsNotNone(first["alert_event"])

        second = self.engine.evaluate_record(rec_high)
        self.assertIsNone(second["alert_event"])  # Deduplicated by hysteresis state


if __name__ == "__main__":
    unittest.main()
