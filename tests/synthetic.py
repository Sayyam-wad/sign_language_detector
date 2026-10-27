"""Procedural hand landmarks for tests (no camera, images or MediaPipe needed).

Each synthetic "sign" is a fixed set of finger curls plus a hand orientation;
samples add pose noise, random scale, position and handedness.
"""

from __future__ import annotations

import numpy as np

# Bone lengths (palm-length units) per finger: base->j1, j1->j2, j2->tip
_BONES = {
    "thumb": (0.45, 0.35, 0.3), "index": (0.45, 0.28, 0.22), "middle": (0.5, 0.3, 0.24),
    "ring": (0.47, 0.28, 0.22), "pinky": (0.36, 0.22, 0.2),
}
# Knuckle (MCP) positions relative to the wrist for a right hand, fingers pointing up (-y).
_BASES = {"thumb": (-0.35, -0.3), "index": (-0.25, -0.95), "middle": (0.0, -1.0),
          "ring": (0.22, -0.95), "pinky": (0.42, -0.85)}
_ORDER = ["thumb", "index", "middle", "ring", "pinky"]


def hand_points(curls, rotation=0.0, scale=100.0, offset=(320.0, 240.0), left=False, rng=None, noise=0.0):
    """21x3 landmarks in pixel units. curls: 5 values in [0, 1] (0 straight, 1 fully bent)."""
    rng = rng or np.random.default_rng(0)
    pts = np.zeros((21, 3))
    for f, name in enumerate(_ORDER):
        bx, by = _BASES[name]
        base = np.array([bx, by, 0.0])
        idx = 1 + 4 * f
        pts[idx] = base
        direction = np.array([-0.6, -0.8, 0]) if name == "thumb" else np.array([0, -1.0, 0])
        pos, angle = base, 0.0
        for k, length in enumerate(_BONES[name]):
            angle += curls[f] * (1.2 if k else 0.9)
            c, s = np.cos(angle), np.sin(angle)
            d = np.array([direction[0], direction[1] * c, -abs(direction[1]) * s])
            pos = pos + length * d / np.linalg.norm(d)
            pts[idx + k + 1] = pos
    if left:
        pts[:, 0] = -pts[:, 0]
    c, s = np.cos(rotation), np.sin(rotation)
    rot = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    pts = pts @ rot.T
    pts += rng.normal(0, noise, pts.shape)
    pts *= scale
    pts[:, :2] += offset
    return pts


def make_dataset(n_classes=8, per_group=12, n_groups=5, seed=0):
    """Returns X, y, groups like asl.dataset produces (class ids taken from real labels)."""
    from asl.features import landmark_features
    from asl.labels import CLASSES
    rng = np.random.default_rng(seed)
    class_ids = list(CLASSES)[:n_classes]
    protos = {c: (rng.uniform(0, 1, 5), rng.uniform(-0.4, 0.4)) for c in class_ids}
    X, y, groups = [], [], []
    for g in range(n_groups):
        for c in class_ids:
            curls, rot = protos[c]
            for _ in range(per_group):
                left = rng.random() < 0.3
                pts = hand_points(np.clip(curls + rng.normal(0, 0.05, 5), 0, 1), rot + rng.normal(0, 0.05),
                                  scale=rng.uniform(60, 160), offset=rng.uniform(100, 400, 2), left=left,
                                  rng=rng, noise=0.01)
                X.append(landmark_features(pts, "Left" if left else "Right"))
                y.append(c)
                groups.append(f"block:{g}")
    return np.array(X), np.array(y), np.array(groups)
