import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple
import cv2
import numpy as np

from tracker import ObjectTracker
from behavior_analyzer import BehaviorAnalyzer
from risk_engine import RiskEngine


class VideoProcessorPhase3:
    """
    Phase 3 Video Processor: Combines ObjectTracker, BehaviorAnalyzer, and RiskEngine.
    Visualizes Risk Score HUD, Explainable Reasons, Classification Status,
    and saves output video to videos/output_risk.mp4.
    """

    COLOR_PERSON = (0, 255, 0)           # Green for Person
    COLOR_PHONE = (0, 215, 255)          # Gold/Yellow-Orange for Phone
    COLOR_SCREEN_REGION = (0, 255, 255)   # Yellow for Cinema Screen Region
    COLOR_ASSOCIATION_LINE = (255, 0, 255) # Magenta for link line

    # Classification HUD status colors
    COLOR_NORMAL = (0, 255, 0)           # Green
    COLOR_WATCH = (0, 165, 255)          # Orange
    COLOR_SUSPECTED = (0, 0, 255)        # Red

    def __init__(
        self,
        tracker: ObjectTracker,
        analyzer: BehaviorAnalyzer,
        risk_engine: RiskEngine,
    ):
        """
        Initialize VideoProcessorPhase3.

        :param tracker: ObjectTracker instance.
        :param analyzer: BehaviorAnalyzer instance.
        :param risk_engine: RiskEngine instance.
        """
        self.tracker = tracker
        self.analyzer = analyzer
        self.risk_engine = risk_engine

    def draw_phase3_hud(
        self,
        frame: np.ndarray,
        tracked_objects: List[Dict[str, Any]],
        assessments: List[Dict[str, Any]],
    ) -> np.ndarray:
        """
        Draw Risk Score HUD, Classification Status, and Explainable Reasons on frame.

        :param frame: OpenCV BGR image frame.
        :param tracked_objects: List of tracked object dicts.
        :param assessments: Risk assessment dicts for current frame.
        :return: Annotated frame.
        """
        annotated_frame = frame.copy()
        h, w = annotated_frame.shape[:2]

        # 1. Draw Screen Region Box
        rx1, ry1, rx2, ry2 = self.analyzer.get_screen_region_pixels(w, h)
        cv2.rectangle(annotated_frame, (rx1, ry1), (rx2, ry2), self.COLOR_SCREEN_REGION, 2)
        cv2.putText(
            annotated_frame,
            "Cinema Screen Region (Configurable)",
            (rx1 + 4, ry1 - 6),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            self.COLOR_SCREEN_REGION,
            1,
            cv2.LINE_AA,
        )

        # 2. Draw Tracked Objects & Bounding Boxes
        for obj in tracked_objects:
            x1, y1, x2, y2 = obj["box"]
            display_id = obj["display_id"]
            cname = obj["class_name"]
            color = self.COLOR_PERSON if cname == "person" else self.COLOR_PHONE

            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                annotated_frame,
                display_id,
                (x1 + 2, y1 - 4),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
                cv2.LINE_AA,
            )

        # 3. Draw Person <-> Phone Association line
        for ass in assessments:
            phone_tid = ass["phone_track_id"]
            person_tid = ass["person_track_id"]
            phone_obj = next((o for o in tracked_objects if o["track_id"] == phone_tid and o["class_name"] == "cell phone"), None)
            person_obj = next((o for o in tracked_objects if o["track_id"] == person_tid and o["class_name"] == "person"), None) if person_tid else None

            if phone_obj and person_obj:
                cv2.line(
                    annotated_frame,
                    phone_obj["center"],
                    person_obj["center"],
                    self.COLOR_ASSOCIATION_LINE,
                    2,
                    cv2.LINE_AA,
                )

        # 4. Render Explainable Risk Score HUD Panel (Top Left)
        if assessments:
            top_ass = max(assessments, key=lambda a: a["risk_score"])
            score = top_ass["risk_score"]
            classification = top_ass["classification"]
            reasons = top_ass["reasons"][:3]  # Display up to 3 short reasons
            phone_tid = top_ass["phone_track_id"]
            person_tid = top_ass["person_track_id"]

            status_color = (
                self.COLOR_SUSPECTED
                if classification == "SUSPECTED_RECORDING"
                else (self.COLOR_WATCH if classification == "WATCH" else self.COLOR_NORMAL)
            )

            status_text = (
                "SUSPECTED RECORDING BEHAVIOR"
                if classification == "SUSPECTED_RECORDING"
                else classification
            )

            # Panel dimensions
            panel_height = 110 + len(reasons) * 20
            overlay = annotated_frame.copy()
            cv2.rectangle(overlay, (10, 10), (450, 10 + panel_height), (15, 15, 15), -1)
            cv2.addWeighted(overlay, 0.8, annotated_frame, 0.2, 0, annotated_frame)

            # Header
            cv2.putText(
                annotated_frame,
                "CINEGUARD AI - RISK ENGINE",
                (20, 32),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

            # Track ID info
            target_str = f"Target: Phone #{phone_tid}" + (f" | Person #{person_tid}" if person_tid else "")
            cv2.putText(
                annotated_frame,
                target_str,
                (20, 52),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48,
                (200, 200, 200),
                1,
                cv2.LINE_AA,
            )

            # Behavioral Risk Score
            score_str = f"Behavioral Risk: {score}/100"
            cv2.putText(
                annotated_frame,
                score_str,
                (20, 75),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                status_color,
                2,
                cv2.LINE_AA,
            )

            # Status Banner
            cv2.putText(
                annotated_frame,
                f"Status: {status_text}",
                (20, 96),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                status_color,
                1,
                cv2.LINE_AA,
            )

            # Reasons list
            for i, reason in enumerate(reasons):
                cv2.putText(
                    annotated_frame,
                    f" - {reason}",
                    (25, 118 + i * 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.42,
                    (230, 230, 230),
                    1,
                    cv2.LINE_AA,
                )

            # 5. Render Alert Trigger Popup Banner (if alert fired on this frame)
            alert_ev = top_ass.get("alert_event")
            if alert_ev:
                alert_banner_y = h - 60
                cv2.rectangle(
                    annotated_frame,
                    (10, alert_banner_y),
                    (w - 10, alert_banner_y + 45),
                    (0, 0, 180),
                    -1,
                )
                cv2.rectangle(
                    annotated_frame,
                    (10, alert_banner_y),
                    (w - 10, alert_banner_y + 45),
                    (0, 0, 255),
                    2,
                )
                cv2.putText(
                    annotated_frame,
                    f"[ALERT GENERATED] {alert_ev['alert_id']} | Risk Score: {score}/100",
                    (25, alert_banner_y + 28),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA,
                )

        return annotated_frame

    def process_video(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """
        Run Phase 3 Risk Pipeline on input video.

        :param input_path: Input video filepath (videos/input.mp4).
        :param output_path: Output video filepath (videos/output_risk.mp4).
        :return: Metrics dictionary including generated alerts and assessments.
        """
        input_file = Path(input_path)
        if not input_file.exists():
            raise FileNotFoundError(f"[ERROR] Input video missing at: '{input_path}'")

        cap = cv2.VideoCapture(str(input_file))
        if not cap.isOpened():
            raise RuntimeError(f"[ERROR] Could not open video file: '{input_path}'")

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
            raise RuntimeError(f"[ERROR] Could not open VideoWriter for '{output_path}'")

        print("\n==================================================")
        print("   CINEGUARD AI - PHASE 3 RISK ENGINE PIPELINE    ")
        print("==================================================")
        print(f"Input Video   : {input_path}")
        print(f"Output Video  : {output_path}")
        print(f"Resolution    : {width}x{height} @ {input_fps:.2f} FPS")
        print(f"Total Frames  : {total_frames}")
        print("--------------------------------------------------")

        self.tracker.reset_tracker()
        processed_frames = 0
        all_assessments = []
        all_alerts = []
        max_score = 0
        start_time = time.time()

        try:
            while True:
                ret, frame = cap.read()
                if not ret or frame is None:
                    break

                # 1. Object tracking
                tracked_objects = self.tracker.track_frame(frame)

                # 2. Behavioral analysis
                behavior_records = self.analyzer.analyze_frame(
                    tracked_objects=tracked_objects,
                    frame_idx=processed_frames,
                    fps=input_fps,
                    frame_width=width,
                    frame_height=height,
                )

                # 3. Risk Engine evaluation
                frame_assessments = []
                for record in behavior_records:
                    assessment = self.risk_engine.evaluate_record(record)
                    frame_assessments.append(assessment)
                    all_assessments.append(assessment)

                    if assessment["risk_score"] > max_score:
                        max_score = assessment["risk_score"]

                    if assessment.get("alert_event"):
                        all_alerts.append(assessment["alert_event"])

                # 4. Render Phase 3 HUD
                annotated_frame = self.draw_phase3_hud(
                    frame, tracked_objects, frame_assessments
                )

                writer.write(annotated_frame)
                processed_frames += 1

                if processed_frames % 30 == 0 or processed_frames == total_frames:
                    elapsed = time.time() - start_time
                    fps_now = processed_frames / elapsed if elapsed > 0 else 0
                    pct = (processed_frames / total_frames * 100) if total_frames > 0 else 0
                    sys.stdout.write(
                        f"\rProgress: [{processed_frames}/{total_frames}] {pct:.1f}% | FPS: {fps_now:.2f}"
                    )
                    sys.stdout.flush()

        finally:
            cap.release()
            writer.release()
            print()

        total_elapsed = time.time() - start_time
        avg_fps = processed_frames / total_elapsed if total_elapsed > 0 else 0

        metrics = {
            "processed_frames": processed_frames,
            "max_risk_score": max_score,
            "total_assessments": len(all_assessments),
            "total_alerts": len(all_alerts),
            "alerts": all_alerts,
            "elapsed_seconds": total_elapsed,
            "processing_fps": avg_fps,
            "output_file": str(output_file),
            "sample_assessment": all_assessments[0] if all_assessments else None,
        }

        return metrics
