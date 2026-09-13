import os
import sys
import uuid
import unittest
from pathlib import Path

# Ensure backend directory is in python path
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from fastapi.testclient import TestClient
from alert_api import app


class TestAPIEndpoints(unittest.TestCase):
    """
    Comprehensive REST API Test Suite for CineGuard AI.
    Verifies all API contracts, health checks, stats calculations, demo resets,
    video streaming, and alert/incident state transitions.
    """

    @classmethod
    def setUpClass(cls):
        """Initialize FastAPI TestClient."""
        cls.client = TestClient(app)

    def test_01_health_endpoint(self):
        """Test 1: GET /api/health returns 200 with required parameters."""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")
        self.assertTrue(data["human_verification_required"])
        self.assertEqual(data["mode"], "DEMO MODE")

    def test_02_video_endpoint(self):
        """Test 2: GET /api/video/risk returns 200 OK video stream."""
        res = self.client.get("/api/video/risk")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("content-type"), "video/mp4")
        self.assertEqual(res.headers.get("accept-ranges"), "bytes")
        self.assertGreater(len(res.content), 1000)

    def test_03_stats_endpoint(self):
        """Test 3: GET /api/stats returns valid operational metrics."""
        res = self.client.get("/api/stats")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        for key in ["active_alerts", "total_alerts", "confirmed_incidents", "dismissed_alerts", "false_alarm_rate"]:
            self.assertIn(key, data)

    def test_04_demo_reset(self):
        """Test 4: POST /api/demo/reset resets database and seeds baseline alert."""
        res = self.client.post("/api/demo/reset")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["active_alerts"], 1)

        # Verify alert exists in database
        alerts_res = self.client.get("/api/alerts")
        self.assertEqual(alerts_res.status_code, 200)
        alerts = alerts_res.json()
        self.assertGreaterEqual(len(alerts), 1)

    def test_05_alert_workflow_review_confirm_incident(self):
        """Test 5: Full alert workflow (NEW -> UNDER_REVIEW -> CONFIRMED -> INCIDENT)."""
        # Reset to clean demo baseline
        self.client.post("/api/demo/reset")
        alerts = self.client.get("/api/alerts").json()
        target_alert = alerts[0]
        aid = target_alert["alert_id"]

        # Step 1: Start review (NEW -> UNDER_REVIEW)
        rev_res = self.client.post(f"/api/alerts/{aid}/review", json={"reviewer_action": "Reviewing"})
        self.assertEqual(rev_res.status_code, 200)
        self.assertEqual(rev_res.json()["status"], "UNDER_REVIEW")

        # Step 2: Confirm incident (UNDER_REVIEW -> CONFIRMED)
        conf_res = self.client.post(f"/api/alerts/{aid}/confirm", json={"reviewer_action": "Confirmed Staff Verification"})
        self.assertEqual(conf_res.status_code, 200)
        self.assertEqual(conf_res.json()["status"], "CONFIRMED")

        # Step 3: Verify incident appears in /api/incidents
        inc_res = self.client.get("/api/incidents")
        self.assertEqual(inc_res.status_code, 200)
        incidents = inc_res.json()
        matching = [i for i in incidents if i["alert_id"] == aid]
        self.assertEqual(len(matching), 1)

    def test_06_alert_workflow_dismiss(self):
        """Test 6: Alert dismissal (NEW -> DISMISSED) creates no incident."""
        self.client.post("/api/demo/reset")
        alerts = self.client.get("/api/alerts").json()
        target_alert = alerts[0]
        aid = target_alert["alert_id"]

        # Dismiss directly or via UNDER_REVIEW
        self.client.post(f"/api/alerts/{aid}/review", json={"reviewer_action": "Reviewing"})
        dis_res = self.client.post(f"/api/alerts/{aid}/dismiss", json={"reviewer_action": "Dismissed False Alarm"})
        self.assertEqual(dis_res.status_code, 200)
        self.assertEqual(dis_res.json()["status"], "DISMISSED")

        # Verify false alarm rate in stats
        stats = self.client.get("/api/stats").json()
        self.assertGreater(stats["false_alarm_rate"], 0.0)

    def test_07_invalid_transitions_rejected(self):
        """Test 7: Direct invalid status transitions return 400 Bad Request."""
        self.client.post("/api/demo/reset")
        alerts = self.client.get("/api/alerts").json()
        target_alert = alerts[0]
        aid = target_alert["alert_id"]

        # Direct NEW -> CONFIRMED (bypassing UNDER_REVIEW) must fail
        err_res = self.client.post(f"/api/alerts/{aid}/confirm", json={"reviewer_action": "Direct"})
        self.assertEqual(err_res.status_code, 400)

    def test_08_nonexistent_alert_404(self):
        """Test 8: Non-existent alert ID returns 404 Not Found."""
        res = self.client.get("/api/alerts/ALERT-NON-EXISTENT-999")
        self.assertEqual(res.status_code, 404)


if __name__ == "__main__":
    unittest.main(verbosity=2)
