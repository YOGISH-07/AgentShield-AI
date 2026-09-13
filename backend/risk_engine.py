import uuid
from typing import List, Dict, Any, Tuple, Optional


class RiskEngine:
    """
    Explainable Behavioral Risk Engine for CineGuard AI.
    Converts Phase 2 spatial, screen region, and temporal feature records
    into a 0–100 behavioral risk score with human-readable explanations,
    state persistence, and hysteresis-based alert generation.
    """

    # Configurable Prototype Scoring Weights
    # Calibrated so brief detections do not prematurely trigger alerts.
    # Requires a combination of signals: phone + association + screen alignment + sustained duration >= 5s
    DEFAULT_WEIGHTS = {
        "phone_detected": 15,
        "person_phone_association": 15,
        "in_screen_region": 20,
        "sustained_behavior_full": 25,    # duration >= 5s
        "sustained_behavior_partial": 10, # 2s <= duration < 5s
        "screen_directed_movement": 10,
        "persistent_observation": 10,     # >= 15 observations
    }

    # Configurable Duration Thresholds (seconds)
    DEFAULT_DURATION_FULL_SEC = 5.0
    DEFAULT_DURATION_PARTIAL_SEC = 2.0
    DEFAULT_ALERT_THRESHOLD = 70

    def __init__(
        self,
        camera_id: str = "CAM-01",
        weights: Optional[Dict[str, int]] = None,
        alert_threshold: int = 70,
        state_timeout_seconds: float = 5.0,
    ):
        """
        Initialize RiskEngine.

        :param camera_id: Camera identifier string (e.g. 'CAM-01').
        :param weights: Dict of scoring weights override.
        :param alert_threshold: Score threshold (0-100) to trigger an alert.
        :param state_timeout_seconds: Inactivity duration before relationship state expires.
        """
        self.camera_id = camera_id
        self.weights = (
            weights if weights is not None else self.DEFAULT_WEIGHTS.copy()
        )
        self.alert_threshold = alert_threshold
        self.state_timeout_seconds = state_timeout_seconds

        # Temporal relationship state cache:
        # Key: (person_track_id, phone_track_id) or (None, phone_track_id)
        self._relationship_states: Dict[Tuple[Optional[int], int], Dict[str, Any]] = {}

    def get_classification(self, score: int) -> str:
        """
        Convert numeric risk score (0-100) into behavioral classification state.
        0-39: NORMAL, 40-69: WATCH, 70-100: SUSPECTED_RECORDING
        """
        if score >= 70:
            return "SUSPECTED_RECORDING"
        elif score >= 40:
            return "WATCH"
        else:
            return "NORMAL"

    def _cleanup_expired_states(self, current_timestamp: float):
        """Remove relationship states that have been inactive longer than timeout."""
        expired_keys = [
            k
            for k, state in self._relationship_states.items()
            if (current_timestamp - state["last_seen"]) > self.state_timeout_seconds
        ]
        for k in expired_keys:
            del self._relationship_states[k]

    def evaluate_record(self, behavior_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a single Phase 2 behavioral feature record and return an explainable risk assessment.

        :param behavior_record: Dictionary output from BehaviorAnalyzer.
        :return: Risk assessment dictionary including score, classification, reasons, and optional alert.
        """
        phone_id = behavior_record.get("phone_track_id")
        person_id = behavior_record.get("person_track_id")
        timestamp = behavior_record.get("timestamp_seconds", 0.0)

        # 1. Cleanup old expired states
        self._cleanup_expired_states(timestamp)

        rel_key = (person_id, phone_id)

        # 2. Retrieve or initialize temporal relationship state
        if rel_key not in self._relationship_states:
            self._relationship_states[rel_key] = {
                "first_seen": timestamp,
                "last_seen": timestamp,
                "observation_count": 0,
                "alert_triggered": False,
                "last_score": 0,
            }

        state = self._relationship_states[rel_key]
        state["last_seen"] = timestamp
        state["observation_count"] += 1

        # Calculate actual duration based on first_seen timestamp
        duration_sec = behavior_record.get("duration_seconds", max(0.0, timestamp - state["first_seen"]))

        # 3. Calculate Explainable Weighted Risk Score & Reasons
        score = 0
        reasons = []

        # Feature 1: Mobile device detected
        if behavior_record.get("phone_detected", False):
            pts = self.weights["phone_detected"]
            score += pts
            reasons.append("Mobile device detected")

        # Feature 2: Person-phone association
        if behavior_record.get("phone_near_person", False) and person_id is not None:
            pts = self.weights["person_phone_association"]
            score += pts
            reasons.append(f"Device associated with tracked Person #{person_id}")

        # Feature 3: Located within cinema screen region
        if behavior_record.get("phone_in_screen_region", False):
            pts = self.weights["in_screen_region"]
            score += pts
            reasons.append("Device located within configured screen region")

        # Feature 4: Sustained relevant behavior duration
        if duration_sec >= self.DEFAULT_DURATION_FULL_SEC:
            pts = self.weights["sustained_behavior_full"]
            score += pts
            reasons.append(f"Behavior persisted for {duration_sec:.1f} seconds")
        elif duration_sec >= self.DEFAULT_DURATION_PARTIAL_SEC:
            pts = self.weights["sustained_behavior_partial"]
            score += pts
            reasons.append(f"Behavior observed for {duration_sec:.1f} seconds")

        # Feature 5: Screen-directed movement alignment
        if behavior_record.get("phone_moving_toward_screen_region", False):
            pts = self.weights["screen_directed_movement"]
            score += pts
            reasons.append("Device movement directed toward screen region")

        # Feature 6: Persistent relationship observation count
        if state["observation_count"] >= 15:
            pts = self.weights["persistent_observation"]
            score += pts
            reasons.append("Persistent relationship observation history")

        # Cap maximum risk score strictly at 100
        score = min(100, max(0, score))
        classification = self.get_classification(score)

        # 4. State Transition & Hysteresis Alert Triggering
        alert_event = None
        
        # Trigger alert ONLY on crossing threshold from below
        if score >= self.alert_threshold and not state["alert_triggered"]:
            state["alert_triggered"] = True
            alert_id = f"ALERT-{self.camera_id}-{uuid.uuid4().hex[:8].upper()}"
            
            alert_event = {
                "alert_id": alert_id,
                "timestamp_seconds": round(timestamp, 2),
                "camera_id": self.camera_id,
                "person_track_id": person_id,
                "phone_track_id": phone_id,
                "risk_score": score,
                "classification": classification,
                "reasons": list(reasons),
                "human_verification_required": True,
            }
        elif score < self.alert_threshold and state["alert_triggered"]:
            # Reset alert state if score drops below threshold (Hysteresis)
            state["alert_triggered"] = False

        state["last_score"] = score

        assessment = {
            "timestamp_seconds": round(timestamp, 2),
            "camera_id": self.camera_id,
            "person_track_id": person_id,
            "phone_track_id": phone_id,
            "risk_score": score,
            "classification": classification,
            "reasons": reasons,
            "human_verification_required": True,
            "alert_event": alert_event,
        }

        return assessment
