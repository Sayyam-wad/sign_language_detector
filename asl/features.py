"""Hand-shape features from 21 MediaPipe landmarks.

Version 2 (this file) vs. the original 42 distances:

* Pixel-aspect coordinates: MediaPipe x/y are fractions of width and height, so
  on a 640x480 frame a distance along x was worth 33% more than the same
  distance along y. Landmarks are converted to x*W, y*H first.
* Scale normalisation: everything is divided by the palm length (wrist to
  middle-finger knuckle), so moving the hand closer to the camera no longer
  changes the features. The README claimed this before; the code didn't do it.
* Handedness normalisation: left hands are mirrored onto right-hand geometry.
* Orientation is kept on purpose (unlike pure distances): ASL pairs like H/U,
  K/P and G/Q share a shape and differ mainly in which way the hand points.

Groups (85 features): 20 wrist-relative xyz coordinates (60), 15 finger joint
angles, 10 fingertip-to-fingertip distances.
"""

from __future__ import annotations

import numpy as np

FEATURE_VERSION = 2

WRIST = 0
FINGERS = {  # MCP/CMC, PIP/MCP, DIP/IP, TIP
    "thumb": (1, 2, 3, 4),
    "index": (5, 6, 7, 8),
    "middle": (9, 10, 11, 12),
    "ring": (13, 14, 15, 16),
    "pinky": (17, 18, 19, 20),
}
TIPS = (4, 8, 12, 16, 20)
_TIP_PAIRS = [(a, b) for i, a in enumerate(TIPS) for b in TIPS[i + 1:]]


def _feature_names() -> list[str]:
    names = [f"lm{i}_{ax}" for i in range(1, 21) for ax in "xyz"]
    for finger in FINGERS:
        names += [f"{finger}_angle{j}" for j in range(3)]
    names += [f"tipdist_{a}_{b}" for a, b in _TIP_PAIRS]
    return names


FEATURE_NAMES = _feature_names()
N_FEATURES = len(FEATURE_NAMES)


def normalize_landmarks(points: np.ndarray, handedness: str = "Right") -> np.ndarray:
    """Wrist at origin, palm length 1, left hands mirrored. Input/output shape (21, 3)."""
    p = np.asarray(points, dtype=np.float64).copy()
    if p.shape != (21, 3):
        raise ValueError(f"expected (21, 3) landmarks, got {p.shape}")
    if handedness == "Left":
        p[:, 0] = -p[:, 0]
    p -= p[WRIST]
    palm = np.linalg.norm(p[9, :2])
    if palm < 1e-6:  # degenerate detection; fall back to overall hand size
        palm = np.linalg.norm(p[:, :2], axis=1).max() or 1.0
    return p / palm


def _angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Angle at b (radians) between segments b->a and b->c."""
    v1, v2 = a - b, c - b
    cos = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9)
    return float(np.arccos(np.clip(cos, -1.0, 1.0)))


def landmark_features(points: np.ndarray, handedness: str = "Right") -> np.ndarray:
    p = normalize_landmarks(points, handedness)
    coords = p[1:].ravel()
    angles = []
    for base, j1, j2, tip in FINGERS.values():
        chain = [WRIST, base, j1, j2, tip]
        angles += [_angle(p[chain[k - 1]], p[chain[k]], p[chain[k + 1]]) for k in (1, 2, 3)]
    tip_d = [np.linalg.norm(p[a, :2] - p[b, :2]) for a, b in _TIP_PAIRS]
    return np.concatenate([coords, angles, tip_d]).astype(np.float32)
