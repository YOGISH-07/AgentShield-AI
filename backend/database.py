import os
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


class DatabaseManager:
    """
    SQLite Database Manager for AgentShield AI.
    Handles thread-safe parameterized storage for Agent Safety alerts and verified incidents
    targeting data/agentshield.db.
    """

    def __init__(self, db_path: str = "data/agentshield.db"):
        """
        Initialize DatabaseManager.

        :param db_path: Path to SQLite database file.
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()

    def _get_connection(self) -> sqlite3.Connection:
        """Create and return a new SQLite database connection."""
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        """Create alerts and incidents tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Table 1: Agent Safety Alerts Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT UNIQUE NOT NULL,
                    camera_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL DEFAULT 'AGENT-07',
                    tool_name TEXT NOT NULL DEFAULT 'unknown_tool',
                    target_resource TEXT DEFAULT 'unknown_resource',
                    action_payload TEXT DEFAULT '',
                    timestamp REAL NOT NULL,
                    person_track_id INTEGER DEFAULT 7,
                    phone_track_id INTEGER DEFAULT 1,
                    risk_score INTEGER NOT NULL,
                    classification TEXT NOT NULL,
                    decision TEXT NOT NULL DEFAULT 'BLOCK',
                    reasons_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    reviewed_at TEXT,
                    resolved_at TEXT
                )
                """
            )

            # Table 2: Verified Incidents Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_id TEXT UNIQUE NOT NULL,
                    alert_id TEXT NOT NULL,
                    camera_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL DEFAULT 'AGENT-07',
                    tool_name TEXT NOT NULL DEFAULT 'unknown_tool',
                    target_resource TEXT DEFAULT 'unknown_resource',
                    timestamp REAL NOT NULL,
                    risk_score INTEGER NOT NULL,
                    reasons_json TEXT NOT NULL,
                    verification_status TEXT NOT NULL,
                    reviewer_action TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (alert_id) REFERENCES alerts(alert_id)
                )
                """
            )
            conn.commit()

    # --- ALERT DATABASE METHODS ---

    def insert_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Insert a new alert record into database using parameterized query."""
        reasons_str = json.dumps(alert_data.get("reasons", []))
        created_at_str = alert_data.get("created_at", datetime.now().isoformat())
        agent_id = alert_data.get("agent_id", alert_data.get("camera_id", "AGENT-07"))

        query = """
            INSERT INTO alerts (
                alert_id, camera_id, agent_id, tool_name, target_resource, action_payload,
                timestamp, person_track_id, phone_track_id, risk_score, classification,
                decision, reasons_json, status, created_at, reviewed_at, resolved_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            with self._get_connection() as conn:
                conn.execute(
                    query,
                    (
                        alert_data["alert_id"],
                        alert_data.get("camera_id", agent_id),
                        agent_id,
                        alert_data.get("tool_name", "execute_command"),
                        alert_data.get("target_resource", "production_server"),
                        alert_data.get("action_payload", ""),
                        alert_data.get("timestamp_seconds", 0.0),
                        alert_data.get("person_track_id", 7),
                        alert_data.get("phone_track_id", 1),
                        alert_data["risk_score"],
                        alert_data.get("classification", "CRITICAL_VIOLATION"),
                        alert_data.get("decision", "BLOCK"),
                        reasons_str,
                        alert_data.get("status", "NEW"),
                        created_at_str,
                        alert_data.get("reviewed_at"),
                        alert_data.get("resolved_at"),
                    ),
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False

    def get_alert_by_id(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve alert by alert_id."""
        query = "SELECT * FROM alerts WHERE alert_id = ?"
        with self._get_connection() as conn:
            cursor = conn.execute(query, (alert_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_alert_dict(row)
            return None

    def list_alerts(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all alerts, optionally filtered by status."""
        if status_filter:
            query = "SELECT * FROM alerts WHERE status = ? ORDER BY timestamp DESC"
            params = (status_filter,)
        else:
            query = "SELECT * FROM alerts ORDER BY timestamp DESC"
            params = ()

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            return [self._row_to_alert_dict(row) for row in rows]

    def update_alert_status(
        self,
        alert_id: str,
        new_status: str,
        reviewed_at: Optional[str] = None,
        resolved_at: Optional[str] = None,
    ) -> bool:
        """Update status and timestamps for an alert."""
        query = "UPDATE alerts SET status = ?"
        params = [new_status]

        if reviewed_at:
            query += ", reviewed_at = ?"
            params.append(reviewed_at)

        if resolved_at:
            query += ", resolved_at = ?"
            params.append(resolved_at)

        query += " WHERE alert_id = ?"
        params.append(alert_id)

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0

    # --- INCIDENT DATABASE METHODS ---

    def insert_incident(self, incident_data: Dict[str, Any]) -> bool:
        """Insert a verified incident record."""
        reasons_str = json.dumps(incident_data.get("reasons", []))
        created_at_str = incident_data.get("created_at", datetime.now().isoformat())
        agent_id = incident_data.get("agent_id", incident_data.get("camera_id", "AGENT-07"))

        query = """
            INSERT INTO incidents (
                incident_id, alert_id, camera_id, agent_id, tool_name, target_resource,
                timestamp, risk_score, reasons_json, verification_status, reviewer_action, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            with self._get_connection() as conn:
                conn.execute(
                    query,
                    (
                        incident_data["incident_id"],
                        incident_data["alert_id"],
                        incident_data.get("camera_id", agent_id),
                        agent_id,
                        incident_data.get("tool_name", "execute_command"),
                        incident_data.get("target_resource", "production_server"),
                        incident_data.get("timestamp_seconds", 0.0),
                        incident_data["risk_score_at_alert"],
                        reasons_str,
                        incident_data.get("verification_status", "CONFIRMED_HUMAN_VERIFIED"),
                        incident_data.get("reviewer_action", "Confirmed Staff Verification"),
                        created_at_str,
                    ),
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False

    def list_incidents(self) -> List[Dict[str, Any]]:
        """List all verified incident records."""
        query = "SELECT * FROM incidents ORDER BY created_at DESC"
        with self._get_connection() as conn:
            cursor = conn.execute(query)
            rows = cursor.fetchall()
            return [self._row_to_incident_dict(row) for row in rows]

    # --- OPERATIONAL METRICS & STATS ---

    def get_operational_stats(self) -> Dict[str, Any]:
        """Calculate operational stats from SQLite database records."""
        with self._get_connection() as conn:
            total_alerts = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
            active_alerts = conn.execute(
                "SELECT COUNT(*) FROM alerts WHERE status IN ('NEW', 'UNDER_REVIEW')"
            ).fetchone()[0]
            confirmed_incidents = conn.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
            dismissed_alerts = conn.execute(
                "SELECT COUNT(*) FROM alerts WHERE status = 'DISMISSED'"
            ).fetchone()[0]

            resolved_total = confirmed_incidents + dismissed_alerts
            false_alarm_rate = (
                round((dismissed_alerts / resolved_total) * 100, 1) if resolved_total > 0 else 0.0
            )

            return {
                "active_alerts": active_alerts,
                "total_alerts": total_alerts,
                "confirmed_incidents": confirmed_incidents,
                "dismissed_alerts": dismissed_alerts,
                "false_alarm_rate": false_alarm_rate,
            }

    # --- HELPER ROW CONVERTERS ---

    def _row_to_alert_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert an SQLite Row object to alert dictionary."""
        d = dict(row)
        reasons_raw = d.pop("reasons_json", "[]")
        try:
            d["reasons"] = json.loads(reasons_raw)
        except json.JSONDecodeError:
            d["reasons"] = []

        d["timestamp_seconds"] = d.pop("timestamp", 0.0)
        d["human_verification_required"] = True
        d["agent_id"] = d.get("agent_id") or d.get("camera_id") or "AGENT-07"
        d["tool_name"] = d.get("tool_name") or "execute_command"
        d["target_resource"] = d.get("target_resource") or "production_server"
        d["action_payload"] = d.get("action_payload") or ""
        d["decision"] = d.get("decision") or "BLOCK"
        return d

    def _row_to_incident_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert an SQLite Row object to incident dictionary."""
        d = dict(row)
        reasons_raw = d.pop("reasons_json", "[]")
        try:
            d["reasons"] = json.loads(reasons_raw)
        except json.JSONDecodeError:
            d["reasons"] = []

        d["timestamp_seconds"] = d.pop("timestamp", 0.0)
        d["risk_score_at_alert"] = d.pop("risk_score", 0)
        d["human_verification_required"] = True
        d["agent_id"] = d.get("agent_id") or d.get("camera_id") or "AGENT-07"
        d["tool_name"] = d.get("tool_name") or "execute_command"
        d["target_resource"] = d.get("target_resource") or "production_server"
        return d

    def clear_all_data(self):
        """Clear alerts and incidents tables."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM incidents")
            conn.execute("DELETE FROM alerts")
            conn.commit()
