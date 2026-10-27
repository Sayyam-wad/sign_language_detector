"""Check the environment: packages, MediaPipe API, cameras, data and model.

    python -m asl.doctor [--show]   (--show opens a preview of each working camera)
"""

from __future__ import annotations

import argparse
import importlib
import sys

from asl import config


def check(label: str, ok: bool, detail: str = "") -> bool:
    print(f"  [{'ok' if ok else '!!'}] {label}{f'  ({detail})' if detail else ''}")
    return ok


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--show", action="store_true")
    p.add_argument("--max-index", type=int, default=5)
    a = p.parse_args(argv)
    good = True

    print("Python & packages")
    good &= check(f"Python {sys.version.split()[0]}", (3, 9) <= sys.version_info[:2] <= (3, 12),
                  "MediaPipe's legacy hand API needs Python 3.9-3.12")
    for mod in ("numpy", "cv2", "sklearn", "joblib", "mediapipe", "pyttsx3"):
        try:
            m = importlib.import_module(mod)
            good &= check(mod, True, getattr(m, "__version__", ""))
        except ImportError:
            good &= check(mod, mod == "pyttsx3", "missing" + (" (optional: speech)" if mod == "pyttsx3" else ""))
    try:
        from asl.landmarks import _mediapipe_hands
        _mediapipe_hands()
        check("mediapipe hands API", True)
    except ImportError as e:
        good &= check("mediapipe hands API", False, str(e))

    print("\nCameras")
    try:
        import cv2
        found = []
        for i in range(a.max_index + 1):
            cap = cv2.VideoCapture(i)
            ok, frame = cap.read() if cap.isOpened() else (False, None)
            if ok and frame is not None:
                found.append(i)
                check(f"camera {i}", True, f"{frame.shape[1]}x{frame.shape[0]}")
                if a.show:
                    cv2.imshow(f"camera {i} - any key", frame)
                    cv2.waitKey(0)
                    cv2.destroyAllWindows()
            cap.release()
        good &= check("at least one camera", bool(found),
                      f"set ASL_CAMERA_INDEX to one of {found}" if found else "none found")
    except ImportError:
        good = False

    print("\nProject files")
    n_imgs = sum(1 for _ in config.DATA_DIR.glob("*/*.jpg")) if config.DATA_DIR.exists() else 0
    good &= check(f"model at {config.MODEL_PATH}", config.MODEL_PATH.exists(), "python -m asl.train")
    print(f"  [--] training images: {n_imgs} in {config.DATA_DIR} (only needed to retrain)")
    print("\nAll good." if good else "\nFix the items marked !! above.")
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
