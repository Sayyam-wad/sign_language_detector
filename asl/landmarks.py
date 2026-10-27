"""MediaPipe hand detection, isolated behind one small class.

MediaPipe 0.10.30+ removed the legacy `mp.solutions` API that this project
uses, so an unpinned `pip install mediapipe` used to crash every script with
an AttributeError. requirements.txt pins a compatible version, and this module
fails with a clear message instead.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from asl import config


@dataclass
class Hand:
    points: np.ndarray        # (21, 3) landmarks in pixel-aspect units (x*W, y*H, z*W)
    handedness: str           # "Left" or "Right" as reported by MediaPipe
    score: float              # handedness confidence
    raw: object = None        # original MediaPipe landmarks, for drawing

    def bbox(self) -> tuple[int, int, int, int]:
        xs, ys = self.points[:, 0], self.points[:, 1]
        return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def _mediapipe_hands():
    try:
        import mediapipe as mp
    except ImportError as e:  # pragma: no cover
        raise ImportError("mediapipe is not installed: pip install -r requirements.txt") from e
    if not hasattr(mp, "solutions"):
        raise ImportError(
            f"mediapipe {mp.__version__} no longer ships the `solutions` API used here. "
            "Install a compatible version: pip install \"mediapipe>=0.10.9,<0.10.30\" "
            "(Python 3.9-3.12).")
    return mp.solutions


class HandDetector:
    """Detect a single hand.

    static_image_mode=True treats every image independently (use it for photo
    datasets: with False, MediaPipe's tracker carries state between unrelated
    images). Use False for live video.
    """

    def __init__(self, static_image_mode: bool, min_detection_confidence: float = config.DETECTION_CONFIDENCE,
                 min_tracking_confidence: float = config.TRACKING_CONFIDENCE):
        solutions = _mediapipe_hands()
        self._solutions = solutions
        self._hands = solutions.hands.Hands(
            static_image_mode=static_image_mode,
            max_num_hands=1,
            model_complexity=1,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

    def detect(self, image_bgr: np.ndarray) -> Hand | None:
        import cv2
        h, w = image_bgr.shape[:2]
        result = self._hands.process(cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB))
        if not result.multi_hand_landmarks:
            return None
        lms = result.multi_hand_landmarks[0]
        cls = result.multi_handedness[0].classification[0]
        pts = np.array([[p.x * w, p.y * h, p.z * w] for p in lms.landmark], dtype=np.float32)
        return Hand(pts, cls.label, float(cls.score), lms)

    def draw(self, image_bgr: np.ndarray, hand: Hand) -> None:
        s = self._solutions
        s.drawing_utils.draw_landmarks(
            image_bgr, hand.raw, s.hands.HAND_CONNECTIONS,
            s.drawing_styles.get_default_hand_landmarks_style(),
            s.drawing_styles.get_default_hand_connections_style())

    def close(self) -> None:
        self._hands.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
