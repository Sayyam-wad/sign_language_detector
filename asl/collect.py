"""Record training images from the webcam.

    python -m asl.collect C O HELLO --count 100      # specific signs (names or class ids)
    python -m asl.collect --all --count 60           # every class
    python -m asl.collect --list                     # images per class so far

Improvements over the original collector
  * Images are saved as data/<class_id>/<session>_<n>.jpg. Every run is a new
    session, and evaluation keeps sessions apart, so you can measure how well
    the model generalises to a new recording (different day, light, hand).
  * Only frames with a detected hand are saved, every `--every`-th frame, so
    the dataset isn't 100 copies of the same instant.
  * Existing images are never deleted or overwritten (the old recollect and
    cleanup scripts deleted whole class folders).
Tip: run several short sessions per sign — vary distance, angle, lighting, and
which hand you use. That is what makes the model work for other people.
"""

from __future__ import annotations

import argparse
import time
from datetime import datetime
from pathlib import Path

from asl import config
from asl.labels import CLASSES, NAME_TO_ID, name_of


def resolve(signs: list[str]) -> list[int]:
    ids = []
    for s in signs:
        key = s.upper().replace("_", " ")
        if key.isdigit() and int(key) in CLASSES:
            ids.append(int(key))
        elif key in NAME_TO_ID:
            ids.append(NAME_TO_ID[key])
        else:
            raise SystemExit(f"Unknown sign '{s}'. Valid: {', '.join(sorted(NAME_TO_ID))}")
    return ids


def counts(data_dir: Path) -> dict[int, int]:
    return {cid: len(list((data_dir / str(cid)).glob("*.jpg"))) if (data_dir / str(cid)).exists() else 0
            for cid in CLASSES}


def collect(class_ids: list[int], count: int, every: int, data_dir: Path) -> None:
    import cv2

    from asl.camera import open_camera, read_frame
    from asl.landmarks import HandDetector

    session = datetime.now().strftime("%Y%m%d-%H%M%S")
    cap = open_camera()
    detector = HandDetector(static_image_mode=False)
    window = "Collect - SPACE start | S skip | Q quit"
    try:
        for n, cid in enumerate(class_ids, 1):
            out = data_dir / str(cid)
            out.mkdir(parents=True, exist_ok=True)
            name = name_of(cid)
            # Wait for the user.
            while True:
                frame = read_frame(cap)
                if frame is None:
                    continue
                shown = frame.copy()
                cv2.putText(shown, f"[{n}/{len(class_ids)}] Sign: {name}", (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                cv2.putText(shown, "SPACE: start   S: skip   Q: quit", (10, shown.shape[0] - 15),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                cv2.imshow(window, shown)
                key = cv2.waitKey(20) & 0xFF
                if key == ord(" "):
                    break
                if key == ord("s"):
                    name = None
                    break
                if key == ord("q"):
                    return
            if name is None:
                continue
            # Short countdown so the first frames aren't the hand moving into place.
            end = time.time() + 2
            while time.time() < end:
                frame = read_frame(cap)
                if frame is not None:
                    cv2.putText(frame, f"{name} in {end - time.time():.1f}s", (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 255), 2)
                    cv2.imshow(window, frame)
                cv2.waitKey(1)
            saved, seen = 0, 0
            while saved < count:
                frame = read_frame(cap)
                if frame is None:
                    continue
                hand = detector.detect(frame)
                seen += 1
                if hand is not None and seen % every == 0:
                    cv2.imwrite(str(out / f"{session}_{saved}.jpg"), frame)  # saved without overlays
                    saved += 1
                shown = frame.copy()
                if hand is not None:
                    detector.draw(shown, hand)
                cv2.putText(shown, f"{name}: {saved}/{count}", (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                if hand is None:
                    cv2.putText(shown, "no hand detected", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.rectangle(shown, (10, shown.shape[0] - 20), (10 + int(300 * saved / count), shown.shape[0] - 10), (0, 255, 0), -1)
                cv2.imshow(window, shown)
                if (cv2.waitKey(1) & 0xFF) == 27:  # ESC ends this sign early
                    break
            print(f"{name}: saved {saved} images to {out}")
    finally:
        detector.close()
        cap.release()
        cv2.destroyAllWindows()


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("signs", nargs="*", help="sign names or class ids, e.g. C O HELLO 18")
    p.add_argument("--all", action="store_true", help="collect every class")
    p.add_argument("--count", type=int, default=60, help="images per sign in this session")
    p.add_argument("--every", type=int, default=3, help="save every N-th frame with a hand")
    p.add_argument("--data-dir", type=Path, default=config.DATA_DIR)
    p.add_argument("--list", action="store_true", help="show images per class and exit")
    a = p.parse_args(argv)
    if a.list:
        for cid, n in counts(a.data_dir).items():
            print(f"{cid:>3}  {name_of(cid):<15} {n}")
        return
    ids = list(CLASSES) if a.all else resolve(a.signs)
    if not ids:
        p.error("name at least one sign, or use --all")
    collect(ids, a.count, max(1, a.every), a.data_dir)


if __name__ == "__main__":
    main()
