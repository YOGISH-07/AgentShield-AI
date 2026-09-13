import os
import sys
import urllib.request
from pathlib import Path
import cv2
import numpy as np


def create_demo_scenario_video(
    output_path: str = "videos/demo_cinema.mp4",
    total_duration_sec: float = 25.0,
    fps: float = 30.0,
):
    """
    Generate a 25-second (750 frames @ 30 FPS) demonstration scenario video
    implementing 4 realistic computer-vision test scenes for CineGuard AI evaluation.

    SCENE 1 (0.0s - 5.0s): NORMAL - Person only (no phone)
    SCENE 2 (5.0s - 10.0s): PHONE APPEARS - Person holding phone outside screen region
    SCENE 3 (10.0s - 20.0s): SUSTAINED SCREEN BEHAVIOR - Phone held inside screen region
    SCENE 4 (20.0s - 25.0s): BEHAVIOR ENDS - Phone removed / return to normal
    """
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    # 1. Image with person + phone
    sample_phone_path = out_file.parent / "phone_person_sample.jpg"
    if not sample_phone_path.exists():
        print("Downloading sample frame containing person & smartphone...")
        url = "https://images.pexels.com/photos/1092671/pexels-photo-1092671.jpeg?auto=compress&cs=tinysrgb&w=640"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=10).read()
            with open(sample_phone_path, "wb") as f:
                f.write(data)
        except Exception as e:
            print(f"Warning: Could not download sample photo ({e})")

    # 2. Image with person only (from Ultralytics bus.jpg / zidane.jpg assets)
    import ultralytics
    assets_dir = Path(ultralytics.__file__).parent / "assets"
    bus_path = assets_dir / "bus.jpg"

    width, height = 640, 480

    phone_sample = cv2.imread(str(sample_phone_path)) if sample_phone_path.exists() else None
    if phone_sample is not None:
        phone_sample = cv2.resize(phone_sample, (width, height))

    person_only_sample = cv2.imread(str(bus_path)) if bus_path.exists() else None
    if person_only_sample is not None:
        person_only_sample = cv2.resize(person_only_sample, (width, height))
    else:
        person_only_sample = np.full((height, width, 3), (40, 40, 50), dtype=np.uint8)

    total_frames = int(total_duration_sec * fps)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(out_file), fourcc, fps, (width, height))

    if not writer.isOpened():
        raise RuntimeError(f"Could not open VideoWriter for path: {output_path}")

    print(f"\n==================================================")
    print(f"   CINEGUARD AI - DEMO SCENARIO VIDEO GENERATOR   ")
    print(f"==================================================")
    print(f"Target Output : {output_path}")
    print(f"Duration      : {total_duration_sec:.1f} seconds ({total_frames} frames @ {fps} FPS)")
    print(f"Scene 1 (0-5s): SCENE 1 — NORMAL (Person only)")
    print(f"Scene 2 (5-10s): SCENE 2 — PHONE APPEARS (Outside Screen Region)")
    print(f"Scene 3 (10-20s): SCENE 3 — SUSTAINED SCREEN BEHAVIOR (Inside Screen Region)")
    print(f"Scene 4 (20-25s): SCENE 4 — BEHAVIOR ENDS (Phone removed)")
    print(f"--------------------------------------------------")

    for frame_idx in range(total_frames):
        timestamp = frame_idx / fps

        # SCENE 1: NORMAL (0.0s - 5.0s, frames 0-150) -> Person only (no phone)
        if timestamp < 5.0:
            shift_x = int(3 * np.sin(frame_idx / 15.0))
            M = np.float32([[1, 0, shift_x], [0, 1, 0]])
            frame = cv2.warpAffine(person_only_sample, M, (width, height))

        # SCENE 2: PHONE APPEARS (5.0s - 10.0s, frames 150-300) -> Phone outside cinema screen region (shifted left)
        elif timestamp < 10.0:
            M = np.float32([[1, 0, -110], [0, 1, 60]])
            frame = cv2.warpAffine(phone_sample, M, (width, height), borderValue=(40, 40, 50))

        # SCENE 3: SUSTAINED SCREEN BEHAVIOR (10.0s - 20.0s, frames 300-600) -> Phone inside screen region
        elif timestamp < 20.0:
            shift_x = int(5 * np.sin(frame_idx / 15.0))
            shift_y = int(3 * np.cos(frame_idx / 15.0))
            M = np.float32([[1, 0, shift_x], [0, 1, shift_y]])
            frame = cv2.warpAffine(phone_sample, M, (width, height))

        # SCENE 4: BEHAVIOR ENDS (20.0s - 25.0s, frames 600-750) -> Phone removed, return to normal posture
        else:
            shift_x = int(3 * np.sin(frame_idx / 15.0))
            M = np.float32([[1, 0, shift_x], [0, 1, 0]])
            frame = cv2.warpAffine(person_only_sample, M, (width, height))

        writer.write(frame)

    writer.release()
    print(f"Synthetic demo test video generated successfully: '{output_path}'\n")
    return True


if __name__ == "__main__":
    root_dir = Path(__file__).resolve().parent.parent
    target_path = root_dir / "videos" / "demo_cinema.mp4"
    create_demo_scenario_video(str(target_path))
