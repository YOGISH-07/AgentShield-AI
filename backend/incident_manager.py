import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from database import DatabaseManager


class IncidentManager:
    """
    Incident Manager for CineGuard AI.
    Logs structured, anonymous incident records when an alert is confirmed by authorized staff.
    Does NOT store names, faces, or personal identity information.
    """

    def __init__(self, db: DatabaseManager):
        """
        Initialize IncidentManager.

        :param db: Instance of DatabaseManager.
        """
        self.db = db

    def create_incident_from_alert(
        self, alert_data: Dict[str, Any], reviewer_action: str = "confirmed"
    ) -> Dict[str, Any]:
        """
        Create a new verified incident record from a confirmed alert.

        :param alert_data: Dict containing alert fields.
        :param reviewer_action: Action string ('confirmed').
        :return: Created incident record dict.
        """
        incident_id = f"INC-{alert_data['camera_id']}-{uuid.uuid4().hex[:8].upper()}"

        incident_record = {
            "incident_id": incident_id,
            "alert_id": alert_data["alert_id"],
            "camera_id": alert_data["camera_id"],
            "timestamp_seconds": alert_data["timestamp_seconds"],
            "risk_score_at_alert": alert_data["risk_score"],
            "reasons": alert_data.get("reasons", []),
            "verification_status": "CONFIRMED_OBSERVED_BEHAVIOR",
            "reviewer_action": reviewer_action,
            "human_verification_required": True,
            "created_at": datetime.now().isoformat(),
        }

        self.db.insert_incident(incident_record)
        return incident_record

    def list_incidents(self) -> List[Dict[str, Any]]:
        """List all confirmed incident records."""
        return self.db.list_incidents()
