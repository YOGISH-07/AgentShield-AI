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


def main():
    """
    CineGuard AI - Phase 3 Execution Script:
    Explainable Behavioral Risk Engine & Alert Generation System.
    """
    print("==================================================")
    print("        CineGuard AI - Phase 3 Prototype          ")
    print("  Explainable Behavioral Risk Engine & Alerting   ")
    print("==================================================")

    input_video_path = project_root / "videos" / "input.mp4"
    output_video_path = project_root / "videos" / "output_risk.mp4"
    models_dir_path = project_root / "models"

    print(f"\n[1/4] Initializing Object Tracker...")
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

    print(f"[2/4] Initializing Behavior Analyzer...")
    screen_region = {"x1": 0.20, "y1": 0.10, "x2": 0.80, "y2": 0.60}
    analyzer = BehaviorAnalyzer(screen_region=screen_region, proximity_threshold_px=180.0)

    print(f"[3/4] Initializing Risk Engine (Camera: CAM-01, Alert Threshold: 70)...")
    risk_engine = RiskEngine(
        camera_id="CAM-01",
        alert_threshold=70,
        state_timeout_seconds=5.0,
    )

    processor = VideoProcessorPhase3(
        tracker=tracker, analyzer=analyzer, risk_engine=risk_engine
    )

    print(f"[4/4] Processing Video Stream for Phase 3...")
    try:
        metrics = processor.process_video(
            input_path=str(input_video_path),
            output_path=str(output_video_path),
        )
    except FileNotFoundError as e:
        print(e)
        print("\nTip: Generate a test video using: python backend/generate_test_video.py\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n[UNEXPECTED ERROR] {e}\n")
        sys.exit(1)

    # Output Summary Report
    print("\n==================================================")
    print("       CINEGUARD AI - PHASE 3 SUMMARY REPORT      ")
    print("==================================================")
    print(f" Total Frames Processed  : {metrics['processed_frames']}")
    print(f" Maximum Behavioral Risk : {metrics['max_risk_score']}/100")
    print(f" Total Alert Events      : {metrics['total_alerts']}")
    print(f" Processing Time         : {metrics['elapsed_seconds']:.2f} s ({metrics['processing_fps']:.2f} FPS)")
    print(f" Output Risk Video Saved : {metrics['output_file']}")
    print("--------------------------------------------------")
    
    if metrics["alerts"]:
        print(" Triggered Alert Payload(s):")
        for alert in metrics["alerts"]:
            print(json.dumps(alert, indent=4))
    else:
        print(" No alert threshold crossings occurred during this stream.")

    print("--------------------------------------------------")
    print(" Sample Risk Assessment Record:")
    if metrics["sample_assessment"]:
        print(json.dumps(metrics["sample_assessment"], indent=4))
    else:
        print("  (No relevant target detections)")
    print("==================================================\n")
    print("Phase 3 complete! Output video saved to videos/output_risk.mp4.")


if __name__ == "__main__":
    main()
