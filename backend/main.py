import os
import sys
from pathlib import Path

# Ensure backend directory is in python path when running main.py directly
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Resolve root directory (parent of backend folder)
project_root = current_dir.parent

from detector import YOLODetector
from video_processor import VideoProcessor


def main():
    """
    CineGuard AI - Main Execution Script
    """
    print("==================================================")
    print("        CineGuard AI - Phase 1 Prototype          ")
    print("  Computer-Vision Smartphone & Person Detector    ")
    print("==================================================")

    # Path configurations (relative to project root)
    input_video_path = project_root / "videos" / "input.mp4"
    output_video_path = project_root / "videos" / "output_detection.mp4"
    models_dir_path = project_root / "models"

    print(f"\n[1/3] Validating Environment & Model...")
    try:
        # Initialize YOLO Detector (downloads yolov8n.pt to models/ if not present)
        detector = YOLODetector(
            model_name_or_path="yolov8n.pt",
            models_dir=str(models_dir_path),
            conf_threshold=0.4,
        )
    except ImportError as e:
        print(f"\n[CRITICAL DEPENDENCY ERROR] {e}")
        print("Please install required packages using:")
        print("    pip install -r backend/requirements.txt\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n[MODEL INITIALIZATION ERROR] {e}\n")
        sys.exit(1)

    print(f"[2/3] Initializing Video Processor...")
    processor = VideoProcessor(detector=detector)

    print(f"[3/3] Processing Video Stream...")
    try:
        metrics = processor.process_video(
            input_path=str(input_video_path),
            output_path=str(output_video_path),
        )
    except FileNotFoundError as e:
        print(e)
        print("\nTip: You can generate a sample test video by running:")
        print("    python backend/generate_test_video.py\n")
        sys.exit(1)
    except RuntimeError as e:
        print(e)
        sys.exit(1)
    except Exception as e:
        print(f"\n[UNEXPECTED ERROR] An unexpected error occurred: {e}\n")
        sys.exit(1)

    # Requirement 9: Print useful processing information in terminal
    print("\n==================================================")
    print("         CINEGUARD AI - PROCESSING SUMMARY        ")
    print("==================================================")
    print(f" Frames Processed  : {metrics['processed_frames']}")
    print(f" People Detections : {metrics['total_person_detections']} total frame instances")
    print(f" Phone Detections  : {metrics['total_phone_detections']} total frame instances")
    print(f" Processing Time   : {metrics['elapsed_seconds']:.2f} seconds")
    print(f" Processing Speed  : {metrics['processing_fps']:.2f} FPS")
    print(f" Output Video Saved: {metrics['output_file']}")
    print("==================================================\n")
    print("Processing complete! Output saved to videos/output_detection.mp4.")


if __name__ == "__main__":
    main()
