import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Tuple
import cv2
import numpy as np

from detector import YOLODetector


class VideoProcessor:
    """
    Handles video ingestion, frame-by-frame detection using YOLODetector,
    visual annotation, and saving annotated output video.
    """

    # Distinct BGR color palette for detected classes
    # 'person': Green (0, 255, 0), 'cell phone': Cyan (255, 255, 0) / Orange (0, 165, 255)
    COLOR_MAP = {
        "person": (0, 255, 0),       # Green
        "cell phone": (0, 215, 255),  # Gold/Yellow-Orange
    }
    DEFAULT_COLOR = (255, 0, 0)      # Blue fallback

    def __init__(self, detector: YOLODetector):
        """
        Initialize VideoProcessor with an active detector instance.

        :param detector: Instance of YOLODetector.
        """
        self.detector = detector

    def draw_annotations(self, frame: np.ndarray, detections: list) -> np.ndarray:
        """
        Draw bounding boxes, class names, and confidence scores on the frame.

        :param frame: OpenCV BGR image frame.
        :param detections: List of detection dicts from YOLODetector.
        :return: Annotated OpenCV frame.
        """
        annotated_frame = frame.copy()

        for det in detections:
            x1, y1, x2, y2 = det["box"]
            conf = det["confidence"]
            class_name = det["class_name"]

            # Select color based on object class
            color = self.COLOR_MAP.get(class_name, self.DEFAULT_COLOR)

            # Draw bounding box rectangle
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)

            # Prepare text label
            label = f"{class_name}: {conf:.2f}"
            
            # Label background banner for clarity
            (text_w, text_h), baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1
            )
            banner_y1 = max(0, y1 - text_h - 10)
            banner_y2 = y1

            cv2.rectangle(
                annotated_frame,
                (x1, banner_y1),
                (x1 + text_w + 6, banner_y2),
                color,
                -1,
            )

            # Text text in high-contrast color (black or white based on background)
            text_color = (0, 0, 0)
            cv2.putText(
                annotated_frame,
                label,
                (x1 + 3, banner_y2 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                text_color,
                1,
                cv2.LINE_AA,
            )

        return annotated_frame

    def process_video(
        self, input_path: str, output_path: str
    ) -> Dict[str, Any]:
        """
        Process an input video frame-by-frame, detect objects, annotate,
        write output video, and collect operational metrics.

        :param input_path: Filepath to input .mp4 video.
        :param output_path: Filepath for output .mp4 video.
        :return: Dictionary containing processing statistics.
        """
        input_file = Path(input_path)

        # 1. Error Handling: Check input video existence
        if not input_file.exists():
            raise FileNotFoundError(
                f"\n[ERROR] Input video not found at path: '{input_path}'\n"
                f"Please place a valid .mp4 video file in the 'videos/' directory "
                f"named 'input.mp4'."
            )

        # 2. Error Handling: Open video with OpenCV
        cap = cv2.VideoCapture(str(input_file))
        if not cap.isOpened():
            raise RuntimeError(
                f"\n[ERROR] Could not open video file: '{input_path}'.\n"
                f"The video file may be corrupt or encoded in an unsupported format."
            )

        # Read video metadata
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        input_fps = cap.get(cv2.CAP_PROP_FPS)
        if input_fps <= 0 or np.isnan(input_fps):
            input_fps = 30.0  # Default fallback FPS
        total_input_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Ensure output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Setup VideoWriter with codecs fallback
        fourcc_options = [
            cv2.VideoWriter_fourcc(*"mp4v"),
            cv2.VideoWriter_fourcc(*"avc1"),
            cv2.VideoWriter_fourcc(*"XVID"),
        ]
        
        writer = None
        for fourcc in fourcc_options:
            writer = cv2.VideoWriter(
                str(output_file), fourcc, input_fps, (width, height)
            )
            if writer.isOpened():
                break

        if writer is None or not writer.isOpened():
            cap.release()
            raise RuntimeError(
                f"[ERROR] Could not initialize OpenCV VideoWriter for output file: '{output_path}'"
            )

        print(f"\n==========================================")
        print(f"       CINEGUARD AI - VIDEO PROCESSING     ")
        print(f"==========================================")
        print(f"Input Video  : {input_path}")
        print(f"Resolution   : {width}x{height}")
        print(f"Target FPS   : {input_fps:.2f}")
        print(f"Total Frames : {total_input_frames}")
        print(f"Output Video : {output_path}")
        print(f"------------------------------------------")
        print(f"Processing frames... Please wait.")

        # Metrics counters
        processed_frames_count = 0
        total_person_detections = 0
        total_phone_detections = 0

        start_time = time.time()

        try:
            while True:
                ret, frame = cap.read()
                if not ret or frame is None:
                    break

                processed_frames_count += 1

                # Perform object detection
                detections = self.detector.detect(frame)

                # Count detected objects per class
                for det in detections:
                    cname = det["class_name"]
                    if cname == "person":
                        total_person_detections += 1
                    elif cname == "cell phone":
                        total_phone_detections += 1

                # Draw annotations on frame
                annotated_frame = self.draw_annotations(frame, detections)

                # Write annotated frame to output video
                writer.write(annotated_frame)

                # Print progress update every 30 frames
                if processed_frames_count % 30 == 0 or processed_frames_count == total_input_frames:
                    elapsed = time.time() - start_time
                    current_fps = processed_frames_count / elapsed if elapsed > 0 else 0.0
                    progress_pct = (
                        (processed_frames_count / total_input_frames) * 100
                        if total_input_frames > 0
                        else 0
                    )
                    sys.stdout.write(
                        f"\rProgress: [{processed_frames_count}/{total_input_frames}] "
                        f"{progress_pct:.1f}% | FPS: {current_fps:.2f}"
                    )
                    sys.stdout.flush()

        finally:
            cap.release()
            writer.release()
            print()  # Newline after progress bar

        total_elapsed_time = time.time() - start_time
        avg_processing_fps = (
            processed_frames_count / total_elapsed_time
            if total_elapsed_time > 0
            else 0.0
        )

        metrics = {
            "processed_frames": processed_frames_count,
            "total_person_detections": total_person_detections,
            "total_phone_detections": total_phone_detections,
            "elapsed_seconds": total_elapsed_time,
            "processing_fps": avg_processing_fps,
            "output_file": str(output_file),
        }

        return metrics
