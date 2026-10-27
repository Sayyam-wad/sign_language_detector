"""Sign atlas: one representative hand skeleton per sign.

    python -m asl.atlas [--features artifacts/features.npz]

For each class we pick the *medoid* training sample (the real sample closest to
all others in feature space, so it's an actual pose rather than a blurred
average) and store its normalised landmarks in asl/assets/atlas.json. The
text-to-sign viewer and the browser demo draw these skeletons instead of
showing dataset photos, so no faces are shown and no dataset is needed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from asl import config
from asl.features import normalize_landmarks
from asl.labels import name_of

ATLAS_PATH = Path(__file__).resolve().parent / "assets" / "atlas.json"

# MediaPipe's hand topology (pairs of landmark indices).
CONNECTIONS = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8), (5, 9), (9, 10), (10, 11),
               (11, 12), (9, 13), (13, 14), (14, 15), (15, 16), (13, 17), (0, 17), (17, 18), (18, 19), (19, 20)]
FINGER_COLORS = {  # BGR, one colour per finger (thumb..pinky), palm grey
    "thumb": (80, 180, 255), "index": (90, 220, 120), "middle": (255, 200, 80),
    "ring": (230, 120, 220), "pinky": (120, 120, 255), "palm": (170, 170, 170)}


def _finger(a: int, b: int) -> str:
    if (a, b) in [(0, 5), (5, 9), (9, 13), (13, 17), (0, 17)]:
        return "palm"
    return ["thumb", "index", "middle", "ring", "pinky"][(max(a, b) - 1) // 4]


def build(features_path: Path = config.FEATURES_PATH, out: Path = ATLAS_PATH) -> dict:
    d = np.load(features_path)
    if "landmarks" not in d.files:
        raise SystemExit("Feature file has no landmarks; rebuild it with `python -m asl.dataset`.")
    X, y, pts, hands = d["X"], d["y"].astype(int), d["landmarks"], d["handedness"]
    Xs = (X - X.mean(0)) / (X.std(0) + 1e-9)
    atlas = {}
    for cid in sorted(set(y)):
        idx = np.flatnonzero(y == cid)
        sub = Xs[idx]
        medoid = idx[np.argmin(((sub[:, None, :] - sub[None, :, :]) ** 2).sum(-1).sum(1))]
        p = normalize_landmarks(pts[medoid], str(hands[medoid]))
        atlas[name_of(cid)] = np.round(p, 3).tolist()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(atlas, separators=(",", ":")))
    print(f"Saved {len(atlas)} signs to {out}")
    return atlas


def load(path: Path = ATLAS_PATH) -> dict[str, np.ndarray]:
    if not path.exists():
        return {}
    return {k: np.asarray(v, dtype=np.float32) for k, v in json.loads(path.read_text()).items()}


def render(points: np.ndarray, size: int = 160, label: str | None = None, background=(30, 30, 30)) -> np.ndarray:
    """Draw a normalised skeleton (wrist at origin, palm length 1) into a square BGR image."""
    import cv2
    img = np.full((size, size, 3), background, np.uint8)
    xy = np.asarray(points)[:, :2]
    lo, hi = xy.min(0), xy.max(0)
    scale = (size * 0.78) / max(hi[0] - lo[0], hi[1] - lo[1], 1e-6)
    centre = (lo + hi) / 2
    px = ((xy - centre) * scale + size / 2).astype(int)
    if label:  # leave room for the caption
        px[:, 1] += int(size * 0.06)
    lw = max(2, size // 50)
    for a, b in CONNECTIONS:
        cv2.line(img, tuple(px[a]), tuple(px[b]), FINGER_COLORS[_finger(a, b)], lw, cv2.LINE_AA)
    for i, (x, yy) in enumerate(px):
        cv2.circle(img, (x, yy), lw + (1 if i in (4, 8, 12, 16, 20) else 0), (245, 245, 245), -1, cv2.LINE_AA)
    if label:
        cv2.putText(img, label[:12], (6, int(size * 0.11)), cv2.FONT_HERSHEY_SIMPLEX, size / 330, (0, 230, 255), 1,
                    cv2.LINE_AA)
    return img


def sheet(atlas: dict[str, np.ndarray], names: list[str], cols: int = 9, size: int = 120) -> np.ndarray:
    tiles = [render(atlas[n], size, n) for n in names if n in atlas]
    rows = []
    for r in range(0, len(tiles), cols):
        row = tiles[r:r + cols]
        row += [np.full_like(tiles[0], 30)] * (cols - len(row))
        rows.append(np.hstack(row))
    return np.vstack(rows)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--features", type=Path, default=config.FEATURES_PATH)
    p.add_argument("--sheet", type=Path, default=None, help="also save a PNG contact sheet of every sign")
    a = p.parse_args(argv)
    atlas = build(a.features)
    if a.sheet:
        import cv2

        from asl.labels import LETTERS, PHRASES
        cv2.imwrite(str(a.sheet), sheet({k: np.asarray(v) for k, v in atlas.items()}, LETTERS + PHRASES))
        print(f"Saved {a.sheet}")


if __name__ == "__main__":
    main()
