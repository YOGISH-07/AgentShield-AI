import uuid
from typing import List, Dict, Any, Tuple, Optional


class RiskEngine:
    """
    Explainable AI Agent Action Risk Engine for AgentShield AI.
    Evaluates autonomous agent tool invocations, target resources, and command payloads
    into a 0–100 risk score with human-readable explanations, safety decisions
    (ALLOW, HUMAN APPROVAL, BLOCK), state persistence, and alerting.
    """

    # Configurable Scoring Weights for AI Agent Safety Controls
    DEFAULT_WEIGHTS = {
        "baseline_risk": 15,
        "unauthorized_tool": 25,
        "sensitive_resource": 20,
        "destructive_command": 30,
        "high_privilege_scope": 20,
        "prompt_injection_signal": 20,
        "rapid_execution_loop": 10,
    }

    # Thresholds
    DEFAULT_EVALUATE_THRESHOLD = 40
    DEFAULT_ALERT_THRESHOLD = 70

    def __init__(
        self,
        agent_id: str = "FINANCE-AI",
        weights: Optional[Dict[str, int]] = None,
        alert_threshold: int = 70,
        state_timeout_seconds: float = 10.0,
    ):
        """
        Initialize AgentShield RiskEngine.

        :param agent_id: Identifier of the monitored AI agent (e.g. 'AGENT-07').
        :param weights: Dict of scoring weights override.
        :param alert_threshold: Score threshold (0-100) to trigger a security interception.
        :param state_timeout_seconds: Inactivity duration before agent state cache expires.
        """
        self.agent_id = agent_id
        self.weights = weights if weights is not None else self.DEFAULT_WEIGHTS.copy()
        self.alert_threshold = alert_threshold
        self.state_timeout_seconds = state_timeout_seconds

        # Agent action state cache
        self._agent_states: Dict[str, Dict[str, Any]] = {}

    def get_classification(self, score: int) -> str:
        """
        Convert numeric risk score (0-100) into Agent Safety classification state.
        0-39: NORMAL, 40-69: EVALUATE, 70-100: CRITICAL_VIOLATION
        """
        if score >= 70:
            return "CRITICAL_VIOLATION"
        elif score >= 40:
            return "EVALUATE"
        else:
            return "NORMAL"

    def get_decision(self, score: int) -> str:
        """
        Derive Safety Decision based on risk score.
        0-39: ALLOW
        40-69: HUMAN APPROVAL
        70-100: BLOCK
        """
        if score >= 70:
            return "BLOCK"
        elif score >= 40:
            return "HUMAN APPROVAL"
        else:
            return "ALLOW"

    def _cleanup_expired_states(self, current_timestamp: float):
        """Remove agent states inactive longer than timeout."""
        expired_keys = [
            k
            for k, state in self._agent_states.items()
            if (current_timestamp - state["last_seen"]) > self.state_timeout_seconds
        ]
        for k in expired_keys:
            del self._agent_states[k]

    def evaluate_record(self, action_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a single AI agent tool call / action record and return an explainable risk assessment.

        :param action_record: Dictionary describing agent tool call and payload.
        :return: Risk assessment dictionary including score, classification, decision, reasons, and optional alert.
        """
        agent_id = action_record.get("agent_id", self.agent_id)
        tool_name = action_record.get("tool_name", "unknown_tool")
        target_resource = action_record.get("target_resource", "unknown_resource")
        action_payload = action_record.get("action_payload", "")
        timestamp = action_record.get("timestamp_seconds", 0.0)

        self._cleanup_expired_states(timestamp)

        if agent_id not in self._agent_states:
            self._agent_states[agent_id] = {
                "first_seen": timestamp,
                "last_seen": timestamp,
                "action_count": 0,
                "alert_triggered": False,
                "last_score": 0,
            }

        state = self._agent_states[agent_id]
        state["last_seen"] = timestamp
        state["action_count"] += 1

        # 1. Calculate Explainable Risk Score & Reasons
        base_risk = self.weights.get("baseline_risk", 15)
        score = base_risk
        reasons = ["Baseline agent action risk (+15)"]

        # Feature 1: Unauthorized or unlisted tool invocation
        if action_record.get("is_unauthorized_tool", False):
            pts = self.weights["unauthorized_tool"]
            score += pts
            reasons.append(f"Unauthorized tool invocation attempt: {tool_name}")

        # Feature 2: Accessing sensitive target resource
        if action_record.get("is_sensitive_resource", False):
            pts = self.weights["sensitive_resource"]
            score += pts
            reasons.append(f"Target resource marked high-sensitivity ({target_resource})")

        # Feature 3: Destructive command pattern (e.g. DROP, DELETE, EXFILTRATE, CHMOD 777)
        if action_record.get("is_destructive_command", False):
            pts = self.weights["destructive_command"]
            score += pts
            reasons.append(f"Destructive payload pattern detected: '{action_payload[:40]}'")

        # Feature 4: High privilege scope request
        if action_record.get("is_high_privilege_scope", False):
            pts = self.weights["high_privilege_scope"]
            score += pts
            reasons.append("Action requires root/administrator privilege escalation")

        # Feature 5: Prompt injection / untrusted input signal
        if action_record.get("has_prompt_injection_signal", False):
            pts = self.weights["prompt_injection_signal"]
            score += pts
            reasons.append("Adversarial prompt injection pattern detected in payload")

        # Feature 6: Rapid execution loop / rate anomaly
        if action_record.get("is_rapid_execution_loop", False) or action_record.get("execution_frequency", 1) >= 5:
            pts = self.weights["rapid_execution_loop"]
            score += pts
            reasons.append("Rapid automated tool execution loop detected")

        # Cap score strictly between 0 and 100
        score = min(100, max(0, score))
        classification = self.get_classification(score)
        decision = self.get_decision(score)

        # Require human verification if score >= 40 (HUMAN APPROVAL or BLOCK)
        human_verification_required = decision in ("HUMAN APPROVAL", "BLOCK")

        # 2. Hysteresis Alert Triggering (triggers alert when crossing threshold >= 70 or requiring review)
        alert_event = None
        if score >= self.alert_threshold and not state["alert_triggered"]:
            state["alert_triggered"] = True
            alert_id = f"ALERT-{agent_id}-{uuid.uuid4().hex[:8].upper()}"

            alert_event = {
                "alert_id": alert_id,
                "timestamp_seconds": round(timestamp, 2),
                "camera_id": agent_id,  # Kept for schema backward compatibility
                "agent_id": agent_id,
                "tool_name": tool_name,
                "target_resource": target_resource,
                "action_payload": action_payload,
                "person_track_id": 7,   # Compatibility mapping
                "phone_track_id": 1,    # Compatibility mapping
                "risk_score": score,
                "classification": classification,
                "decision": decision,
                "reasons": list(reasons),
                "human_verification_required": human_verification_required,
            }
        elif score < self.alert_threshold and state["alert_triggered"]:
            state["alert_triggered"] = False

        state["last_score"] = score

        assessment = {
            "timestamp_seconds": round(timestamp, 2),
            "camera_id": agent_id,
            "agent_id": agent_id,
            "tool_name": tool_name,
            "target_resource": target_resource,
            "action_payload": action_payload,
            "person_track_id": 7,
            "phone_track_id": 1,
            "risk_score": score,
            "classification": classification,
            "decision": decision,
            "reasons": reasons,
            "human_verification_required": human_verification_required,
            "alert_event": alert_event,
        }

        return assessment
