import sys
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure backend directory is in python path
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from alert_api import app


class TestApiEndpoints(unittest.TestCase):
    """
    Integration tests for AgentShield AI FastAPI endpoints.
    """

    def setUp(self):
        """Initialize FastAPI TestClient."""
        self.client = TestClient(app)

    def test_health_endpoint(self):
        """Test GET /api/health returns AgentShield AI service status."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("AgentShield", data["service"])
        self.assertTrue(data["human_verification_required"])

    def test_demo_reset_endpoint(self):
        """Test POST /api/demo/reset clears database and seeds baseline alert."""
        response = self.client.post("/api/demo/reset")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")

    def test_agent_stream_endpoint(self):
        """Test GET /api/agent/stream returns real-time safety evaluation."""
        response = self.client.get("/api/agent/stream?elapsed_seconds=12.0")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("decision", data)
        self.assertIn("risk_score", data)

    def test_alerts_and_incidents_endpoints(self):
        """Test GET /api/alerts, GET /api/incidents, and GET /api/stats."""
        res_alerts = self.client.get("/api/alerts")
        self.assertEqual(res_alerts.status_code, 200)

        res_incidents = self.client.get("/api/incidents")
        self.assertEqual(res_incidents.status_code, 200)

        res_stats = self.client.get("/api/stats")
        self.assertEqual(res_stats.status_code, 200)
        stats = res_stats.json()
        self.assertIn("active_alerts", stats)


if __name__ == "__main__":
    unittest.main()
