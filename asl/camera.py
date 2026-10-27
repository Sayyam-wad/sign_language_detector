"""Camera helpers shared by the app, the collector and the doctor check."""

from __future__ import annotations

import sys
import time

from asl import config


def open_camera(index: int = config.CAMERA_INDEX, width: int = config.FRAME_WIDTH, height: int = config.FRAME_HEIGHT):
    """Open a camera and make sure it actually returns frames."""
    import cv2
    # DirectShow opens much faster on Windows; other platforms use the default backend.
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW) if sys.platform == "win32" else cv2.VideoCapture(index)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera {index}. Run `python -m asl.doctor` to list working cameras, "
                           "then set ASL_CAMERA_INDEX.")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    for _ in range(5):
        ok, frame = cap.read()
        if ok and frame is not None and frame.size:
            return cap
        time.sleep(0.5)
    cap.release()
    raise RuntimeError(f"Camera {index} opened but returns no frames (is another app using it?).")


def read_frame(cap, mirror: bool = config.MIRROR):
    import cv2
    ok, frame = cap.read()
    if not ok or frame is None or not frame.size:
        return None
    return cv2.flip(frame, 1) if mirror else frame
