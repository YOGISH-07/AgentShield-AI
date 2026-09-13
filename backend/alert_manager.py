from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from database import DatabaseManager
from incident_manager import IncidentManager


class AlertManager:
    """
    Alert Manager for CineGuard AI.
    Handles real-time alert event ingestion from Phase 3 Risk Engine,
    deduplication cooldowns, human-in-the-loop lifecycle state transitions,
    and triggering incident creation upon confirmation.
    """

    # Lifecycle States: NEW -> UNDER_REVIEW -> CONFIRMED / DISMISSED (or NEW -> DISMISSED)
    VALID_TRANSITIONS = {
        "NEW": {"UNDER_REVIEW", "DISMISSED"},
        "UNDER_REVIEW": {"CONFIRMED", "DISMISSED"},
        "CONFIRMED": set(),
        "DISMISSED": set(),
    }

    def __init__(self, db: DatabaseManager, cooldown_seconds: float = 10.0):
        """
        Initialize AlertManager.

        :param db: Instance of DatabaseManager.
        :param cooldown_seconds: Time window to suppress duplicate alerts for same target.
        """
        self.db = db
        self.incident_manager = IncidentManager(db=db)
        self.cooldown_seconds = cooldown_seconds

        # Deduplication cache: Maps (camera_id, person_track_id, phone_track_id) -> last_created_timestamp
        self._recent_alert_timestamps: Dict[Tuple[str, Optional[int], Optional[int]], float] = {}

    def create_alert(self, alert_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Ingest a Phase 3 alert event, apply deduplication cooldown, and insert into SQLite.

        :param alert_event: Dictionary matching Phase 3 alert payload.
        :return: Inserted alert dictionary or None if deduplicated.
        """
        cam_id = alert_event.get("camera_id", "CAM-01")
        person_id = alert_event.get("person_track_id")
        phone_id = alert_event.get("phone_track_id")
        timestamp = alert_event.get("timestamp_seconds", 0.0)

        dedup_key = (cam_id, person_id, phone_id)

        # Alert Deduplication Check
        if dedup_key in self._recent_alert_timestamps:
            last_time = self._recent_alert_timestamps[dedup_key]
            if (timestamp - last_time) < self.cooldown_seconds:
                # Suppress duplicate alert creation within cooldown
                return None

        self._recent_alert_timestamps[dedup_key] = timestamp

        alert_record = {
            "alert_id": alert_event["alert_id"],
            "camera_id": cam_id,
            "timestamp_seconds": timestamp,
            "person_track_id": person_id,
            "phone_track_id": phone_id,
            "risk_score": alert_event["risk_score"],
            "classification": alert_event.get("classification", "SUSPECTED_RECORDING"),
            "reasons": alert_event.get("reasons", []),
            "status": "NEW",
            "human_verification_required": True,
            "created_at": datetime.now().isoformat(),
            "reviewed_at": None,
            "resolved_at": None,
        }

        success = self.db.insert_alert(alert_record)
        return alert_record if success else None

    def get_alert(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve alert by alert_id."""
        return self.db.get_alert_by_id(alert_id)

    def list_alerts(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all alerts, optionally filtered by status."""
        return self.db.list_alerts(status_filter=status_filter)

    def _validate_transition(self, current_status: str, target_status: str):
        """Validate state transition machine."""
        allowed = self.VALID_TRANSITIONS.get(current_status, set())
        if target_status not in allowed:
            raise ValueError(
                f"Invalid status transition: '{current_status}' -> '{target_status}'. "
                f"Allowed transitions from '{current_status}': {list(allowed) if allowed else 'None'}"
            )

    def start_review(self, alert_id: str, reviewer_action: str = "review") -> Dict[str, Any]:
        """Transition alert status from NEW -> UNDER_REVIEW."""
        alert = self.get_alert(alert_id)
        if not alert:
            raise KeyError(f"Alert with ID '{alert_id}' not found.")

        self._validate_transition(alert["status"], "UNDER_REVIEW")
        now_str = datetime.now().isoformat()

        self.db.update_alert_status(alert_id, "UNDER_REVIEW", reviewed_at=now_str)
        alert["status"] = "UNDER_REVIEW"
        alert["reviewed_at"] = now_str
        return alert

    def confirm_alert(self, alert_id: str, reviewer_action: str = "confirmed") -> Dict[str, Any]:
        """Transition alert status from UNDER_REVIEW -> CONFIRMED and generate Incident Record."""
        alert = self.get_alert(alert_id)
        if not alert:
            raise KeyError(f"Alert with ID '{alert_id}' not found.")

        self._validate_transition(alert["status"], "CONFIRMED")
        now_str = datetime.now().isoformat()

        # Update alert in DB
        self.db.update_alert_status(alert_id, "CONFIRMED", resolved_at=now_str)
        alert["status"] = "CONFIRMED"
        alert["resolved_at"] = now_str

        # Create structured incident record
        incident = self.incident_manager.create_incident_from_alert(
            alert_data=alert, reviewer_action=reviewer_action
        )
        alert["incident"] = incident
        return alert

    def dismiss_alert(self, alert_id: str, reviewer_action: str = "dismissed") -> Dict[str, Any]:
        """Transition alert status from NEW/UNDER_REVIEW -> DISMISSED."""
        alert = self.get_alert(alert_id)
        if not alert:
            raise KeyError(f"Alert with ID '{alert_id}' not found.")

        self._validate_transition(alert["status"], "DISMISSED")
        now_str = datetime.now().isoformat()

        self.db.update_alert_status(alert_id, "DISMISSED", resolved_at=now_str)
        alert["status"] = "DISMISSED"
        alert["resolved_at"] = now_str
        return alert

    def reset_cache(self):
        """Clear deduplication timestamp cache for demo resets."""
        self._recent_alert_timestamps.clear()

    def get_operational_stats(self) -> Dict[str, Any]:
        """Get operational stats calculated from SQLite database."""
        return self.db.get_operational_stats()
