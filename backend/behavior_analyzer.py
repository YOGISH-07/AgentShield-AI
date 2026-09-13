import math
from typing import List, Dict, Any, Tuple, Optional
import numpy as np


class BehaviorAnalyzer:
    """
    Behavior Analyzer for CineGuard AI.
    Extracts spatial relationships, movement vectors, screen region alignment,
    and temporal persistence for tracked persons and mobile phones.
    """

    # Configurable Cinema Screen Region in normalized coordinates (0.0 to 1.0)
    DEFAULT_SCREEN_REGION = {
        "x1": 0.20,
        "y1": 0.10,
        "x2": 0.80,
        "y2": 0.60,
    }

    def __init__(
        self,
        screen_region: Optional[Dict[str, float]] = None,
        proximity_threshold_px: float = 180.0,
    ):
        """
        Initialize Behavior Analyzer.

        :param screen_region: Normalized dict with keys 'x1', 'y1', 'x2', 'y2'.
        :param proximity_threshold_px: Maximum distance in pixels to associate phone with person.
        """
        self.screen_region = (
            screen_region if screen_region is not None else self.DEFAULT_SCREEN_REGION.copy()
        )
        self.proximity_threshold_px = proximity_threshold_px

        # Temporal tracking history across frames
        # Maps phone_track_id -> list of (frame_idx, timestamp_sec, center_x, center_y)
        self._phone_trajectories: Dict[int, List[Tuple[int, float, int, int]]] = {}
        
        # Maps (person_track_id, phone_track_id) -> start_frame_idx
        self._association_start_frame: Dict[Tuple[int, int], int] = {}
        
        # Maps phone_track_id -> first_seen_frame_idx
        self._phone_first_seen_frame: Dict[int, int] = {}

    def set_screen_region(self, x1: float, y1: float, x2: float, y2: float):
        """Update cinema screen region normalized coordinates."""
        self.screen_region = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}

    def get_screen_region_pixels(self, frame_width: int, frame_height: int) -> Tuple[int, int, int, int]:
        """Convert normalized screen region coordinates to pixel values."""
        rx1 = int(self.screen_region["x1"] * frame_width)
        ry1 = int(self.screen_region["y1"] * frame_height)
        rx2 = int(self.screen_region["x2"] * frame_width)
        ry2 = int(self.screen_region["y2"] * frame_height)
        return rx1, ry1, rx2, ry2

    @staticmethod
    def _euclidean_distance(pt1: Tuple[float, float], pt2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two 2D points."""
        return math.hypot(pt1[0] - pt2[0], pt1[1] - pt2[1])

    def _is_in_screen_region(
        self, cx: int, cy: int, frame_width: int, frame_height: int
    ) -> bool:
        """Check if pixel coordinates fall within the cinema screen region."""
        rx1, ry1, rx2, ry2 = self.get_screen_region_pixels(frame_width, frame_height)
        return rx1 <= cx <= rx2 and ry1 <= cy <= ry2

    def _distance_to_screen_region(
        self, cx: int, cy: int, frame_width: int, frame_height: int
    ) -> float:
        """
        Calculate normalized distance from a point to the nearest boundary of the screen region.
        Returns 0.0 if the point is inside the screen region.
        """
        rx1, ry1, rx2, ry2 = self.get_screen_region_pixels(frame_width, frame_height)

        dx = max(rx1 - cx, 0, cx - rx2)
        dy = max(ry1 - cy, 0, cy - ry2)

        pixel_dist = math.hypot(dx, dy)
        # Normalize distance relative to frame diagonal
        frame_diag = math.hypot(frame_width, frame_height)
        return float(pixel_dist / frame_diag) if frame_diag > 0 else 0.0

    def _is_moving_toward_screen_region(
        self, phone_id: int, frame_width: int, frame_height: int
    ) -> bool:
        """
        Calculate whether the phone's recent movement vector is directed toward the screen region center.
        """
        traj = self._phone_trajectories.get(phone_id, [])
        if len(traj) < 3:
            return False

        # Compute movement vector over last few frames
        prev_pos = traj[-3][2:]
        curr_pos = traj[-1][2:]

        move_dx = curr_pos[0] - prev_pos[0]
        move_dy = curr_pos[1] - prev_pos[1]
        move_mag = math.hypot(move_dx, move_dy)

        if move_mag < 2.0:  # Negligible movement
            return False

        # Screen region center
        rx1, ry1, rx2, ry2 = self.get_screen_region_pixels(frame_width, frame_height)
        scx, scy = (rx1 + rx2) / 2.0, (ry1 + ry2) / 2.0

        # Vector towards screen center from current position
        target_dx = scx - curr_pos[0]
        target_dy = scy - curr_pos[1]
        target_mag = math.hypot(target_dx, target_dy)

        if target_mag == 0:
            return True

        # Dot product to check alignment
        dot_product = (move_dx * target_dx + move_dy * target_dy) / (move_mag * target_mag)
        return dot_product > 0.3  # Positive alignment towards screen region

    def analyze_frame(
        self,
        tracked_objects: List[Dict[str, Any]],
        frame_idx: int,
        fps: float,
        frame_width: int,
        frame_height: int,
    ) -> List[Dict[str, Any]]:
        """
        Analyze tracked objects in the current frame and extract behavioral signals.

        :param tracked_objects: List of tracked object dicts from ObjectTracker.
        :param frame_idx: Current frame index (0-indexed).
        :param fps: Video frame rate (FPS).
        :param frame_width: Frame width in pixels.
        :param frame_height: Frame height in pixels.
        :return: List of structured behavior signal dictionaries.
        """
        if fps <= 0:
            fps = 30.0

        timestamp_sec = frame_idx / fps

        # Separate tracked persons and tracked phones
        persons = [obj for obj in tracked_objects if obj["class_name"] == "person"]
        phones = [obj for obj in tracked_objects if obj["class_name"] == "cell phone"]

        behavior_results = []

        # Update phone trajectory history
        for phone in phones:
            p_id = phone["track_id"]
            cx, cy = phone["center"]

            if p_id not in self._phone_first_seen_frame:
                self._phone_first_seen_frame[p_id] = frame_idx

            if p_id not in self._phone_trajectories:
                self._phone_trajectories[p_id] = []

            self._phone_trajectories[p_id].append((frame_idx, timestamp_sec, cx, cy))
            # Keep history buffer bounded
            if len(self._phone_trajectories[p_id]) > 60:
                self._phone_trajectories[p_id].pop(0)

        # Process each detected phone
        for phone in phones:
            phone_id = phone["track_id"]
            pcx, pcy = phone["center"]

            # Calculate phone total visible duration
            first_frame = self._phone_first_seen_frame[phone_id]
            time_phone_visible_sec = (frame_idx - first_frame + 1) / fps

            # Calculate recent movement magnitude (pixels per second over last 5 frames)
            traj = self._phone_trajectories.get(phone_id, [])
            phone_movement = 0.0
            if len(traj) >= 2:
                last_pos = traj[-1]
                prev_pos = traj[max(0, len(traj) - 5)]
                dist_px = self._euclidean_distance((last_pos[2], last_pos[3]), (prev_pos[2], prev_pos[3]))
                time_diff = max(0.01, last_pos[1] - prev_pos[1])
                phone_movement = dist_px / time_diff  # Speed in px/s

            # Screen region analysis
            in_screen = self._is_in_screen_region(pcx, pcy, frame_width, frame_height)
            dist_to_screen = self._distance_to_screen_region(pcx, pcy, frame_width, frame_height)
            moving_toward_screen = self._is_moving_toward_screen_region(phone_id, frame_width, frame_height)

            # Find nearest person (if any) to evaluate person <-> phone association
            associated_person = None
            min_dist = float("inf")

            for person in persons:
                person_id = person["track_id"]
                px1, py1, px2, py2 = person["box"]
                
                # Distance from phone center to person bounding box center or bounds
                person_cx, person_cy = person["center"]
                dist = self._euclidean_distance((pcx, pcy), (person_cx, person_cy))

                if dist < min_dist and dist <= self.proximity_threshold_px:
                    min_dist = dist
                    associated_person = person

            person_near = associated_person is not None
            person_track_id = associated_person["track_id"] if associated_person else None

            # Calculate relationship persistence (association duration)
            duration_seconds = 0.0
            if person_track_id is not None:
                assoc_key = (person_track_id, phone_id)
                if assoc_key not in self._association_start_frame:
                    self._association_start_frame[assoc_key] = frame_idx
                
                start_f = self._association_start_frame[assoc_key]
                duration_seconds = (frame_idx - start_f + 1) / fps
            
            # Construct structured behavior result
            behavior_record = {
                "frame_idx": frame_idx,
                "timestamp_seconds": round(timestamp_sec, 2),
                "phone_track_id": phone_id,
                "person_track_id": person_track_id,
                "phone_detected": True,
                "person_detected": len(persons) > 0,
                "phone_near_person": person_near,
                "phone_position": {
                    "pixel": [pcx, pcy],
                    "normalized": [round(pcx / frame_width, 3), round(pcy / frame_height, 3)],
                },
                "phone_movement_speed_px_s": round(phone_movement, 2),
                "phone_in_screen_region": in_screen,
                "phone_distance_to_screen_region": round(dist_to_screen, 4),
                "phone_moving_toward_screen_region": moving_toward_screen,
                "time_phone_visible_seconds": round(time_phone_visible_sec, 2),
                "duration_seconds": round(duration_seconds, 2),
            }

            behavior_results.append(behavior_record)

        return behavior_results
