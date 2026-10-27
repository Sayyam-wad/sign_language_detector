"""Turn the image dataset into a feature matrix.

    python -m asl.dataset [--data-dir data] [--block-size 20]

Layout: data/<class_id>/<image>.jpg (the original layout, unchanged).

Every image also gets a *group* used for leakage-free evaluation:
  * images saved by `asl.collect` are named <session>_<n>.jpg -> group = session
  * older images named <n>.jpg were 100 consecutive webcam frames, so
    neighbouring frames are near-duplicates. They are grouped into contiguous
    blocks (frames 0-19, 20-39, ...), and evaluation never puts frames from the
    same block in both train and test.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np

from asl import config
from asl.features import FEATURE_VERSION, N_FEATURES, landmark_features
from asl.labels import name_of

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}
_SESSION_RE = re.compile(r"^(?P<session>.+)_(?P<idx>\d+)$")


def _natural_key(path: Path):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", path.stem)]


def group_for(path: Path, block_size: int) -> str:
    m = _SESSION_RE.match(path.stem)
    if m:
        return f"session:{m.group('session')}"
    if path.stem.isdigit():
        return f"block:{int(path.stem) // block_size}"
    return f"file:{path.stem}"


def list_images(data_dir: Path) -> list[tuple[int, Path]]:
    items = []
    for class_dir in sorted((d for d in data_dir.iterdir() if d.is_dir() and d.name.isdigit()), key=lambda d: int(d.name)):
        for img in sorted((f for f in class_dir.iterdir() if f.suffix.lower() in IMAGE_EXTS), key=_natural_key):
            items.append((int(class_dir.name), img))
    return items


def build(data_dir: Path, out_path: Path, block_size: int = 20, min_confidence: float = 0.5) -> dict:
    import cv2

    from asl.landmarks import HandDetector

    items = list_images(data_dir)
    if not items:
        raise SystemExit(f"No images found under {data_dir}/<class_id>/. Collect some with `python -m asl.collect`.")

    X, y, groups, paths, hands, raw, sizes = [], [], [], [], [], [], []
    missed: Counter[int] = Counter()
    total: Counter[int] = Counter()
    with HandDetector(static_image_mode=True, min_detection_confidence=min_confidence) as detector:
        for n, (class_id, path) in enumerate(items, 1):
            total[class_id] += 1
            img = cv2.imread(str(path))
            hand = detector.detect(img) if img is not None else None
            if hand is None:
                missed[class_id] += 1
                continue
            X.append(landmark_features(hand.points, hand.handedness))
            y.append(class_id)
            groups.append(group_for(path, block_size))
            paths.append(str(path.relative_to(data_dir)))
            hands.append(hand.handedness)
            raw.append(hand.points)
            sizes.append(img.shape[1::-1])  # (width, height)
            if n % 200 == 0:
                print(f"  {n}/{len(items)} images", file=sys.stderr)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_path, X=np.asarray(X, dtype=np.float32).reshape(-1, N_FEATURES),
                        y=np.asarray(y), groups=np.asarray(groups), paths=np.asarray(paths),
                        handedness=np.asarray(hands), feature_version=FEATURE_VERSION,
                        landmarks=np.asarray(raw, dtype=np.float32).reshape(-1, 21, 3),
                        image_size=np.asarray(sizes, dtype=np.int32).reshape(-1, 2))

    print(f"\n{'class':<16}{'images':>8}{'hands':>8}")
    for cid in sorted(total):
        print(f"{name_of(cid):<16}{total[cid]:>8}{total[cid] - missed[cid]:>8}")
    detected = sum(total.values()) - sum(missed.values())
    print(f"\nDetected a hand in {detected}/{sum(total.values())} images "
          f"({detected / max(sum(total.values()), 1):.1%}); {len(set(groups))} groups.")
    print(f"Saved {out_path}")
    return {"images": sum(total.values()), "samples": detected, "classes": len(total)}


def load(path: Path = config.FEATURES_PATH) -> dict:
    d = np.load(path, allow_pickle=False)
    if int(d["feature_version"]) != FEATURE_VERSION:
        raise SystemExit(f"{path} was built with feature version {int(d['feature_version'])}; "
                         f"re-run `python -m asl.dataset`.")
    return {k: d[k] for k in d.files}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data-dir", type=Path, default=config.DATA_DIR)
    p.add_argument("--out", type=Path, default=config.FEATURES_PATH)
    p.add_argument("--block-size", type=int, default=20, help="frames per group for un-sessioned images")
    p.add_argument("--min-confidence", type=float, default=0.5,
                   help="MediaPipe detection confidence (the old 0.1 let false detections into training)")
    a = p.parse_args(argv)
    build(a.data_dir, a.out, a.block_size, a.min_confidence)


if __name__ == "__main__":
    main()
