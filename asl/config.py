"""Settings. Every value can be overridden with an environment variable (ASL_<NAME>)."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _env(name: str, default):
    raw = os.getenv(f"ASL_{name}")
    if raw is None:
        return default
    if isinstance(default, bool):
        return raw.lower() in ("1", "true", "yes")
    if isinstance(default, Path):
        return Path(raw)
    return type(default)(raw)


# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_DIR = _env("DATA_DIR", ROOT / "data")               # data/<class_id>/*.jpg
ARTIFACTS_DIR = _env("ARTIFACTS_DIR", ROOT / "artifacts")
FEATURES_PATH = ARTIFACTS_DIR / "features.npz"
MODEL_PATH = _env("MODEL_PATH", ARTIFACTS_DIR / "model.joblib")
REPORT_DIR = ARTIFACTS_DIR / "report"

# ── Camera ────────────────────────────────────────────────────────────────────
CAMERA_INDEX = _env("CAMERA_INDEX", 0)
FRAME_WIDTH = _env("FRAME_WIDTH", 640)
FRAME_HEIGHT = _env("FRAME_HEIGHT", 480)
MIRROR = _env("MIRROR", True)

# ── Hand detection (MediaPipe) ────────────────────────────────────────────────
DETECTION_CONFIDENCE = _env("DETECTION_CONFIDENCE", 0.5)
TRACKING_CONFIDENCE = _env("TRACKING_CONFIDENCE", 0.5)

# ── Recognition ───────────────────────────────────────────────────────────────
SMOOTHING = _env("SMOOTHING", 0.6)             # EMA weight on previous frames (0 = no smoothing)
MIN_CONFIDENCE = _env("MIN_CONFIDENCE", 0.55)   # below this, show "?" instead of a guess
HOLD_SECONDS = _env("HOLD_SECONDS", 1.2)        # hold a sign this long to add it automatically
SPACE_SECONDS = _env("SPACE_SECONDS", 2.0)      # no hand for this long adds a space
AUTO_COMMIT = _env("AUTO_COMMIT", True)

# ── Text to speech ────────────────────────────────────────────────────────────
SPEECH_RATE = _env("SPEECH_RATE", 140)

# ── Training ──────────────────────────────────────────────────────────────────
RANDOM_STATE = 42
