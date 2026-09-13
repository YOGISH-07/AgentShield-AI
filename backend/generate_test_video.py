import os
import sys
import urllib.request
from pathlib import Path
import cv2
import numpy as np


def create_sample_video(output_path: str = "videos/input.mp4", num_frames: int = 90, fps: float = 30.0):
    """
    Generate a 3-second realistic test video containing a person holding a cell phone,
    panning across frames inside the cinema screen region for CineGuard AI verification.
    """
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    sample_img_path = out_file.parent / "phone_person_sample.jpg"

    # Download sample image if not present locally
    if not sample_img_path.exists():
        print("Downloading sample test frame containing person & smartphone...")
        url = "https://images.pexels.com/photos/1092671/pexels-photo-1092671.jpeg?auto=compress&cs=tinysrgb&w=640"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=10).read()
            with open(sample_img_path, "wb") as f:
                f.write(data)
        except Exception as e:
            print(f"Warning: Could not download sample photo ({e}). Generating synthetic fallback frame.")

    # Read base image if available, else generate synthetic base image
    base_img = cv2.imread(str(sample_img_path)) if sample_img_path.exists() else None

    width, height = 640, 480
    if base_img is not None:
        base_img = cv2.resize(base_img, (width, height))

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(out_file), fourcc, fps, (width, height))

    if not writer.isOpened():
        print(f"Error: Could not open VideoWriter for {output_path}")
        return False

    print(f"Generating realistic test video at '{output_path}' ({num_frames} frames @ {fps} FPS)...")

    for i in range(num_frames):
        if base_img is not None:
            # Slight dynamic panning movement across frames to simulate camera motion / tracking
            shift_x = int(10 * np.sin(i / 10.0))
            shift_y = int(5 * np.cos(i / 10.0))
            
            M = np.float32([[1, 0, shift_x], [0, 1, shift_y]])
            frame = cv2.warpAffine(base_img, M, (width, height))
        else:
            # Fallback frame
            frame = np.full((height, width, 3), (40, 40, 50), dtype=np.uint8)

        writer.write(frame)

    writer.release()
    print(f"Test video generated successfully: '{output_path}'")
    return True


if __name__ == "__main__":
    root_dir = Path(__file__).resolve().parent.parent
    target_path = root_dir / "videos" / "input.mp4"
    create_sample_video(str(target_path))
