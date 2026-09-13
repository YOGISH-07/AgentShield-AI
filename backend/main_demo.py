import os
import sys
import json
import time
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


def run_demo_pipeline():
    """
    Execute Phase 6 Demonstration Pipeline.
    Processes videos/demo_cinema.mp4 -> videos/demo_output_risk.mp4,
    logs a real-time timeline, ingests alerts into SQLite, and outputs summary metrics.
    """
    print("==================================================")
    print("        CineGuard AI - Phase 6 Demonstration       ")
    print("   Realistic 25-Second Computer-Vision Scenario   ")
    print("==================================================")

    input_video = project_root / "videos" / "demo_cinema.mp4"
    output_video = project_root / "videos" / "demo_output_risk.mp4"
    models_dir = project_root / "models"
    db_path = project_root / "data" / "cineguard.db"

    # Ensure input video exists
    if not input_video.exists():
        print(f"Generating demonstration test video '{input_video}'...")
        from generate_demo_scenario import create_demo_scenario_video
        create_demo_scenario_video(str(input_video))

    print(f"\n[1/4] Initializing Database & Alert Manager...")
    db = DatabaseManager(db_path=str(db_path))
    alert_manager = AlertManager(db=db, cooldown_seconds=5.0)

    print(f"[2/4] Initializing Object Tracker (yolov8n.pt)...")
    tracker = ObjectTracker(
        model_name_or_path="yolov8n.pt",
        models_dir=str(models_dir),
        conf_threshold=0.4,
        tracker_type="bytetrack.yaml",
    )

    print(f"[3/4] Initializing Behavior Analyzer & Calibrated Risk Engine...")
    screen_region = {"x1": 0.20, "y1": 0.10, "x2": 0.80, "y2": 0.60}
    analyzer = BehaviorAnalyzer(screen_region=screen_region, proximity_threshold_px=180.0)
    risk_engine = RiskEngine(camera_id="CAM-01", alert_threshold=70, state_timeout_seconds=5.0)

    processor = VideoProcessorPhase3(tracker=tracker, analyzer=analyzer, risk_engine=risk_engine)

    print(f"\n[4/4] Processing Demo Video & Generating Real-Time Timeline Logs...")
    print(f"Input Video  : {input_video}")
    print(f"Output Video : {output_video}")
    print("--------------------------------------------------------------------------------")
    print(f"{'TIME':<8} | {'FRAME':<10} | {'CLASSIFICATION':<22} | {'RISK SCORE':<12} | {'TIMELINE EVENT / SIGNAL'}")
    print("--------------------------------------------------------------------------------")

    import cv2
    cap = cv2.VideoCapture(str(input_video))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    output_file = Path(output_video)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(output_file), fourcc, fps, (width, height))

    tracker.reset_tracker()
    processed_frames = 0
    max_risk_score = 0
    alert_events = []
    start_wall_time = time.time()

    # Define milestone frames to print timeline checkpoints
    checkpoint_frames = {0, 150, 300, 450, 600, 749}

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            # 1. Tracking
            tracked_objects = tracker.track_frame(frame)

            # 2. Behavior Analysis
            behavior_records = analyzer.analyze_frame(
                tracked_objects=tracked_objects,
                frame_idx=processed_frames,
                fps=fps,
                frame_width=width,
                frame_height=height,
            )

            # 3. Risk Engine Evaluation
            frame_assessments = []
            alert_on_this_frame = None

            if behavior_records:
                for rec in behavior_records:
                    ass = risk_engine.evaluate_record(rec)
                    frame_assessments.append(ass)
                    if ass["risk_score"] > max_risk_score:
                        max_risk_score = ass["risk_score"]

                    if ass.get("alert_event"):
                        alert_ev = ass["alert_event"]
                        alert_events.append(alert_ev)
                        alert_on_this_frame = alert_ev
                        # Ingest into AlertManager & SQLite DB
                        alert_manager.create_alert(alert_ev)
            else:
                # Default baseline evaluation when no phone detected
                base_rec = {
                    "frame_idx": processed_frames,
                    "timestamp_seconds": processed_frames / fps,
                    "phone_detected": False,
                    "person_detected": len([o for o in tracked_objects if o["class_name"] == "person"]) > 0,
                    "phone_near_person": False,
                    "phone_in_screen_region": False,
                    "duration_seconds": 0.0,
                }
                ass = risk_engine.evaluate_record(base_rec)
                frame_assessments.append(ass)

            # 4. Render Phase 3 HUD
            annotated_frame = processor.draw_phase3_hud(
                frame, tracked_objects, frame_assessments
            )
            writer.write(annotated_frame)

            # Determine primary assessment for timeline log
            primary_ass = frame_assessments[0] if frame_assessments else {"risk_score": 0, "classification": "NORMAL"}
            t_sec = processed_frames / fps

            # Print timeline logs on milestone checkpoints or when an alert occurs
            if processed_frames in checkpoint_frames or alert_on_this_frame:
                event_desc = []
                if alert_on_this_frame:
                    event_desc.append(f"[ALERT TRIGGERED: {alert_on_this_frame['alert_id']}]")
                elif processed_frames == 0:
                    event_desc.append("SCENE 1: NORMAL (Person only)")
                elif processed_frames == 150:
                    event_desc.append("SCENE 2: PHONE APPEARS (Outside screen region)")
                elif processed_frames == 300:
                    event_desc.append("SCENE 3: SUSTAINED BEHAVIOR (Inside screen region)")
                elif processed_frames == 600:
                    event_desc.append("SCENE 4: BEHAVIOR ENDS (Phone removed)")
                elif processed_frames == 749:
                    event_desc.append("DEMO END")

                print(
                    f"{t_sec:>5.1f}s   | Frame {processed_frames:<4} | "
                    f"{primary_ass['classification']:<22} | "
                    f"Risk: {primary_ass['risk_score']:>2}/100 | "
                    f"{' '.join(event_desc)}"
                )

            processed_frames += 1

    finally:
        cap.release()
        writer.release()

    total_wall_time = time.time() - start_wall_time
    avg_fps = processed_frames / total_wall_time if total_wall_time > 0 else 0
    output_size = output_file.stat().st_size if output_file.exists() else 0

    first_alert_ts = alert_events[0]["timestamp_seconds"] if alert_events else "N/A"

    print("--------------------------------------------------------------------------------")
    print("\n==================================================")
    print("       CINEGUARD AI - PHASE 6 DEMO SUMMARY        ")
    print("==================================================")
    print(f" Demo Video Duration  : {processed_frames / fps:.1f} seconds ({processed_frames} frames)")
    print(f" Maximum Risk Score   : {max_risk_score}/100")
    print(f" Total Alert Events   : {len(alert_events)}")
    print(f" First Alert Timestamp: {first_alert_ts}s")
    print(f" Processing Speed     : {avg_fps:.2f} FPS (Wall time: {total_wall_time:.2f}s)")
    print(f" Output Video File    : {output_file} ({output_size} bytes)")
    print("==================================================\n")


if __name__ == "__main__":
    run_demo_pipeline()
