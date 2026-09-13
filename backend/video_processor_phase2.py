import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple
import cv2
import numpy as np

from tracker import ObjectTracker
from behavior_analyzer import BehaviorAnalyzer


class VideoProcessorPhase2:
    """
    Phase 2 Video Processor: Integrates Object Tracker and Behavior Analyzer,
    visualizes tracked objects, cinema screen region, spatial associations,
    and duration HUD, and saves output to videos/output_tracking.mp4.
    """

    # Color palette
    COLOR_PERSON = (0, 255, 0)         # Green for Person
    COLOR_PHONE = (0, 215, 255)        # Gold/Yellow-Orange for Phone
    COLOR_SCREEN_REGION = (0, 255, 255) # Bright Yellow for Cinema Screen Region
    COLOR_ASSOCIATION_LINE = (255, 0, 255) # Magenta for Person <-> Phone link

    def __init__(self, tracker: ObjectTracker, analyzer: BehaviorAnalyzer):
        """
        Initialize VideoProcessorPhase2.

        :param tracker: Instance of ObjectTracker.
        :param analyzer: Instance of BehaviorAnalyzer.
        """
        self.tracker = tracker
        self.analyzer = analyzer

    def draw_screen_region(self, frame: np.ndarray) -> np.ndarray:
        """Draw the configured cinema screen region on the frame."""
        h, w = frame.shape[:2]
        rx1, ry1, rx2, ry2 = self.analyzer.get_screen_region_pixels(w, h)

        # Draw outer bounding box for cinema screen region
        cv2.rectangle(frame, (rx1, ry1), (rx2, ry2), self.COLOR_SCREEN_REGION, 2)

        # Label for Screen Region
        label = "Cinema Screen Region (Configurable)"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(
            frame,
            (rx1, max(0, ry1 - th - 8)),
            (rx1 + tw + 6, ry1),
            self.COLOR_SCREEN_REGION,
            -1,
        )
        cv2.putText(
            frame,
            label,
            (rx1 + 3, ry1 - 4),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 0),
            1,
            cv2.LINE_AA,
        )
        return frame

    def draw_phase2_annotations(
        self,
        frame: np.ndarray,
        tracked_objects: List[Dict[str, Any]],
        behavior_records: List[Dict[str, Any]],
    ) -> np.ndarray:
        """
        Draw tracked objects, anonymous track IDs, screen region, association lines, and HUD.

        :param frame: OpenCV BGR image frame.
        :param tracked_objects: List of tracked object dicts.
        :param behavior_records: Behavioral feature records for current frame.
        :return: Annotated frame.
        """
        annotated_frame = frame.copy()
        h, w = annotated_frame.shape[:2]

        # 1. Draw Cinema Screen Region
        annotated_frame = self.draw_screen_region(annotated_frame)

        # Map track_id -> object dict for fast lookup
        obj_map = {obj["display_id"]: obj for obj in tracked_objects}

        # 2. Draw Tracked Objects (Persons & Phones)
        for obj in tracked_objects:
            x1, y1, x2, y2 = obj["box"]
            display_id = obj["display_id"]
            cname = obj["class_name"]
            conf = obj["confidence"]

            color = self.COLOR_PERSON if cname == "person" else self.COLOR_PHONE

            # Draw bounding box
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)

            # Label text showing Anonymous Track ID and confidence
            label_text = f"{display_id} ({conf:.2f})"
            (tw, th), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            
            banner_y1 = max(0, y1 - th - 8)
            banner_y2 = y1

            cv2.rectangle(
                annotated_frame,
                (x1, banner_y1),
                (x1 + tw + 6, banner_y2),
                color,
                -1,
            )
            cv2.putText(
                annotated_frame,
                label_text,
                (x1 + 3, banner_y2 - 4),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),
                1,
                cv2.LINE_AA,
            )

        # 3. Draw Person <-> Phone Association lines and Behavioral HUD
        hud_lines = []
        for rec in behavior_records:
            phone_tid = rec["phone_track_id"]
            person_tid = rec["person_track_id"]
            phone_disp = f"Phone #{phone_tid}"

            phone_obj = next((o for o in tracked_objects if o["track_id"] == phone_tid and o["class_name"] == "cell phone"), None)
            person_obj = next((o for o in tracked_objects if o["track_id"] == person_tid and o["class_name"] == "person"), None) if person_tid else None

            # Draw connecting line between associated Phone and Person
            if phone_obj and person_obj:
                pcx, pcy = phone_obj["center"]
                hcx, hcy = person_obj["center"]
                cv2.line(annotated_frame, (pcx, pcy), (hcx, hcy), self.COLOR_ASSOCIATION_LINE, 2, cv2.LINE_AA)

            # Prepare HUD text
            screen_status = "INSIDE Screen Region" if rec["phone_in_screen_region"] else "OUTSIDE Screen Region"
            person_status = f"Associated with Person #{person_tid}" if person_tid else "Unassociated"
            dur_str = f"Duration: {rec['duration_seconds']:.1f}s"

            hud_lines.append(
                f"{phone_disp} | {person_status} | Screen: {screen_status} | {dur_str}"
            )

        # 4. Render Top HUD Banner
        if hud_lines:
            banner_height = 25 + len(hud_lines) * 22
            overlay = annotated_frame.copy()
            cv2.rectangle(overlay, (10, 10), (w - 10, 10 + banner_height), (20, 20, 20), -1)
            cv2.addWeighted(overlay, 0.75, annotated_frame, 0.25, 0, annotated_frame)

            cv2.putText(
                annotated_frame,
                "CINEGUARD AI - PHASE 2 BEHAVIORAL FEATURE MONITOR",
                (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 255),
                2,
                cv2.LINE_AA,
            )

            for idx, line in enumerate(hud_lines):
                cv2.putText(
                    annotated_frame,
                    line,
                    (20, 52 + idx * 22),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    1,
                    cv2.LINE_AA,
                )

        return annotated_frame

    def process_video(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """
        Run Phase 2 Video Tracking and Behavioral Extraction pipeline.

        :param input_path: Input video path (videos/input.mp4).
        :param output_path: Output video path (videos/output_tracking.mp4).
        :return: Metrics dictionary including behavior logs.
        """
        input_file = Path(input_path)

        if not input_file.exists():
            raise FileNotFoundError(
                f"\n[ERROR] Input video missing at path: '{input_path}'\n"
                f"Please place 'input.mp4' inside the 'videos/' directory."
            )

        cap = cv2.VideoCapture(str(input_file))
        if not cap.isOpened():
            raise RuntimeError(f"[ERROR] Could not open input video: '{input_path}'")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        input_fps = cap.get(cv2.CAP_PROP_FPS)
        if input_fps <= 0 or np.isnan(input_fps):
            input_fps = 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

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
            raise RuntimeError(f"[ERROR] Failed to create VideoWriter for '{output_path}'")

        print("\n==================================================")
        print("    CINEGUARD AI - PHASE 2 TRACKING & BEHAVIOR    ")
        print("==================================================")
        print(f"Input Video   : {input_path}")
        print(f"Output Video  : {output_path}")
        print(f"Resolution    : {width}x{height} @ {input_fps:.2f} FPS")
        print(f"Total Frames  : {total_frames}")
        print("--------------------------------------------------")
        print("Running tracking & behavioral feature extraction...")

        self.tracker.reset_tracker()
        processed_frames_count = 0
        all_behavior_logs = []
        start_time = time.time()

        try:
            while True:
                ret, frame = cap.read()
                if not ret or frame is None:
                    break

                # 1. Multi-object tracking
                tracked_objects = self.tracker.track_frame(frame)

                # 2. Behavioral feature analysis
                behavior_records = self.analyzer.analyze_frame(
                    tracked_objects=tracked_objects,
                    frame_idx=processed_frames_count,
                    fps=input_fps,
                    frame_width=width,
                    frame_height=height,
                )

                if behavior_records:
                    all_behavior_logs.extend(behavior_records)

                # 3. Annotation visualization
                annotated_frame = self.draw_phase2_annotations(
                    frame, tracked_objects, behavior_records
                )

                writer.write(annotated_frame)
                processed_frames_count += 1

                if processed_frames_count % 30 == 0 or processed_frames_count == total_frames:
                    elapsed = time.time() - start_time
                    fps_now = processed_frames_count / elapsed if elapsed > 0 else 0
                    pct = (processed_frames_count / total_frames * 100) if total_frames > 0 else 0
                    sys.stdout.write(
                        f"\rProgress: [{processed_frames_count}/{total_frames}] {pct:.1f}% | FPS: {fps_now:.2f}"
                    )
                    sys.stdout.flush()

        finally:
            cap.release()
            writer.release()
            print()

        total_elapsed = time.time() - start_time
        avg_fps = processed_frames_count / total_elapsed if total_elapsed > 0 else 0

        # Extract unique track IDs for summary
        unique_persons = set()
        unique_phones = set()
        for log in all_behavior_logs:
            if log.get("person_track_id") is not None:
                unique_persons.add(log["person_track_id"])
            if log.get("phone_track_id") is not None:
                unique_phones.add(log["phone_track_id"])

        metrics = {
            "processed_frames": processed_frames_count,
            "unique_persons_tracked": len(unique_persons),
            "unique_phones_tracked": len(unique_phones),
            "total_behavior_records": len(all_behavior_logs),
            "elapsed_seconds": total_elapsed,
            "processing_fps": avg_fps,
            "output_file": str(output_file),
            "behavior_logs": all_behavior_logs,
        }

        return metrics
