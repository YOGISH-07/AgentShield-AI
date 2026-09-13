import os
import sys
import json
from pathlib import Path

# Ensure backend directory is in python path
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

project_root = current_dir.parent

from tracker import ObjectTracker
from behavior_analyzer import BehaviorAnalyzer
from risk_engine import RiskEngine
from video_processor_phase3 import VideoProcessorPhase3
from database import DatabaseManager
from alert_manager import AlertManager


def main():
    """
    CineGuard AI - Phase 4 Integration Execution Script:
    YOLO -> Tracking -> Behavior Analysis -> Risk Engine -> Alert Manager -> SQLite Database.
    """
    print("==================================================")
    print("        CineGuard AI - Phase 4 Prototype          ")
    print("  Real-Time Alert Management & SQLite Integration ")
    print("==================================================")

    input_video_path = project_root / "videos" / "input.mp4"
    output_video_path = project_root / "videos" / "output_risk.mp4"
    models_dir_path = project_root / "models"
    db_path = project_root / "data" / "cineguard.db"

    print(f"\n[1/5] Initializing Database & Alert Manager ({db_path})...")
    db = DatabaseManager(db_path=str(db_path))
    alert_manager = AlertManager(db=db, cooldown_seconds=5.0)

    print(f"[2/5] Initializing Object Tracker...")
    try:
        tracker = ObjectTracker(
            model_name_or_path="yolov8n.pt",
            models_dir=str(models_dir_path),
            conf_threshold=0.4,
            tracker_type="bytetrack.yaml",
        )
    except Exception as e:
        print(f"\n[ERROR] Could not initialize tracker: {e}\n")
        sys.exit(1)

    print(f"[3/5] Initializing Behavior Analyzer & Risk Engine...")
    screen_region = {"x1": 0.20, "y1": 0.10, "x2": 0.80, "y2": 0.60}
    analyzer = BehaviorAnalyzer(screen_region=screen_region, proximity_threshold_px=180.0)
    risk_engine = RiskEngine(camera_id="CAM-01", alert_threshold=70, state_timeout_seconds=5.0)

    processor = VideoProcessorPhase3(tracker=tracker, analyzer=analyzer, risk_engine=risk_engine)

    print(f"[4/5] Processing Video Stream & Streaming Alert Events to Database...")
    try:
        metrics = processor.process_video(
            input_path=str(input_video_path),
            output_path=str(output_video_path),
        )
    except Exception as e:
        print(f"\n[UNEXPECTED ERROR] {e}\n")
        sys.exit(1)

    # Ingest generated alert events into AlertManager & SQLite Database
    alerts_created = []
    if metrics["alerts"]:
        for alert_ev in metrics["alerts"]:
            created_alert = alert_manager.create_alert(alert_ev)
            if created_alert:
                alerts_created.append(created_alert)

    # Demonstrate Human-in-the-loop lifecycle transition workflow on first created alert
    if alerts_created:
        sample_alert_id = alerts_created[0]["alert_id"]
        print(f"\n[5/5] Demonstrating Human-in-the-loop Workflow on Alert: '{sample_alert_id}'...")
        
        # Transition 1: NEW -> UNDER_REVIEW
        under_review = alert_manager.start_review(sample_alert_id, reviewer_action="Security Staff Review Started")
        print(f"  -> State updated: {under_review['status']} (Reviewed at: {under_review['reviewed_at']})")

        # Transition 2: UNDER_REVIEW -> CONFIRMED (Creates Incident Record)
        confirmed = alert_manager.confirm_alert(sample_alert_id, reviewer_action="Staff Verified Screen Alignment")
        print(f"  -> State updated: {confirmed['status']} (Incident ID: {confirmed['incident']['incident_id']})")

    # Fetch Operational Stats directly from SQLite Database
    stats = alert_manager.get_operational_stats()

    print("\n==================================================")
    print("       CINEGUARD AI - PHASE 4 SUMMARY REPORT      ")
    print("==================================================")
    print(f" Frames Processed      : {metrics['processed_frames']}")
    print(f" Risk Alerts Generated : {len(metrics['alerts'])}")
    print(f" DB Alerts Ingested    : {len(alerts_created)}")
    print(f" SQLite Database Path  : {db_path}")
    print("--------------------------------------------------")
    print(" SQLite Operational Statistics:")
    print(f"   Active Alerts       : {stats['active_alerts']}")
    print(f"   Total Alerts        : {stats['total_alerts']}")
    print(f"   Confirmed Incidents : {stats['confirmed_incidents']}")
    print(f"   Dismissed Alerts    : {stats['dismissed_alerts']}")
    print(f"   False Alarm Rate    : {stats['false_alarm_rate']:.2%}")
    print("==================================================\n")
    print("Phase 4 complete! SQLite database updated at data/cineguard.db.")


if __name__ == "__main__":
    main()
