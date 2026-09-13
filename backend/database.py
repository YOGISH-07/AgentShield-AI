import os
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


class DatabaseManager:
    """
    SQLite Database Manager for CineGuard AI.
    Handles thread-safe parameterized storage for alerts and verified incidents
    targeting data/cineguard.db.
    """

    def __init__(self, db_path: str = "data/cineguard.db"):
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
            
            # Table 1: Alerts Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT UNIQUE NOT NULL,
                    camera_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    person_track_id INTEGER,
                    phone_track_id INTEGER,
                    risk_score INTEGER NOT NULL,
                    classification TEXT NOT NULL,
                    reasons_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    reviewed_at TEXT,
                    resolved_at TEXT
                )
                """
            )

            # Table 2: Incidents Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_id TEXT UNIQUE NOT NULL,
                    alert_id TEXT NOT NULL,
                    camera_id TEXT NOT NULL,
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

        query = """
            INSERT INTO alerts (
                alert_id, camera_id, timestamp, person_track_id, phone_track_id,
                risk_score, classification, reasons_json, status, created_at,
                reviewed_at, resolved_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            with self._get_connection() as conn:
                conn.execute(
                    query,
                    (
                        alert_data["alert_id"],
                        alert_data["camera_id"],
                        alert_data["timestamp_seconds"],
                        alert_data.get("person_track_id"),
                        alert_data.get("phone_track_id"),
                        alert_data["risk_score"],
                        alert_data["classification"],
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
            return False  # Duplicate alert_id ignored

    def get_alert_by_id(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an alert record by alert_id."""
        query = "SELECT * FROM alerts WHERE alert_id = ?"
        with self._get_connection() as conn:
            row = conn.execute(query, (alert_id,)).fetchone()
            if row:
                return self._row_to_alert_dict(row)
        return None

    def list_alerts(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all alerts, optionally filtered by lifecycle status."""
        if status_filter:
            query = "SELECT * FROM alerts WHERE status = ? ORDER BY id DESC"
            params = (status_filter,)
        else:
            query = "SELECT * FROM alerts ORDER BY id DESC"
            params = ()

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_alert_dict(row) for row in rows]

    def update_alert_status(
        self, alert_id: str, new_status: str, reviewed_at: Optional[str] = None, resolved_at: Optional[str] = None
    ) -> bool:
        """Update lifecycle status and timestamp fields of an alert."""
        query = """
            UPDATE alerts
            SET status = ?,
                reviewed_at = COALESCE(?, reviewed_at),
                resolved_at = COALESCE(?, resolved_at)
            WHERE alert_id = ?
        """
        with self._get_connection() as conn:
            cursor = conn.execute(query, (new_status, reviewed_at, resolved_at, alert_id))
            conn.commit()
            return cursor.rowcount > 0

    # --- INCIDENT DATABASE METHODS ---

    def insert_incident(self, incident_data: Dict[str, Any]) -> bool:
        """Insert a new incident record into database."""
        reasons_str = json.dumps(incident_data.get("reasons", []))
        query = """
            INSERT INTO incidents (
                incident_id, alert_id, camera_id, timestamp, risk_score,
                reasons_json, verification_status, reviewer_action, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            with self._get_connection() as conn:
                conn.execute(
                    query,
                    (
                        incident_data["incident_id"],
                        incident_data["alert_id"],
                        incident_data["camera_id"],
                        incident_data["timestamp_seconds"],
                        incident_data["risk_score_at_alert"],
                        reasons_str,
                        incident_data.get("verification_status", "CONFIRMED_OBSERVED_BEHAVIOR"),
                        incident_data.get("reviewer_action", "confirmed"),
                        incident_data.get("created_at", datetime.now().isoformat()),
                    ),
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def list_incidents(self) -> List[Dict[str, Any]]:
        """List all verified incident records."""
        query = "SELECT * FROM incidents ORDER BY id DESC"
        with self._get_connection() as conn:
            rows = conn.execute(query).fetchall()
            return [self._row_to_incident_dict(row) for row in rows]

    # --- OPERATIONAL STATISTICS & CLEANUP ---

    def get_operational_stats(self) -> Dict[str, Any]:
        """Calculate real-time operational statistics directly from database records."""
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
                round(dismissed_alerts / resolved_total, 4) if resolved_total > 0 else 0.0
            )

            return {
                "active_alerts": active_alerts,
                "total_alerts": total_alerts,
                "confirmed_incidents": confirmed_incidents,
                "dismissed_alerts": dismissed_alerts,
                "false_alarm_rate": false_alarm_rate,
            }

    def cleanup_expired_records(self, days: int = 7) -> int:
        """
        Delete alert and incident records created older than specified days.
        Does NOT automatically run during testing.
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        with self._get_connection() as conn:
            c1 = conn.execute("DELETE FROM incidents WHERE created_at < ?", (cutoff_date,)).rowcount
            c2 = conn.execute("DELETE FROM alerts WHERE created_at < ?", (cutoff_date,)).rowcount
            conn.commit()
            return c1 + c2

    # --- ROW HELPER CONVERTERS ---

    @staticmethod
    def _row_to_alert_dict(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "alert_id": row["alert_id"],
            "camera_id": row["camera_id"],
            "timestamp_seconds": row["timestamp"],
            "person_track_id": row["person_track_id"],
            "phone_track_id": row["phone_track_id"],
            "risk_score": row["risk_score"],
            "classification": row["classification"],
            "reasons": json.loads(row["reasons_json"]),
            "status": row["status"],
            "human_verification_required": True,
            "created_at": row["created_at"],
            "reviewed_at": row["reviewed_at"],
            "resolved_at": row["resolved_at"],
        }

    @staticmethod
    def _row_to_incident_dict(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "incident_id": row["incident_id"],
            "alert_id": row["alert_id"],
            "camera_id": row["camera_id"],
            "timestamp_seconds": row["timestamp"],
            "risk_score_at_alert": row["risk_score"],
            "reasons": json.loads(row["reasons_json"]),
            "verification_status": row["verification_status"],
            "reviewer_action": row["reviewer_action"],
            "human_verification_required": True,
            "created_at": row["created_at"],
        }
