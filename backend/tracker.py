import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np

try:
    from ultralytics import YOLO
except ImportError as e:
    raise ImportError(
        "Ultralytics package is required. Please install via: pip install ultralytics"
    ) from e


class ObjectTracker:
    """
    Multi-Object Tracker using Ultralytics YOLO tracking engine (ByteTrack / BoT-SORT).
    Assigns anonymous persistent Track IDs across video frames for 'person' and 'cell phone'.
    """

    COCO_TARGET_CLASSES = {0: "person", 67: "cell phone"}

    def __init__(
        self,
        model_name_or_path: str = "yolov8n.pt",
        models_dir: str = "models",
        conf_threshold: float = 0.4,
        tracker_type: str = "bytetrack.yaml",
        target_classes: List[int] = None,
    ):
        """
        Initialize Object Tracker.

        :param model_name_or_path: YOLO model weights filename or path.
        :param models_dir: Directory to cache model weights.
        :param conf_threshold: Minimum confidence threshold.
        :param tracker_type: Tracker configuration file ('bytetrack.yaml' or 'botsort.yaml').
        :param target_classes: List of COCO class IDs to track. Defaults to [0, 67].
        """
        self.conf_threshold = conf_threshold
        self.tracker_type = tracker_type
        self.target_classes = (
            target_classes if target_classes is not None else list(self.COCO_TARGET_CLASSES.keys())
        )

        models_path = Path(models_dir)
        models_path.mkdir(parents=True, exist_ok=True)
        target_model_file = models_path / Path(model_name_or_path).name

        try:
            if target_model_file.exists():
                print(f"[ObjectTracker] Loading model from local file: {target_model_file}")
                self.model = YOLO(str(target_model_file))
            else:
                print(f"[ObjectTracker] Loading model weights '{model_name_or_path}'...")
                self.model = YOLO(model_name_or_path)
                try:
                    self.model.save(str(target_model_file))
                    print(f"[ObjectTracker] Saved model weights to: {target_model_file}")
                except Exception:
                    pass
        except Exception as e:
            raise RuntimeError(
                f"Failed to load YOLO model for tracker: {e}"
            ) from e

        # Fallback tracker counter if track IDs are missing in early frames
        self._fallback_id_counters = {"person": 1, "cell phone": 1}

    def reset_tracker(self):
        """Reset internal tracking state for a new video stream."""
        self._fallback_id_counters = {"person": 1, "cell phone": 1}

    def track_frame(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Process a video frame and track target objects across frames.

        :param frame: OpenCV BGR NumPy image array.
        :return: List of tracked object dictionaries with anonymous track IDs.
        """
        if frame is None or frame.size == 0:
            return []

        # Run YOLO multi-object tracking (persist=True retains IDs across calls)
        try:
            results = self.model.track(
                frame,
                persist=True,
                tracker=self.tracker_type,
                conf=self.conf_threshold,
                verbose=False,
            )[0]
        except Exception:
            # Fallback to standard detect if tracker config fails
            results = self.model(frame, conf=self.conf_threshold, verbose=False)[0]

        tracked_objects = []
        if results.boxes is None or len(results.boxes) == 0:
            return tracked_objects

        # Extract track IDs from results if available
        has_track_ids = results.boxes.id is not None
        track_ids = (
            results.boxes.id.int().cpu().tolist() if has_track_ids else []
        )

        for i, box in enumerate(results.boxes):
            class_id = int(box.cls[0].item())

            # Filter for person (0) and cell phone (67)
            if class_id not in self.target_classes:
                continue

            conf = float(box.conf[0].item())
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)

            class_name = (
                self.COCO_TARGET_CLASSES.get(class_id)
                or self.model.names.get(class_id, f"class_{class_id}")
            )

            # Assign track ID (from YOLO tracker or deterministic fallback)
            if has_track_ids and i < len(track_ids) and track_ids[i] is not None:
                raw_track_id = int(track_ids[i])
            else:
                raw_track_id = self._fallback_id_counters[class_name]
                self._fallback_id_counters[class_name] += 1

            # Format anonymous user-facing label (e.g. Person #3, Phone #7)
            if class_name == "person":
                display_label = f"Person #{raw_track_id}"
            elif class_name == "cell phone":
                display_label = f"Phone #{raw_track_id}"
            else:
                display_label = f"{class_name.capitalize()} #{raw_track_id}"

            tracked_objects.append(
                {
                    "track_id": raw_track_id,
                    "display_id": display_label,
                    "class_id": class_id,
                    "class_name": class_name,
                    "box": (x1, y1, x2, y2),
                    "center": (cx, cy),
                    "confidence": conf,
                }
            )

        return tracked_objects
