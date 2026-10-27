"""Landmark-space data augmentation.

Rotating the 21 landmarks by a small random angle creates realistic "tilted
wrist" variants of each training sample for free (no new images). The angle
range is kept well below the 90° that separates pairs such as H and U, so the
orientation cue the features rely on is preserved.
"""

from __future__ import annotations

import numpy as np

from asl.features import landmark_features


def rotate_landmarks(points: np.ndarray, degrees: float) -> np.ndarray:
    """Rotate in the image plane around the hand's centre (x, y only)."""
    a = np.radians(degrees)
    r = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    out = np.asarray(points, dtype=np.float64).copy()
    c = out[:, :2].mean(axis=0)
    out[:, :2] = (out[:, :2] - c) @ r.T + c
    return out


def augment(landmarks: np.ndarray, handedness: np.ndarray, y: np.ndarray, copies: int = 2,
            max_degrees: float = 25.0, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Return extra (features, labels) made from rotated copies of each sample."""
    rng = np.random.default_rng(seed)
    X, Y = [], []
    for pts, hand, label in zip(landmarks, handedness, y):
        for _ in range(copies):
            X.append(landmark_features(rotate_landmarks(pts, rng.uniform(-max_degrees, max_degrees)), str(hand)))
            Y.append(label)
    return np.asarray(X, dtype=np.float32), np.asarray(Y)
