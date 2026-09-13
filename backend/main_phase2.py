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
from video_processor_phase2 import VideoProcessorPhase2


def main():
    """
    CineGuard AI - Phase 2 Execution Script:
    Multi-Object Tracking, Person-Phone Association & Behavior Feature Extraction.
    """
    print("==================================================")
    print("        CineGuard AI - Phase 2 Prototype          ")
    print("   Object Tracking & Behavior Feature Extraction  ")
    print("==================================================")

    input_video_path = project_root / "videos" / "input.mp4"
    output_video_path = project_root / "videos" / "output_tracking.mp4"
    models_dir_path = project_root / "models"

    print(f"\n[1/3] Initializing YOLO Object Tracker...")
    try:
        tracker = ObjectTracker(
            model_name_or_path="yolov8n.pt",
            models_dir=str(models_dir_path),
            conf_threshold=0.4,
            tracker_type="bytetrack.yaml",
        )
    except ImportError as e:
        print(f"\n[CRITICAL DEPENDENCY ERROR] {e}")
        print("Please install requirements using: pip install -r backend/requirements.txt\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n[MODEL TRACKER ERROR] {e}\n")
        sys.exit(1)

    print(f"[2/3] Configuring Behavior Analyzer & Screen Region...")
    # Cinema Screen Region (normalized bounds: x1=0.20, y1=0.10, x2=0.80, y2=0.60)
    screen_region = {"x1": 0.20, "y1": 0.10, "x2": 0.80, "y2": 0.60}
    analyzer = BehaviorAnalyzer(screen_region=screen_region, proximity_threshold_px=180.0)

    processor = VideoProcessorPhase2(tracker=tracker, analyzer=analyzer)

    print(f"[3/3] Processing Video Stream for Phase 2...")
    try:
        metrics = processor.process_video(
            input_path=str(input_video_path),
            output_path=str(output_video_path),
        )
    except FileNotFoundError as e:
        print(e)
        print("\nTip: Generate a sample test video by running:")
        print("    python backend/generate_test_video.py\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n[UNEXPECTED ERROR] {e}\n")
        sys.exit(1)

    # Calculate statistics from behavior logs
    behavior_logs = metrics.get("behavior_logs", [])
    max_duration = max((log["duration_seconds"] for log in behavior_logs), default=0.0)
    screen_entries = sum(1 for log in behavior_logs if log["phone_in_screen_region"])

    # Sample behavior record format display (Requirement #6)
    sample_record = behavior_logs[0] if behavior_logs else {}

    print("\n==================================================")
    print("       CINEGUARD AI - PHASE 2 SUMMARY REPORT      ")
    print("==================================================")
    print(f" Total Frames Processed   : {metrics['processed_frames']}")
    print(f" Tracked Persons Count    : {metrics['unique_persons_tracked']}")
    print(f" Tracked Phones Count     : {metrics['unique_phones_tracked']}")
    print(f" Screen Region Matches    : {screen_entries} frame instances")
    print(f" Max Behavior Duration    : {max_duration:.2f} seconds")
    print(f" Processing Time          : {metrics['elapsed_seconds']:.2f} s ({metrics['processing_fps']:.2f} FPS)")
    print(f" Output Tracking Video    : {metrics['output_file']}")
    print("--------------------------------------------------")
    print(" Sample Behavior Feature Record:")
    if sample_record:
        print(json.dumps(sample_record, indent=4))
    else:
        print("  (No phone detections in input video stream)")
    print("==================================================\n")
    print("Phase 2 complete! Output video saved to videos/output_tracking.mp4.")


if __name__ == "__main__":
    main()
