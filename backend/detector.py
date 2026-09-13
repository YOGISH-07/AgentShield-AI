import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np

try:
    from ultralytics import YOLO
except ImportError as e:
    raise ImportError(
        "Ultralytics package is not installed. Please run: pip install ultralytics"
    ) from e


class YOLODetector:
    """
    Computer Vision Object Detector using Ultralytics YOLO model.
    Designed specifically to detect 'person' and 'cell phone' in video frames.
    """

    # COCO Dataset Default Class IDs:
    # 0: person, 67: cell phone
    COCO_TARGET_CLASSES = {0: "person", 67: "cell phone"}

    def __init__(
        self,
        model_name_or_path: str = "yolov8n.pt",
        models_dir: str = "models",
        conf_threshold: float = 0.4,
        target_classes: List[int] = None,
    ):
        """
        Initialize the YOLO object detector.

        :param model_name_or_path: Weight file name or path (e.g., 'yolov8n.pt').
        :param models_dir: Path to directory storing model weights.
        :param conf_threshold: Minimum confidence score to accept detection.
        :param target_classes: List of COCO class IDs to detect. Defaults to [0, 67].
        """
        self.conf_threshold = conf_threshold
        self.target_classes = (
            target_classes if target_classes is not None else list(self.COCO_TARGET_CLASSES.keys())
        )

        # Resolve target model weight file path (e.g. models/yolov8n.pt)
        models_path = Path(models_dir)
        models_path.mkdir(parents=True, exist_ok=True)
        
        target_model_file = models_path / Path(model_name_or_path).name

        try:
            if target_model_file.exists():
                print(f"[YOLODetector] Loading model from local file: {target_model_file}")
                self.model = YOLO(str(target_model_file))
            else:
                print(f"[YOLODetector] Loading model weights '{model_name_or_path}'...")
                self.model = YOLO(model_name_or_path)
                # Save copy inside models directory for future offline runs
                try:
                    self.model.save(str(target_model_file))
                    print(f"[YOLODetector] Saved model weights to: {target_model_file}")
                except Exception:
                    pass
        except Exception as e:
            raise RuntimeError(
                f"Failed to load YOLO model weights. Error details: {e}"
            ) from e

    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Process a single image frame and return detected target objects.

        :param frame: BGR NumPy array (OpenCV frame).
        :return: List of dicts with keys: 'box', 'confidence', 'class_id', 'class_name'.
        """
        if frame is None or frame.size == 0:
            return []

        # Run inference (verbose=False keeps terminal output clean)
        results = self.model(frame, verbose=False, conf=self.conf_threshold)[0]

        detections = []
        if results.boxes is None or len(results.boxes) == 0:
            return detections

        for box in results.boxes:
            class_id = int(box.cls[0].item())
            
            # Filter strictly for target classes
            if class_id not in self.target_classes:
                continue

            conf = float(box.conf[0].item())
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

            # Use class name from COCO mapping or model names
            class_name = (
                self.COCO_TARGET_CLASSES.get(class_id)
                or self.model.names.get(class_id, f"class_{class_id}")
            )

            detections.append(
                {
                    "box": (x1, y1, x2, y2),
                    "confidence": conf,
                    "class_id": class_id,
                    "class_name": class_name,
                }
            )

        return detections
